#!/usr/bin/env python3
"""Local dashboard server for Auto Company (Windows + WSL + macOS runtime)."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import platform
import re
import shlex
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import sentry_client

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = Path(__file__).resolve().parent

WINDOWS_STATUS_SCRIPT = REPO_ROOT / "scripts" / "windows" / "status-win.ps1"
WINDOWS_START_SCRIPT = REPO_ROOT / "scripts" / "windows" / "start-win.ps1"
WINDOWS_STOP_SCRIPT = REPO_ROOT / "scripts" / "windows" / "stop-win.ps1"

LINUX_STATUS_SCRIPT = REPO_ROOT / "scripts" / "linux" / "status-linux.sh"
LINUX_NOOP_SCRIPT = REPO_ROOT / "scripts" / "linux" / "noop-action.sh"

MACOS_STATUS_SCRIPT = REPO_ROOT / "scripts" / "macos" / "status-mac.sh"
MACOS_START_SCRIPT = REPO_ROOT / "scripts" / "macos" / "install-daemon.sh"
MACOS_STOP_SCRIPT = REPO_ROOT / "scripts" / "core" / "stop-loop.sh"

LOG_FILE = REPO_ROOT / "logs" / "auto-loop.log"
STATE_FILE = REPO_ROOT / ".auto-loop-state"
CONSENSUS_FILE = REPO_ROOT / "memories" / "consensus.md"
DIRECTIVE_FILE = REPO_ROOT / "memories" / "human-directive.md"
CANDIDATE_REGISTRY_FILE = REPO_ROOT / "memories" / "candidate-registry.md"
ANALYSIS_FILE = REPO_ROOT / "memories" / "analysis-directive.md"
# On-demand analyst trigger (cockpit "Run analyst now"). The cockpit runs INSIDE the
# app container and cannot start host containers (the analyst is a host-cron one-shot
# container), so the button writes a request FILE into the shared logs volume — the
# LOOP_HOLD idiom — and the host-side watcher consumes it under the same flock the
# 04:30 schedule uses (autocompany-deploy/scripts/opportunity-analyst-trigger.sh via
# /etc/cron.d/opportunity-analyst, every 5 minutes). The watcher writes the RUNNING /
# LAST_TRIGGER markers back into the volume, which is how state is visible here.
ANALYST_RUN_REQUEST_FILE = REPO_ROOT / "logs" / "ANALYST_RUN_REQUEST"
ANALYST_RUNNING_FILE = REPO_ROOT / "logs" / "ANALYST_RUNNING"
ANALYST_LAST_TRIGGER_FILE = REPO_ROOT / "logs" / "ANALYST_LAST_TRIGGER"
# Operator-request ledger (written by the company + scripts/core/operator_request_notify.py)
# and the cockpit's answer channel. The answer channel is deliberately NOT
# human-directive.md: that file is a single slot holding one PENDING work instruction, so
# answering a request through it meant overwriting whatever the loop was mid-way through
# executing. See APP-264.
OPERATOR_REQUESTS_FILE = REPO_ROOT / "memories" / "operator-requests.md"
OPERATOR_DECISIONS_FILE = REPO_ROOT / "memories" / "operator-decisions.md"
OPERATOR_DECISIONS_AUDIT = REPO_ROOT / "memories" / "operator-decisions-audit.log"
# Operator-editable runtime overrides, sourced by docker-entrypoint.sh on start.
RUNTIME_ENV_FILE = REPO_ROOT / "logs" / "runtime.env"

# Whitelist of NON-SECRET knobs editable from the cockpit Settings panel. Anything
# not listed here is rejected, so the panel can never write secrets to runtime.env.
SETTINGS_SPEC: list[dict[str, str]] = [
    {"key": "DISCOVERY_ENABLED", "type": "bool",
     "label": "Opportunity Discovery — scan brand-new candidate axes (off = tender-track + 176-R focus only; auto-loop.sh default is OFF when unset)"},
    {"key": "ROUTER_ALTERNATE", "type": "bool",
     "label": "Router alternation (Claude↔Codex when both have headroom)"},
    {"key": "CLAUDE_5H_BUDGET_USD", "type": "number",
     "label": "Claude 5h gate (notional USD per plan window; blank = no gate) — APP-263 hard "
              "gate; blocked Claude is skipped by Alternate until its window resets"},
    {"key": "CODEX_5H_BUDGET_USD", "type": "number",
     "label": "Codex 5h gate (notional USD per plan window; blank = no gate) — APP-263 hard "
              "gate, analyst sessions excluded when verified"},
    {"key": "TOTAL_DAILY_BUDGET_USD", "type": "number",
     "label": "Daily TOTAL gate (notional USD per UTC calendar day; blank = no gate) — "
              "reaching it pauses BOTH engines until the next UTC midnight"},
    {"key": "TOTAL_WEEKLY_BUDGET_USD", "type": "number",
     "label": "Weekly TOTAL gate (notional USD, rolling 7×24h; blank = no gate) — reaching "
              "it pauses BOTH engines until enough spend ages out"},
    {"key": "CODEX_WINDOW_LIMIT", "type": "number",
     "label": "Codex cycles per window (blank = unmetered)"},
    {"key": "MODEL", "type": "text",
     "label": "Claude model (blank = engine default, e.g. claude-haiku-4-5-20251001)"},
    {"key": "CLAUDE_EFFORT", "type": "text",
     "label": "Claude reasoning effort (low / medium / high, blank = default)"},
    {"key": "ENGINE", "type": "text",
     "label": "Primary engine (claude / codex, blank = claude)"},
    {"key": "CODEX_EFFORT", "type": "text",
     "label": "Codex reasoning effort (low / medium / high, blank = codex default)"},
    {"key": "ROUTER_TIER_LADDER", "type": "bool",
     "label": "Tier ladder — round-robin model/effort within the MIN..MAX range (saves tokens)"},
    {"key": "CLAUDE_TIER_LADDER", "type": "text",
     "label": "Claude model ladder, cheapest first (comma-sep), e.g. claude-haiku-4-5-20251001,claude-sonnet-5"},
    {"key": "CODEX_TIER_LADDER", "type": "text",
     "label": "Codex effort ladder, cheapest first (comma-sep), e.g. low,medium"},
    {"key": "ESCALATE_NEXT_CYCLE", "type": "text",
     "label": "Escalate ONE cycle (e.g. claude-opus-5:high) — overrides the ladder for a single "
              "cycle, only while a directive is PENDING, then clears itself. Takes effect on the "
              "next cycle, no restart needed. Blank = normal ladder."},
    {"key": "CYCLE_TIMEOUT_SECONDS", "type": "number",
     "label": "Per-cycle wall clock (seconds, default 900) — the main cost lever: cache-read cost "
              "is superlinear in cycle length"},
    {"key": "ESCALATED_CYCLE_TIMEOUT_SECONDS", "type": "number",
     "label": "Wall clock for an escalated cycle (seconds, default 1800)"},
    {"key": "LOOP_INTERVAL", "type": "number",
     "label": "Loop interval between cycles (seconds)"},
    {"key": "BUDGET_PAUSE_SECONDS", "type": "number",
     "label": "Pause when budget hit and Codex unavailable (seconds)"},
]
SETTINGS_KEYS = {s["key"] for s in SETTINGS_SPEC}

WINDOWS_HOST = "windows"
MACOS_HOST = "macos"
LINUX_HOST = "linux"


def ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def detect_host_kind(system_name: str | None = None) -> str:
    name = system_name or platform.system()
    if name == "Windows":
        return WINDOWS_HOST
    if name == "Darwin":
        return MACOS_HOST
    if name == "Linux":
        return LINUX_HOST
    raise RuntimeError(
        "Dashboard only supports Windows (WSL), macOS, and Linux/container hosts."
    )


def run_powershell_script(
    script_path: Path, args: list[str] | None = None, timeout: int = 90
) -> dict[str, Any]:
    invocation = f"& {ps_quote(str(script_path))}"
    if args:
        invocation += " " + " ".join(ps_quote(arg) for arg in args)

    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        (
            "$ErrorActionPreference='Stop'; "
            "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
            "$OutputEncoding=[System.Text.Encoding]::UTF8; "
            f"{invocation} *>&1 | Out-String"
        ),
    ]

    start = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    elapsed_ms = int((time.time() - start) * 1000)

    output = (proc.stdout or "").strip()
    error = (proc.stderr or "").strip()
    combined = output
    if error:
        combined = f"{output}\n{error}".strip()

    return {
        "ok": proc.returncode == 0,
        "exitCode": proc.returncode,
        "elapsedMs": elapsed_ms,
        "output": combined,
    }


def run_shell_script(
    script_path: Path, args: list[str] | None = None, timeout: int = 90
) -> dict[str, Any]:
    cmd = ["/bin/bash", str(script_path)]
    if args:
        cmd.extend(args)

    start = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    elapsed_ms = int((time.time() - start) * 1000)

    output = (proc.stdout or "").strip()
    error = (proc.stderr or "").strip()
    combined = output
    if error:
        combined = f"{output}\n{error}".strip()

    return {
        "ok": proc.returncode == 0,
        "exitCode": proc.returncode,
        "elapsedMs": elapsed_ms,
        "output": combined,
    }


def get_host_profile(system_name: str | None = None) -> dict[str, Any]:
    host = detect_host_kind(system_name)
    if host == WINDOWS_HOST:
        return {
            "host": host,
            "runner": run_powershell_script,
            "parser": parse_windows_status_output,
            "status_script": WINDOWS_STATUS_SCRIPT,
            "start_script": WINDOWS_START_SCRIPT,
            "start_args": None,
            "stop_script": WINDOWS_STOP_SCRIPT,
            "stop_args": None,
        }
    if host == LINUX_HOST:
        return {
            "host": host,
            "runner": run_shell_script,
            "parser": parse_macos_status_output,
            "status_script": LINUX_STATUS_SCRIPT,
            "start_script": LINUX_NOOP_SCRIPT,
            "start_args": None,
            "stop_script": LINUX_NOOP_SCRIPT,
            "stop_args": None,
        }
    return {
        "host": host,
        "runner": run_shell_script,
        "parser": parse_macos_status_output,
        "status_script": MACOS_STATUS_SCRIPT,
        "start_script": MACOS_START_SCRIPT,
        "start_args": None,
        "stop_script": MACOS_STOP_SCRIPT,
        "stop_args": ["--pause-daemon"],
    }


def read_text_file(path: Path, fallback: str = "") -> str:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return fallback
    except Exception as exc:  # pragma: no cover - defensive
        return f"(read error: {exc})"

    for enc in ("utf-8", "utf-8-sig", "gb18030", "cp936"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue

    return raw.decode("utf-8", errors="replace")


def read_text_file_tail(path: Path, max_bytes: int, fallback: str = "") -> str:
    """Last `max_bytes` of a file, decoded like read_text_file.

    auto-loop.log is PERSISTENT across redeploys and only grows (391 KB / 4700+
    lines by 2026-07-28), and read_engine_runtime() re-parsed all of it on every
    status poll. Everything it extracts uses the LAST match, so the tail is
    sufficient — the caller falls back to the full file only if the once-per-boot
    banner it needs is not inside the window.
    """
    try:
        size = path.stat().st_size
        with path.open("rb") as fh:
            if size > max_bytes:
                fh.seek(size - max_bytes)
            raw = fh.read()
    except FileNotFoundError:
        return fallback
    except Exception as exc:  # pragma: no cover - defensive
        return f"(read error: {exc})"

    # A mid-character seek can split a multi-byte sequence; drop the partial
    # first line rather than emitting replacement junk into the parsed output.
    if size > max_bytes:
        nl = raw.find(b"\n")
        if nl != -1:
            raw = raw[nl + 1 :]

    for enc in ("utf-8", "utf-8-sig", "gb18030", "cp936"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


# Tail window for read_engine_runtime(). Comfortably covers many boots' worth of
# banner + [ROUTER]/[TIER] lines while bounding work per status poll.
ENGINE_RUNTIME_TAIL_BYTES = 262144

DIRECTIVE_MAX_CHARS = 20000
# The writer runs with AC_APP_DIR = DIRECTIVE_APP_DIR (tests point it at a temp app).
DIRECTIVE_APP_DIR = REPO_ROOT
DIRECTIVE_WRITER = REPO_ROOT / "scripts" / "core" / "directive_writer.py"
# Mirrors the writer's DIRECTIVE_BODY_WARN_BYTES default; the panel only colours the summary.
DIRECTIVE_WARN_BYTES = 50000
_directive_writer_mod: Any = None


def _directive_writer_module() -> Any:
    """Load scripts/core/directive_writer.py once, for its pure section helpers.

    The panel must split the body exactly as the writer's append/archive do, so it
    reuses split_body/live_body instead of a second parser that could drift.
    """
    global _directive_writer_mod
    if _directive_writer_mod is None:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("ac_directive_writer", DIRECTIVE_WRITER)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {DIRECTIVE_WRITER}")
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _directive_writer_mod = mod
    return _directive_writer_mod


def directive_sections(raw: str) -> tuple[list[dict[str, Any]], int]:
    """([{heading, bytes, kind}], body_bytes) for the panel summary; ([], 0) on any failure.

    kind: main (ANA DİREKTİF + preamble, never split), archive ('## ARŞİV…' summaries),
    active (everything else). Byte counts partition the body, so they sum to body_bytes.
    """
    try:
        w = _directive_writer_module()
        body = w.live_body(raw)
        first, secs = w.split_body(body)
    except Exception:  # noqa: BLE001 — the summary is optional; the panel must still render
        return [], 0
    out: list[dict[str, Any]] = [
        {"heading": "ANA DİREKTİF + önsöz", "bytes": len(first.encode("utf-8")), "kind": "main"}
    ]
    for heading, text in secs:
        title = heading[3:].strip()
        kind = "archive" if title.startswith(("ARŞİV", "ARCHIVE")) else "active"
        out.append({"heading": title, "bytes": len(text.encode("utf-8")), "kind": kind})
    return out, len(body.encode("utf-8"))


def as_directive_section(text: str, stamp: str) -> str:
    """Turn panel text into exactly ONE '## ' section for `directive_writer.py append`.

    A first line that is already '## …' is kept as the heading; otherwise a
    'OPERATÖR DİREKTİFİ — cockpit <stamp>' heading is added. Every later '# '/'## '
    line is demoted to '### ' — templates carry their own '## Decision' etc., and
    left alone they would split one submission into several sections, which the
    archive step then cannot drop as a unit.
    """
    lines = text.strip().splitlines()
    out: list[str] = []
    if lines and lines[0].startswith("## "):
        out.append(lines[0].rstrip())
        rest = lines[1:]
    else:
        out += [f"## OPERATÖR DİREKTİFİ — cockpit {stamp}", ""]
        rest = lines
    for line in rest:
        if line.startswith("# ") or line.startswith("## "):
            line = "### " + line.lstrip("#").lstrip()
        out.append(line)
    return "\n".join(out).rstrip("\n") + "\n"


def read_directive() -> dict[str, Any]:
    """Parse memories/human-directive.md into a structured payload.

    Returns {present, status, updated, directive}. status is one of
    PENDING / DONE / NONE. The autonomous loop flips PENDING -> DONE after it
    executes the directive, so the dashboard can show whether it was picked up.
    """
    raw = read_text_file(DIRECTIVE_FILE, "")
    if not raw.strip():
        return {"present": False, "status": "NONE", "updated": "", "directive": ""}

    def _section(name: str, to_end: bool = False) -> str:
        # Directive is always the final section, and its body is free-form
        # markdown that may itself contain "## " headings — so for it we must
        # capture to end-of-file (to_end) instead of stopping at the next "## ",
        # which would silently truncate the displayed directive.
        terminator = r"\Z" if to_end else r"(?=^##\s+|\Z)"
        match = re.search(
            rf"^##\s+{name}\s*$\n(.*?){terminator}",
            raw,
            re.MULTILINE | re.DOTALL,
        )
        return match.group(1).strip() if match else ""

    status = (_section("Status") or "PENDING").splitlines()[0].strip().upper()
    if status not in {"PENDING", "DONE"}:
        status = "PENDING"
    sections, body_bytes = directive_sections(raw)
    return {
        "present": True,
        "status": status,
        "updated": _section("Updated"),
        "directive": _section("Directive", to_end=True),
        "sections": sections,
        "bodyBytes": body_bytes,
        "warnBytes": DIRECTIVE_WARN_BYTES,
    }


class DirectiveRefused(Exception):
    """A gate refused the write — most often: the live directive is still PENDING."""


def write_directive(text: str, allow_pending: bool = False) -> dict[str, Any]:
    """APPEND the panel text to the live directive as one new '## ' section (Status -> PENDING).

    Until 2026-10-13 this called the writer's `write`, which REPLACES the whole body:
    two lines typed here while the directive was DONE would have wiped the ~39 KB body,
    ANA DİREKTİF included. The panel now only appends; whole-body replace stays on the
    liaison channel (apply-directive.sh AC_MODE=replace) where it is a deliberate act.
    """
    clean = text.strip()
    if not clean:
        raise ValueError("directive text is empty")
    if len(clean) > DIRECTIVE_MAX_CHARS:
        raise ValueError(f"directive too long (max {DIRECTIVE_MAX_CHARS} chars)")

    section = as_directive_section(clean, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"))
    # Route through the single deterministic writer rather than writing here. The
    # writer does lock -> in-flight gate -> size brake -> backup -> atomic rename ->
    # read-back -> audit -> notify, and refuses to add to a PENDING directive unless
    # the caller says so explicitly. `allow_pending` is what the panel's confirm maps
    # to; appending never deletes text, so the confirm only guards the work queue.
    import subprocess
    import tempfile as _tf
    with _tf.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(section)
        body_path = fh.name
    try:
        cmd = [sys.executable, str(DIRECTIVE_WRITER),
               "--actor", "cockpit-director-panel", "append", "--section-file", body_path]
        if allow_pending:
            cmd.append("--allow-pending")
        env = {**os.environ, "AC_APP_DIR": str(DIRECTIVE_APP_DIR)}
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
    finally:
        Path(body_path).unlink(missing_ok=True)
    if proc.returncode == 2:
        raise DirectiveRefused(proc.stderr.strip() or "refused by the directive writer")
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "directive writer failed")
    return read_directive()


# --- Operator requests: read the ledger, write decisions ---------------------------
#
# The request record is ALREADY option-shaped — `Required input` is the question,
# `Proposed authorization` is a pre-filled default the company itself labels "copy, edit,
# or replace", and REFUSE is valid for every type. The panel renders that; it does not
# invent a protocol.

OPREQ_BLOCK_RE = re.compile(r"^## (OPREQ-[A-Za-z0-9_-]+)\s*$", re.MULTILINE)
# Label is everything up to the FIRST colon, deliberately looser than the ledger
# writer's own `^- ([A-Za-z][A-Za-z /]*):` — because the field this panel most needs is
# written as `- Proposed authorization (copy, edit, or replace — this is the company's
# request, not a decision): System: ...`, and a letters-and-spaces label class cannot
# match past the parenthesis. That field is not in REQUIRED_FIELDS, so the writer's
# parser silently skipping it was never noticed. The parenthetical is stripped to
# normalise the key.
OPREQ_FIELD_RE = re.compile(r"^- ([A-Za-z][^:]*?):\s?(.*)$")
AUTH_LABELS = ("System", "Action", "Target", "Limit")
# The four labels arrive concatenated on one line inside `Proposed authorization`;
# slice between label positions rather than matching greedily past the next one.
AUTH_LABEL_RE = re.compile(rf"\b({'|'.join(AUTH_LABELS)}):\s*")
# Types whose answer is an authorization block. Everything else the panel shows
# read-only with a Refuse option, because inventing a response shape for a type the
# verifier checks differently would close a request with an answer it never got.
AUTHORIZATION_TYPES = {"expenditure-approval", "external-action-authorization"}


def parse_proposed_authorization(text: str) -> dict[str, str]:
    """Split a `Proposed authorization` value into System/Action/Target/Limit."""
    marks = [(m.group(1), m.start(), m.end()) for m in AUTH_LABEL_RE.finditer(text)]
    out: dict[str, str] = {}
    for i, (label, _start, end) in enumerate(marks):
        stop = marks[i + 1][1] if i + 1 < len(marks) else len(text)
        value = text[end:stop].strip()
        if value:
            out[label] = value
    return out


def read_operator_requests() -> dict[str, Any]:
    """Every OPEN request in the ledger, shaped for the cockpit panel."""
    raw = read_text_file(OPERATOR_REQUESTS_FILE, "")
    if not raw.strip():
        return {"present": False, "open": []}

    marks = [(m.group(1), m.start(), m.end()) for m in OPREQ_BLOCK_RE.finditer(raw)]
    items: list[dict[str, Any]] = []
    for i, (req_id, _start, end) in enumerate(marks):
        stop = marks[i + 1][1] if i + 1 < len(marks) else len(raw)
        fields: dict[str, str] = {}
        for line in raw[end:stop].splitlines():
            fm = OPREQ_FIELD_RE.match(line)
            if fm:
                label = fm.group(1).split(" (", 1)[0].strip()
                fields[label] = fm.group(2).strip()
        if fields.get("Status", "").strip().upper() != "OPEN":
            continue
        req_type = fields.get("Type", "").strip()
        proposed = fields.get("Proposed authorization", "")
        items.append(
            {
                "id": req_id,
                "type": req_type,
                "blockedScope": fields.get("Blocked scope", ""),
                "requiredInput": fields.get("Required input", ""),
                "acceptableResponse": fields.get("Acceptable response format", ""),
                "sourceBrief": fields.get("Source brief", ""),
                "created": fields.get("Created", ""),
                # Only offer an authorization form for the types whose verifier
                # actually reads one.
                "authorizable": req_type in AUTHORIZATION_TYPES,
                "proposed": parse_proposed_authorization(proposed) if proposed else {},
            }
        )
    return {"present": True, "open": items}


def _decisions_audit(msg: str) -> None:
    stamp = datetime.now(timezone.utc).isoformat()
    try:
        OPERATOR_DECISIONS_AUDIT.parent.mkdir(parents=True, exist_ok=True)
        with OPERATOR_DECISIONS_AUDIT.open("a", encoding="utf-8") as handle:
            handle.write(f"[{stamp}] {msg}\n")
    except OSError:
        pass  # auditing must never block the decision itself


def write_operator_decision(
    req_id: str, decision: str, fields: dict[str, str], reason: str = ""
) -> dict[str, Any]:
    """Append one operator answer in exactly the shape the verifier already reads.

    Layout is load-bearing, not cosmetic. `_directive_window_after()` in
    operator_request_notify.py starts at `Authorization for <id>:` and then cuts the
    window at the FIRST `OPREQ-` token after it, capped at 1000 chars — so the four
    fields must come immediately after the anchor, and every other mention of the id
    must sit before it. Get that order wrong and the window is empty, which reads as a
    missing authorization rather than a malformed one.
    """
    req_id = (req_id or "").strip()
    if not OPREQ_BLOCK_RE.match(f"## {req_id}"):
        raise ValueError("unknown or malformed request id")

    known = {item["id"]: item for item in read_operator_requests()["open"]}
    if req_id not in known:
        raise ValueError(f"{req_id} is not an OPEN request")

    stamp = datetime.now(timezone.utc).isoformat()
    if decision == "refuse":
        # The REFUSE line must stay ONE physical line — operator_request_notify.py matches
        # it with a line-anchored regex. But collapsing the whole reason into that line
        # destroyed a long refusal's structure (observed 2026-08-06: a numbered, paragraphed
        # rationale arrived in the ledger as a single 2,000-character run-on). So: a short
        # machine-readable head on the REFUSE line, and the operator's text verbatim below
        # it, where both a human and a later cycle can actually read it.
        flat = " ".join((reason or "").split()).strip()
        head = re.split(r"(?<=[.!?])\s", flat, maxsplit=1)[0][:200] if flat else ""
        verbatim = (reason or "").strip()
        block = (
            f"\n## {req_id} — refused {stamp}\n\n"
            f"Resolves: {req_id}\n"
            f"Decided via: cockpit operator-decision panel\n"
            f"REFUSE {req_id} — {head or 'refused by the operator, no reason given'}\n"
        )
        if verbatim and verbatim != head:
            block += f"\nFull reasoning as written by the operator:\n\n{verbatim}\n"
    elif decision == "authorize":
        if not known[req_id]["authorizable"]:
            raise ValueError(
                f"{req_id} is type '{known[req_id]['type']}', which is not answered "
                "with an authorization block — refuse it here or answer it in a directive"
            )
        clean = {}
        for label in AUTH_LABELS:
            value = " ".join(str(fields.get(label, "")).split()).strip()
            # A blank field would authorize an unbounded action; the ledger already
            # promises the operator that a missing line leaves the request OPEN.
            if not value:
                raise ValueError(f"'{label}' is required and must not be empty")
            if "\n" in value:
                raise ValueError(f"'{label}' must be a single line")
            clean[label] = value
        body = "".join(f"{label}: {clean[label]}\n" for label in AUTH_LABELS)
        block = (
            f"\n## {req_id} — authorized {stamp}\n\n"
            f"Resolves: {req_id}\n"
            f"Decided via: cockpit operator-decision panel\n"
            f"Authorization for {req_id}:\n"
            f"{body}"
        )
    else:
        raise ValueError("decision must be 'authorize' or 'refuse'")

    header = (
        "# Operator Decisions\n\n"
        "<!-- Answers to memories/operator-requests.md, submitted from the cockpit\n"
        "     panel. Append-only. Read by scripts/core/operator_request_notify.py as a\n"
        "     second answer source alongside human-directive.md; unlike a directive,\n"
        "     an entry here needs no DONE status because it is a decision, not work.\n"
        "     Do not hand-edit: the exact field shape is what the verifier checks. -->\n"
    )
    existing = read_text_file(OPERATOR_DECISIONS_FILE, "")
    if not existing.strip():
        existing = header
    OPERATOR_DECISIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    OPERATOR_DECISIONS_FILE.write_text(existing.rstrip("\n") + "\n" + block, encoding="utf-8")

    readback = read_text_file(OPERATOR_DECISIONS_FILE, "")
    if block.strip() not in readback:
        _decisions_audit(f"WRITE-FAILED {req_id}: read-back mismatch")
        raise ValueError("decision write failed read-back verification")

    _decisions_audit(f"{decision.upper()} {req_id} via cockpit panel")
    return {"id": req_id, "decision": decision, "recorded": stamp}


def _parse_env_file(raw: str) -> dict[str, str]:
    """Parse simple KEY=value lines (ignores blanks/comments)."""
    out: dict[str, str] = {}
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k:
            out[k] = v
    return out


def read_ideas() -> dict[str, Any]:
    """Read the live candidate registry (memories/candidate-registry.md) for the Ideas panel.

    The loop stopped maintaining a single docs/research/opportunity-scan.md after the
    discovery-directive rewrite (Cycle 106): per-cycle scans go to cycleNNN-*.md and the
    cumulative, framework-ranked record now lives in the lean candidate-registry.md.
    """
    raw = read_text_file(CANDIDATE_REGISTRY_FILE, "")
    updated = ""
    try:
        if CANDIDATE_REGISTRY_FILE.exists():
            import datetime

            updated = datetime.datetime.fromtimestamp(
                CANDIDATE_REGISTRY_FILE.stat().st_mtime, tz=datetime.timezone.utc
            ).isoformat()
    except OSError:
        pass
    return {"present": bool(raw.strip()), "updated": updated, "markdown": raw}


def read_tool_usage() -> dict[str, Any]:
    """Aggregate logs/tool-usage-history.ndjson (written by scripts/ops/tool-usage-audit.py
    at the loop's return moment) into per-UTC-day totals for the text-only Tool Analytics
    panel. Read-only; the ledger is tiny (~100 bytes/cycle), so a full read is fine."""
    ledger = REPO_ROOT / "logs" / "tool-usage-history.ndjson"
    days: dict[str, dict[str, int]] = {}
    updated = ""
    keys = ("calls", "ctx7", "airtable_r", "airtable_w", "linear", "browser", "browser_mcp", "graft")
    try:
        with open(ledger, encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                day = str(row.get("ts", ""))[:10]
                if not day:
                    continue
                agg = days.setdefault(day, {k: 0 for k in keys} | {"cycles": 0})
                agg["cycles"] += 1
                for k in keys:
                    agg[k] += int(row.get(k) or 0)
                # Rows written before browser_mcp existed (pre-2026-08-04) have no such key.
                # Back then every browser call WAS a raw MCP micro-step (the harness did not
                # exist), so treat the old `browser` total as MCP. This slightly overstates
                # historical MCP wherever site-contact-evidence.py ran — the conservative
                # direction: it makes the harness look worse, never better.
                if "browser_mcp" not in row:
                    agg["browser_mcp"] += int(row.get("browser") or 0)
        import datetime as _dt

        updated = _dt.datetime.fromtimestamp(
            ledger.stat().st_mtime, tz=_dt.timezone.utc
        ).isoformat()
    except OSError:
        pass
    ordered = [{"date": d, **v} for d, v in sorted(days.items(), reverse=True)[:10]]
    return {"present": bool(ordered), "updated": updated, "days": ordered}


def read_analysis() -> dict[str, Any]:
    """Read the Opportunity Analyst output (memories/analysis-directive.md) for the Analyst panel."""
    raw = read_text_file(ANALYSIS_FILE, "")
    updated = ""
    try:
        if ANALYSIS_FILE.exists():
            import datetime

            updated = datetime.datetime.fromtimestamp(
                ANALYSIS_FILE.stat().st_mtime, tz=datetime.timezone.utc
            ).isoformat()
    except OSError:
        pass
    return {
        "present": bool(raw.strip()),
        "updated": updated,
        "markdown": raw,
        "trigger": analyst_trigger_state(),
    }


def analyst_trigger_state() -> dict[str, Any]:
    """Lifecycle of the on-demand analyst trigger, from the volume markers."""
    return {
        "pending": ANALYST_RUN_REQUEST_FILE.exists(),
        "running": ANALYST_RUNNING_FILE.exists(),
        "running_info": read_text_file(ANALYST_RUNNING_FILE, "").strip(),
        "last": read_text_file(ANALYST_LAST_TRIGGER_FILE, "").strip(),
    }


def analyst_run_now() -> dict[str, Any]:
    """Queue an on-demand Opportunity Analyst run (host watcher fires within 5 min).

    Guards mirror the wake button's philosophy — the server refuses rather than
    guesses: an already-pending request or an in-flight run is never doubled. The
    real anti-overlap guard is the host-side flock; these checks just keep the
    button honest and the state legible.
    """
    state = analyst_trigger_state()
    if state["pending"]:
        return {"ok": False, "reason": "pending",
                "error": "A run request is already queued — the host watcher fires within 5 minutes."}
    if state["running"]:
        return {"ok": False, "reason": "running",
                "error": f"An analyst run is already in flight ({state['running_info'] or 'no info'})."}
    import datetime

    stamp = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        ANALYST_RUN_REQUEST_FILE.write_text(
            f"requested_at={stamp} by=cockpit\n", encoding="utf-8"
        )
    except OSError as exc:  # noqa: BLE001
        return {"ok": False, "error": f"Could not write the request file: {exc}"}
    return {"ok": True,
            "message": "Queued — the host watcher starts the run within 5 minutes. "
                       "A full run takes ~15 minutes and costs roughly $23 (calibrated)."}


DIRECTIVE_TEMPLATES_DIR = REPO_ROOT / "dashboard" / "directive-templates"
# Copy-to-clipboard directive templates shown as buttons in the Director panel.
# Order + labels here; body text lives in dashboard/directive-templates/*.md.
DIRECTIVE_TEMPLATES = [
    # 2026-08-24 Wowcar re-charter: the five discovery/tender-era templates moved to
    # directive-templates/_archive/ — restore by moving one back and re-listing it here.
    {"id": "wowcar-gate-advance", "label": "Gate işi", "file": "06-wowcar-gate-advance.md",
     "hint": "Mevcut gate'in kanıt işini ilerlet: ledger/mutabakat/SOP + OPREQ + haftalık "
             "rapor. §15 sponsor-kapılı eylemler ve gate-pass iddiası yasak."},
    {"id": "wowcar-hold-and-document", "label": "Watch mode", "file": "07-wowcar-hold-and-document.md",
     "hint": "Yeni gate işi yok: yalnız DELTA'nın adlandırdığı değişiklik, OPREQ çözümleri "
             "ve vadesi gelen haftalık rapor. Boş cycle doğru çıktıdır."},
]


def read_directive_templates() -> dict[str, Any]:
    """Return the Director-panel copy templates (label + hint + full body text)."""
    out = []
    for t in DIRECTIVE_TEMPLATES:
        text = read_text_file(DIRECTIVE_TEMPLATES_DIR / t["file"], "")
        if text.strip():
            out.append({"id": t["id"], "label": t["label"], "hint": t["hint"], "text": text})
    return {"templates": out}


def read_settings() -> dict[str, Any]:
    """Return the Settings-panel spec + current values from logs/runtime.env.

    Only whitelisted keys are surfaced. A missing/blank value means the knob is
    unset (the container falls back to its Coolify env / Dockerfile default).
    """
    current = _parse_env_file(read_text_file(RUNTIME_ENV_FILE, ""))
    values = {s["key"]: current.get(s["key"], "") for s in SETTINGS_SPEC}

    # A blank `values` entry used to be reported as "unset", which conflated two
    # very different states: nothing is configuring this knob, versus something
    # outside this file is and the panel cannot see it. MODEL and CLAUDE_EFFORT
    # are the live example — absent from runtime.env, set in Coolify, shown empty.
    # `effective` is what the loop actually inherits (the entrypoint exports
    # runtime.env over the container env, so this process's environ already
    # reflects the winner); `source` says which layer supplied it.
    #
    # "container" is deliberately not called "coolify": from inside the container
    # the Coolify env and the image's own `ENV` block are indistinguishable, and
    # both are real sources. LOOP_INTERVAL proved it — deleted from Coolify on
    # 2026-07-28, still shadowed on the next boot, because the Dockerfile carries
    # LOOP_INTERVAL=30. Naming the layer we cannot actually identify would just be
    # a more confident version of the same mistake.
    effective: dict[str, str] = {}
    source: dict[str, str] = {}
    for spec in SETTINGS_SPEC:
        key = spec["key"]
        if current.get(key, ""):
            effective[key], source[key] = current[key], "runtime.env"
        elif os.environ.get(key, ""):
            effective[key], source[key] = os.environ[key], "container"
        else:
            effective[key], source[key] = "", "default"

    return {
        "present": RUNTIME_ENV_FILE.exists(),
        "path": str(RUNTIME_ENV_FILE),
        "spec": SETTINGS_SPEC,
        "values": values,
        "effective": effective,
        "source": source,
        "needsRestart": True,
    }


def write_settings(incoming: dict[str, Any]) -> dict[str, Any]:
    """Write whitelisted KEY=value knobs to logs/runtime.env.

    Rejects any non-whitelisted key (so secrets can never be written here). Keys
    with a blank value are omitted from the file (revert to the default).
    """
    bad = [k for k in incoming if k not in SETTINGS_KEYS]
    if bad:
        raise ValueError(f"unknown setting(s): {', '.join(sorted(bad))}")

    # Preserve any non-whitelisted keys already in the file (e.g. an operator-set
    # COOLIFY_DEPLOY_TOKEN used by the Redeploy button) — the panel only manages the
    # whitelist, it must not wipe other overrides.
    existing_all = _parse_env_file(read_text_file(RUNTIME_ENV_FILE, ""))
    preserved = {k: v for k, v in existing_all.items() if k not in SETTINGS_KEYS}

    lines = [
        "# Auto-Company runtime overrides — sourced by docker-entrypoint.sh on start.",
        "# Managed by the cockpit Settings panel. Non-secret config only.",
        f"# Updated {datetime.now(timezone.utc).isoformat()}",
        "",
    ]
    for k, v in preserved.items():
        lines.append(f"{k}={v}")
    if preserved:
        lines.append("")
    for spec in SETTINGS_SPEC:
        key = spec["key"]
        if key not in incoming:
            # preserve an existing value not included in this write
            existing = _parse_env_file(read_text_file(RUNTIME_ENV_FILE, "")).get(key, "")
            val = existing
        else:
            val = str(incoming[key]).strip()
        if spec["type"] == "bool":
            val = "1" if val in {"1", "true", "True", "on", "yes"} else ("0" if val != "" else "")
        if val == "":
            continue  # unset -> omit -> falls back to container default
        if spec["type"] == "number":
            # keep only a sane numeric-ish token; reject junk
            if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", val):
                raise ValueError(f"{key} must be a number, got '{val}'")
        lines.append(f"{key}={val}")

    RUNTIME_ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return read_settings()


def _proc_cmdline(pid: str) -> list[str]:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return []
    return [p for p in raw.decode("utf-8", "replace").split("\0") if p]


def _proc_ppid(pid: str) -> str:
    try:
        for line in Path(f"/proc/{pid}/status").read_text("utf-8", "replace").splitlines():
            if line.startswith("PPid:"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return ""


LOOP_HOLD_FILE = REPO_ROOT / "logs" / "LOOP_HOLD"
HOLD_AUDIT_FILE = REPO_ROOT / "logs" / "hold-audit.log"


def read_hold() -> dict[str, Any]:
    """Current mechanical-hold state for the cockpit's Hold/Release control.

    The hold is the only thing that actually stops the loop (a hold DIRECTIVE just
    asks the model to be idle). Two very different things write this file: the
    operator, and the loop itself when a budget gate latches. The panel must show
    WHICH, because releasing an operator pause is routine while releasing a budget
    latch means overriding a spend guard — the file's own text says it is cleared
    'after verifying the accounting is sound'.
    """
    try:
        text = LOOP_HOLD_FILE.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"held": False, "reason": "", "latched": "", "kind": ""}
    reason = ""
    latched = ""
    for line in text.splitlines():
        if line.startswith("reason "):
            reason = line[len("reason "):].strip()
        elif line.startswith("latched "):
            latched = line[len("latched "):].strip()
    kind = "operator" if reason.lower().startswith("operator") else "budget-or-loop"
    return {"held": True, "reason": reason or text.strip()[:200],
            "latched": latched, "kind": kind}


def set_hold(arm: bool, reason: str = "") -> dict[str, Any]:
    """Arm or release the mechanical hold, recording every transition.

    Deliberately NOT symmetric with the loop's own latch: the loop writes this file
    to stop itself on a budget breach; the cockpit writes it because a human said
    so, and says so in the text. Both transitions append to logs/hold-audit.log —
    a release that silently overrode a budget latch is exactly the event you want
    to find later.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prev = read_hold()
    try:
        if arm:
            body = (
                f"latched {now}\n"
                f"reason operator (cockpit): {reason or 'hold requested from the Control Deck'}\n"
                "cleared_by operator only — release from the cockpit, or rm this file, "
                "after verifying the accounting is sound\n"
            )
            LOOP_HOLD_FILE.parent.mkdir(parents=True, exist_ok=True)
            LOOP_HOLD_FILE.write_text(body, encoding="utf-8")
        else:
            if not prev["held"]:
                return {"ok": True, "held": False, "note": "already released"}
            LOOP_HOLD_FILE.unlink(missing_ok=True)
    except OSError as exc:
        return {"ok": False, "error": f"could not {'arm' if arm else 'release'} the hold: {exc}"}
    try:
        with open(HOLD_AUDIT_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts": now, "action": "arm" if arm else "release",
                "via": "cockpit", "reason": reason,
                "previous": {"held": prev["held"], "kind": prev["kind"],
                             "reason": prev["reason"], "latched": prev["latched"]},
            }, ensure_ascii=False) + "\n")
    except OSError:
        pass                      # the audit line is best-effort; the state change is not
    return {"ok": True, **read_hold()}


def wake_loop() -> dict[str, Any]:
    """End the inter-cycle sleep early so the next cycle starts now.

    The alternative ways to hurry a cycle are both worse: a redeploy rebuilds the
    image and resets loop_count, and shortening LOOP_INTERVAL multiplies spend
    against the Claude window permanently, when what is wanted is one cycle now.

    The loop's `sleep "$LOOP_INTERVAL"` is guarded with `|| true` (see
    scripts/core/auto-loop.sh) precisely so this is safe — without that guard
    `set -e` would take the whole loop down with the killed sleep.

    Targeting is deliberately narrow. A cycle in flight ALSO has a `sleep` child:
    the watchdog that enforces CYCLE_TIMEOUT_SECONDS. Killing that one would
    disarm the timeout on a running cycle. The two are told apart by parentage —
    the inter-cycle sleep is a DIRECT child of the main loop process, while the
    watchdog sleep hangs off a subshell — and the state file must additionally
    say the loop is idle. Anything ambiguous is refused rather than guessed at.
    """
    state = read_state_file_pairs()
    status = (state.get("STATUS") or "").lower()
    if status != "idle":
        return {"ok": False, "reason": "busy",
                "error": f"Loop is not sleeping (STATUS={status or 'unknown'}). "
                         "A cycle is already running — nothing to wake."}

    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError as exc:  # noqa: BLE001
        return {"ok": False, "error": f"Cannot read /proc: {exc}"}

    loop_pids = {p for p in pids if any("auto-loop.sh" in a for a in _proc_cmdline(p))}
    if not loop_pids:
        return {"ok": False, "error": "auto-loop.sh is not running in this container."}
    # The main loop is the auto-loop.sh whose parent is not itself auto-loop.sh.
    main = [p for p in loop_pids if _proc_ppid(p) not in loop_pids]
    if len(main) != 1:
        return {"ok": False,
                "error": f"Expected exactly one main loop process, found {len(main)}. "
                         "Refusing to guess which sleep to end."}
    main_pid = main[0]

    targets = []
    for p in pids:
        cmd = _proc_cmdline(p)
        if cmd and cmd[0] == "sleep" and _proc_ppid(p) == main_pid:
            targets.append((p, " ".join(cmd)))
    if not targets:
        return {"ok": False, "error": "No inter-cycle sleep found under the main loop."}
    if len(targets) > 1:
        return {"ok": False,
                "error": f"Found {len(targets)} sleeps under the main loop; refusing to guess."}

    pid, cmd = targets[0]
    try:
        os.kill(int(pid), signal.SIGTERM)
    except OSError as exc:  # noqa: BLE001
        return {"ok": False, "error": f"Could not signal pid {pid}: {exc}"}
    return {"ok": True, "pid": pid, "killed": cmd,
            "message": "Sleep ended — the next cycle starts within seconds."}


def trigger_redeploy() -> dict[str, Any]:
    """Trigger a Coolify redeploy so runtime.env changes take effect.

    Needs COOLIFY_APP_UUID (+ COOLIFY_DEPLOY_TOKEN, COOLIFY_URL) in the container
    env. Degrades gracefully with a clear message when not configured, so editing
    settings works even before the deploy webhook is wired.
    """
    uuid = os.environ.get("COOLIFY_APP_UUID", "").strip()
    token = os.environ.get("COOLIFY_DEPLOY_TOKEN", "").strip()
    base = os.environ.get("COOLIFY_URL", "https://app.coolify.io").strip().rstrip("/")
    if not uuid or not token:
        return {
            "ok": False,
            "configured": False,
            "error": "Redeploy not configured. Set COOLIFY_APP_UUID + "
                     "COOLIFY_DEPLOY_TOKEN (deploy-scoped) in the container env.",
        }
    import urllib.error
    import urllib.request

    url = f"{base}/api/v1/deploy?uuid={uuid}&force=false"
    # Cloudflare returns error 1010 (banned browser signature) to urllib's default
    # User-Agent — a browser-like UA is required, not optional. See
    # memories/redeploy-auto-company.md.
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
            body = resp.read().decode("utf-8", "replace")[:500]
            return {"ok": True, "configured": True, "status": resp.status, "response": body}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "configured": True, "status": exc.code,
                "error": exc.read().decode("utf-8", "replace")[:300]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "configured": True, "error": str(exc)}


# --- ccusage integration (optional, prototype) -------------------------------
# ccusage (https://github.com/ryoppippi/ccusage) reads the local agent transcripts
# (~/.claude/projects + Codex sessions under $CODEX_HOME) and prices tokens against a
# cached table. It fills the loop ledger's blind spot: a $ ESTIMATE for Codex (whose
# ChatGPT-auth runs carry no USD) and a per-model Claude/Codex split. NOTE: this is an
# API-EQUIVALENT estimate, not billed spend — the company runs on flat subscriptions.
# Shelled out + cached (CCUSAGE_TTL_SECONDS), refreshed in a background thread so it
# never blocks the /api/status poll. Fails open when ccusage is absent.
_CCUSAGE_CACHE: dict[str, Any] = {"at": 0.0, "data": None}
_CCUSAGE_REFRESHING = {"v": False}
_CCUSAGE_TTL = int(os.environ.get("CCUSAGE_TTL_SECONDS", "600"))


def _week_start_epoch() -> float:
    """Monday 00:00 UTC of the current ISO week — the weekly cost-display reset
    boundary (operator decision 2026-08-24: panel counters restart weekly; the
    underlying logs and budget-gate ledgers are never touched)."""
    now = datetime.now(timezone.utc)
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0)
    return monday.timestamp()


def _ccusage_compute() -> dict[str, Any]:
    cmd_str = os.environ.get("CCUSAGE_CMD", "ccusage")
    # Weekly reset semantics: the estimate window starts at Monday 00:00 UTC.
    since = datetime.fromtimestamp(_week_start_epoch(), timezone.utc).strftime("%Y%m%d")
    base = shlex.split(cmd_str) + ["daily", "--json", "--since", since]

    def _run(extra: list[str]) -> str | None:
        try:
            proc = subprocess.run(
                base + extra, cwd=str(REPO_ROOT), capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=45,
            )
        except Exception:
            return None
        return (proc.stdout or "").strip() or None

    # Try online (fetches/caches pricing); fall back to --offline for air-gapped hosts.
    raw = _run([]) or _run(["--offline"])
    if not raw:
        return {"available": False, "reason": "ccusage not installed / no output"}

    try:
        daily = (json.loads(raw).get("daily") or [])
        model_cost: dict[str, float] = {}
        for day in daily:
            for mb in (day.get("modelBreakdowns") or []):
                name = str(mb.get("modelName", "?"))
                model_cost[name] = model_cost.get(name, 0.0) + float(mb.get("cost", 0) or 0)

        def _is_codex(n: str) -> bool:
            n = n.lower()
            return n.startswith(("gpt", "o1", "o3", "o4")) or "codex" in n

        claude_cost = sum(c for n, c in model_cost.items() if "claude" in n.lower())
        codex_cost = sum(c for n, c in model_cost.items() if _is_codex(n))
        models = sorted(
            ({"name": n, "cost": round(c, 2)} for n, c in model_cost.items()),
            key=lambda m: m["cost"], reverse=True,
        )[:6]
        today = None
        if daily:
            last = daily[-1]
            today = {"date": str(last.get("period", "")),
                     "cost": round(float(last.get("totalCost", 0) or 0), 2)}
        return {
            "available": True,
            "totalCost": round(sum(model_cost.values()), 2),
            "claudeCost": round(claude_cost, 2),
            "codexCost": round(codex_cost, 2),
            "days": len(daily),
            "since": since,
            "today": today,
            "models": models,
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {"available": False, "reason": f"parse error: {exc}"[:120]}


def read_ccusage() -> dict[str, Any]:
    """Return the cached ccusage estimate; refresh in the background when stale.

    Never blocks: the first call returns a pending marker and kicks off a thread;
    later polls pick up the computed result once it lands.
    """
    now = time.time()
    data = _CCUSAGE_CACHE.get("data")
    fresh = data is not None and (now - float(_CCUSAGE_CACHE.get("at", 0))) < _CCUSAGE_TTL
    if not fresh and not _CCUSAGE_REFRESHING["v"]:
        _CCUSAGE_REFRESHING["v"] = True

        def _bg() -> None:
            try:
                result = _ccusage_compute()
                _CCUSAGE_CACHE.update(at=time.time(), data=result)
            finally:
                _CCUSAGE_REFRESHING["v"] = False

        threading.Thread(target=_bg, daemon=True).start()
    return data if data is not None else {"available": False, "reason": "computing"}


def read_engine_runtime() -> dict[str, Any]:
    """The ACTUAL per-cycle routed engine — Runtime State otherwise shows only the base config.

    The loop boots with ENGINE=claude / MODEL=haiku, but the quota-aware router overrides the
    engine every cycle and a round-robin tier ladder picks the model/effort. This parses the
    log's latest [ROUTER]/[TIER] lines + logs/router-state to surface the real active engine,
    model, effort, the tier ladders, the round-robin index, and the next pick.
    """
    # Read a bounded tail instead of the whole (ever-growing, redeploy-persistent)
    # log on every poll. Every field below takes the LAST match, so the tail is
    # enough — except the once-per-boot banner lines, which can fall outside the
    # window on a long-running container. Detect that by its marker and re-read in
    # full only then, so the common case stays cheap and the rare case stays correct.
    text = read_text_file_tail(LOG_FILE, ENGINE_RUNTIME_TAIL_BYTES, "")
    if "Tier ladder:" not in text or "Window budget:" not in text:
        text = read_text_file(LOG_FILE, "")
    engine = read_text_file(LOG_FILE.parent / "router-state", "").strip().lower()
    out: dict[str, Any] = {"routedEngine": engine}

    # Tolerant to both the fill-weighted line and the legacy round-robin line.
    # The Claude effort group is optional: pre-APP-241 lines carried no
    # `effort=` after the model name, so requiring it would silently fall back
    # to a years-old line instead of the current one.
    tiers = re.findall(
        r"\[TIER\] (\S+).*?Claude=([^\s,\[]+)(?:\s+effort=([A-Za-z0-9_-]+))?"
        r".*?Codex effort=(\w+)",
        text,
    )
    if tiers:
        mode, cmodel, cmeff, ceff = tiers[-1]
        out["tierMode"] = mode
        out["claudePick"] = cmodel
        out["claudeEffort"] = cmeff
        out["codexEffort"] = ceff
        if engine == "codex":
            out["routedModel"] = os.environ.get("CODEX_MODEL", "gpt-5.6-sol")
            out["routedEffort"] = ceff
        else:
            out["routedModel"] = cmodel
            # Was hardcoded "" — since APP-241 a ladder rung carries its own
            # effort (`model:effort`) and the live ladder's rungs differ ONLY
            # by effort (sonnet-5:low..opus-5:high), so a blank field hid the
            # single most decision-relevant value of a Claude cycle.
            out["routedEffort"] = cmeff

    # A one-shot escalation OVERRIDES the ladder's pick for that cycle, and the
    # panel was reporting the pick rather than what ran: on 2026-07-28 the last
    # cycle executed claude-opus-5:high while Runtime State said claude-sonnet-5
    # — from the [TIER] line, which is written before the override is applied.
    # Position, not recency of match, is what decides: [ESCALATE] CONSUMED is
    # logged immediately after [TIER] within the same cycle, so it counts only
    # when it appears AFTER the [TIER] line being reported.
    if tiers and engine != "codex":
        last_tier = text.rfind("[TIER]")
        esc = None
        for m in re.finditer(
            r"\[ESCALATE\] one-shot '\S+' CONSUMED — model=(\S+) effort=(\S+)", text
        ):
            if m.start() > last_tier:
                esc = m
        if esc:
            out["routedModel"] = esc.group(1)
            out["routedEffort"] = esc.group(2)
            out["escalated"] = True

    routers = re.findall(r"\[ROUTER\] (.+)", text)
    if routers:
        out["routerReason"] = routers[-1].strip()[:180]

    # auto-loop.log is PERSISTENT across redeploys (~390 KB / 4700+ lines by
    # 2026-07-28), so everything parsed out of it must take the LAST match.
    # These two used re.search(), which returns the FIRST — pinning the panel
    # to a 2026-07-21 boot: it reported a `$8` budget and a `haiku,sonnet`
    # ladder for a week after both had changed, while `interval` (findall[-1],
    # two lines below) stayed correct. Same function, adjacent lines.
    lad = re.findall(
        r"Tier ladder:.*?Claude \[([^\]]*)\].*?Codex effort \[([^\]]*)\]", text)
    if lad:
        claude_lad, codex_lad = lad[-1]
        out["claudeLadder"] = [s.strip() for s in claude_lad.split(",") if s.strip()]
        out["codexLadder"] = [s.strip() for s in codex_lad.split(",") if s.strip()]

    mb = re.findall(r"Window budget: \$([0-9.]+) per (\d+)s", text)
    if mb:
        out["windowBudget"] = mb[-1][0]
    # APP-263 sonrası CANLI gate'ler boot bannerında "Budget gates ...: ... Daily
    # TOTAL $500 ... Weekly TOTAL $2500" olarak basılır. Eski "Window budget"
    # kalıbı 2026-07-30'da emekli oldu ama kalıcı logdaki Temmuz satırı yüzünden
    # panel "$40 cap" fosilini gösteriyordu (operatör yakaladı, 2026-08-24).
    gates = re.findall(
        r"Budget gates.*?Daily TOTAL \$([0-9.]+).*?Weekly TOTAL \$([0-9.]+)", text)
    if gates:
        out["dailyBudget"], out["weeklyBudget"] = gates[-1]
    itv = re.findall(r"Interval: (\d+)s", text)
    if itv:
        out["interval"] = itv[-1]

    return out


def _window_cutoff_epoch() -> float:
    """The same window boundary auto-loop.sh enforces the budget on.

    The loop's `_window_anchor_epoch()` prefers ccusage's `blockStart` — the start
    of the CURRENT Claude billing block — and only falls back to a rolling
    now-minus-5h when that reading is missing or stale. The dashboard used the
    rolling cutoff unconditionally, so right after a block reset it still counted
    the previous block's spend and then printed that total against the loop's cap:
    on 2026-07-28 the panel showed $49.36 / $40 "over budget" while the component
    that actually enforces the gate saw $10.75 / $40. Two windows, one cap, and the
    number on screen belonged to neither.
    """
    stale_secs = int(os.environ.get("OPERATOR_USAGE_STALE_SECS", "900"))
    cutoff = time.time() - int(os.environ.get("WINDOW_SECONDS", "18000"))
    usage = LOG_FILE.parent / "operator-usage.json"
    try:
        if time.time() - usage.stat().st_mtime > stale_secs:
            return cutoff
        block_start = json.loads(usage.read_text(encoding="utf-8")).get("blockStart")
        if not block_start:
            return cutoff
        anchor = datetime.fromisoformat(
            str(block_start).replace("Z", "+00:00")
        ).timestamp()
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return cutoff
    # Never widen the window past the rolling bound — a stale-but-parseable
    # blockStart from a previous block would otherwise pull in older spend.
    return max(cutoff, anchor)


def read_cost_summary() -> dict[str, Any]:
    """Aggregate cycle cost from auto-loop.log + credit status from ~/.claude.json.

    Cost lines look like: `... [OK] Completed (cost: 2.2577963, subtype: success)`.
    """
    text = read_text_file(LOG_FILE, "")
    costs: list[float] = []
    for m in re.finditer(r"cost:\s*([0-9]+(?:\.[0-9]+)?)\b", text):
        try:
            costs.append(float(m.group(1)))
        except ValueError:
            pass

    # Weekly view (operator decision 2026-08-24): headline counters restart every
    # Monday 00:00 UTC. Computed from the SAME log in one line pass — nothing is
    # rotated or deleted; a line whose timestamp cannot be parsed stays in the
    # all-time totals only (fail-safe: the weekly figure never over-counts).
    week_cut = _week_start_epoch()
    week_usd = 0.0
    week_cycles = week_limits = week_fallbacks = week_offloads = week_gate_pauses = 0
    _ts_re = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]")
    _cost_re = re.compile(r"\(cost:\s*([0-9]+(?:\.[0-9]+)?)")
    for line in text.splitlines():
        tm = _ts_re.match(line)
        if not tm:
            continue
        try:
            ts = datetime.strptime(tm.group(1), "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc).timestamp()
        except ValueError:
            continue
        if ts < week_cut:
            continue
        cm = _cost_re.search(line)
        if cm:
            try:
                week_usd += float(cm.group(1))
                week_cycles += 1
            except ValueError:
                pass
        if "[LIMIT]" in line:
            week_limits += 1
        if "[FALLBACK]" in line:
            week_fallbacks += 1
        if "offloading to Codex" in line or "[BUDGET-CODEX]" in line:
            week_offloads += 1
        # A REAL pause, not the hourly "[BUDGET]" status line the old counter
        # mislabeled as pauses (487 status lines read as 487 pauses).
        if "[GATE]" in line and "paus" in line.lower():
            week_gate_pauses += 1

    credit_reason = ""
    try:
        cj = Path.home() / ".claude.json"
        if cj.exists():
            data = json.loads(cj.read_text(encoding="utf-8"))
            credit_reason = str(data.get("cachedExtraUsageDisabledReason", "") or "")
    except Exception:  # pragma: no cover - defensive
        credit_reason = ""

    window_usd = 0.0
    try:
        ledger = LOG_FILE.parent / "spend-window.log"
        if ledger.exists():
            cutoff = _window_cutoff_epoch()
            for line in ledger.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if len(parts) == 2:
                    try:
                        ts, c = float(parts[0]), float(parts[1])
                        if ts >= cutoff:
                            window_usd += c
                    except ValueError:
                        pass
    except Exception:  # pragma: no cover - defensive
        window_usd = 0.0

    # Current routed engine (the loop writes claude|codex to logs/router-state).
    engine = read_text_file(LOG_FILE.parent / "router-state", "").strip().lower() or ""

    # Codex cycles inside the rolling window (each line in codex-window.log is one
    # completed Codex cycle: "<epoch> <count> ..."). Lets the operator SEE Codex is
    # carrying load even though Codex cycles cost $0 (ChatGPT-auth) so windowUsd stays flat.
    codex_window = 0
    try:
        cl = LOG_FILE.parent / "codex-window.log"
        if cl.exists():
            ccut = time.time() - int(os.environ.get("WINDOW_SECONDS", "18000"))
            for line in cl.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if parts:
                    try:
                        if float(parts[0]) >= ccut:
                            codex_window += 1
                    except ValueError:
                        pass
    except Exception:  # pragma: no cover - defensive
        codex_window = 0

    # Budget offloads to Codex. The router logs "... offloading to Codex"; older builds
    # tagged "[BUDGET-CODEX]". Count both so the counter reflects real offloads.
    budget_offloads = text.count("offloading to Codex") + text.count("[BUDGET-CODEX]")

    return {
        "totalUsd": round(sum(costs), 4),
        "lastUsd": round(costs[-1], 4) if costs else 0.0,
        "cycles": len(costs),
        "creditReason": credit_reason,
        "limitHits": text.count("[LIMIT]"),
        "windowUsd": round(window_usd, 4),
        # key name kept for frontend compatibility; the value is the APP-263
        # Claude 5h gate (WINDOW_BUDGET_USD is deprecated and ignored)
        "windowBudget": os.environ.get("CLAUDE_5H_BUDGET_USD", "") or "",
        "fallbackHits": text.count("[FALLBACK]"),
        "budgetPauses": text.count("[BUDGET]"),
        "budgetOffloads": budget_offloads,
        "engine": engine,
        "codexWindow": codex_window,
        # Weekly window (resets Monday 00:00 UTC) — the panel's headline figures.
        "weekUsd": round(week_usd, 4),
        "weekCycles": week_cycles,
        "weekLimitHits": week_limits,
        "weekFallbacks": week_fallbacks,
        "weekOffloads": week_offloads,
        "weekGatePauses": week_gate_pauses,
        "weekStart": datetime.fromtimestamp(week_cut, timezone.utc).strftime("%Y-%m-%d"),
        # Canlı gate görünümü: loop'un kendi [BUDGET] satırının SON hali —
        # "Daily TOTAL $10.63/$500 | Weekly TOTAL $28.46/$2500". Gate'i uygulayan
        # bileşenle aynı sayı; panel artık emekli 5h penceresini değil bunu gösterir.
        **_last_budget_gate(text),
        "ccusage": read_ccusage(),
    }


def _last_budget_gate(text: str) -> dict[str, Any]:
    m = re.findall(
        r"\[BUDGET\].*?Daily TOTAL \$([0-9.]+)/\$([0-9.]+)"
        r".*?Weekly TOTAL \$([0-9.]+)/\$([0-9.]+)", text)
    if not m:
        return {}
    d_used, d_cap, w_used, w_cap = m[-1]
    return {"gateDailyUsd": float(d_used), "gateDailyCap": float(d_cap),
            "gateWeeklyUsd": float(w_used), "gateWeeklyCap": float(w_cap)}


def read_tail(path: Path, lines: int = 120) -> str:
    if lines <= 0:
        return ""
    text = read_text_file(path, "")
    if not text:
        return ""
    rows = text.splitlines()
    return "\n".join(rows[-lines:])


def parse_sections(raw: str) -> dict[str, list[str]]:
    section_re = re.compile(r"^=== (.+) ===$")
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in raw.splitlines():
        row = line.rstrip("\n")
        match = section_re.match(row.strip())
        if match:
            current = match.group(1)
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(row)

    return sections


def parse_int(value: str | None) -> int | None:
    if not value:
        return None
    value = value.strip()
    return int(value) if value.isdigit() else None


def parse_positive_int(value: str | None, default: int) -> int:
    try:
        parsed = int(value or "")
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def parse_key_values(rows: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for row in rows:
        if "=" not in row:
            continue
        key, value = row.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def blank_parsed() -> dict[str, Any]:
    return {
        "guardian": {"state": "unknown", "pid": None, "raw": ""},
        "autostart": {"state": "unknown", "raw": ""},
        "daemon": {
            "state": "unknown",
            "activeState": "unknown",
            "subState": "unknown",
            "mainPid": None,
            "raw": "",
        },
        "loop": {
            "state": "unknown",
            "pid": None,
            "daemonSummary": "unknown",
            "engine": "",
            "model": "",
            "lastRun": "",
            "errorCount": "",
            "loopCount": "",
            "raw": "",
        },
        "consensusPreview": "",
        "recentLog": "",
    }


def parse_windows_status_output(raw: str) -> dict[str, Any]:
    sections = parse_sections(raw)
    parsed = blank_parsed()

    guardian_rows = sections.get("Windows Guardian", [])
    guardian_line = next(
        (x.strip() for x in guardian_rows if x.strip().startswith("Awake guardian:")),
        "",
    )
    parsed["guardian"]["raw"] = "\n".join(guardian_rows).strip()
    if guardian_line:
        parsed["guardian"]["raw"] = guardian_line
        if "STOPPED" in guardian_line:
            parsed["guardian"]["state"] = "stopped"
        elif "RUNNING" in guardian_line:
            parsed["guardian"]["state"] = "running"
            pid_match = re.search(r"PID (\d+)", guardian_line)
            parsed["guardian"]["pid"] = int(pid_match.group(1)) if pid_match else None

    autostart_rows = sections.get("Windows Autostart Task", [])
    autostart_line = next(
        (x.strip() for x in autostart_rows if x.strip().startswith("Autostart:")),
        "",
    )
    parsed["autostart"]["raw"] = "\n".join(autostart_rows).strip()
    if autostart_line:
        parsed["autostart"]["raw"] = autostart_line
        if "NOT CONFIGURED" in autostart_line:
            parsed["autostart"]["state"] = "not_configured"
        elif "CONFIGURED" in autostart_line:
            parsed["autostart"]["state"] = "configured"

    daemon_rows = sections.get("WSL Daemon (systemd --user)", [])
    parsed["daemon"]["raw"] = "\n".join(daemon_rows).strip()
    daemon_compact = [x.strip() for x in daemon_rows if x.strip()]
    if daemon_compact:
        first = daemon_compact[0]
        lowered = first.lower()
        if "not installed" in lowered:
            parsed["daemon"]["state"] = "not_installed"
        elif first == "active":
            parsed["daemon"]["state"] = "active"
        elif first in {"inactive", "activating", "failed"}:
            parsed["daemon"]["state"] = "inactive"
        for row in daemon_compact:
            if row.startswith("MainPID="):
                parsed["daemon"]["mainPid"] = parse_int(row.split("=", 1)[1])
            elif row.startswith("ActiveState="):
                parsed["daemon"]["activeState"] = row.split("=", 1)[1].strip()
            elif row.startswith("SubState="):
                parsed["daemon"]["subState"] = row.split("=", 1)[1].strip()

    loop_rows = sections.get("Loop Status (scripts/core/monitor.sh)", [])
    if not loop_rows:
        loop_rows = sections.get("Loop Status (monitor.sh)", [])
    loop_status_rows = sections.get("Auto Company Status", [])
    merged_loop_rows = list(loop_rows) + list(loop_status_rows)
    parsed["loop"]["raw"] = "\n".join(merged_loop_rows).strip()
    for row in (x.strip() for x in merged_loop_rows if x.strip()):
        if row.startswith("Loop:"):
            if "NOT RUNNING" in row or "STOPPED" in row:
                parsed["loop"]["state"] = "stopped"
                parsed["loop"]["pid"] = None
            elif "RUNNING" in row:
                parsed["loop"]["state"] = "running"
                pid_match = re.search(r"PID (\d+)", row)
                parsed["loop"]["pid"] = int(pid_match.group(1)) if pid_match else None
        elif row.startswith("Daemon:"):
            parsed["loop"]["daemonSummary"] = row.replace("Daemon:", "", 1).strip()
        elif row.startswith("ENGINE="):
            parsed["loop"]["engine"] = row.split("=", 1)[1].strip()
        elif row.startswith("MODEL="):
            parsed["loop"]["model"] = row.split("=", 1)[1].strip()
        elif row.startswith("LAST_RUN="):
            parsed["loop"]["lastRun"] = row.split("=", 1)[1].strip()
        elif row.startswith("ERROR_COUNT="):
            parsed["loop"]["errorCount"] = row.split("=", 1)[1].strip()
        elif row.startswith("LOOP_COUNT="):
            parsed["loop"]["loopCount"] = row.split("=", 1)[1].strip()

    parsed["consensusPreview"] = "\n".join(sections.get("Latest Consensus", [])).strip()
    parsed["recentLog"] = "\n".join(sections.get("Recent Log", [])).strip()
    return parsed


def parse_macos_status_output(raw: str) -> dict[str, Any]:
    sections = parse_sections(raw)
    parsed = blank_parsed()

    guardian_fields = parse_key_values(sections.get("Guardian", []))
    parsed["guardian"]["state"] = guardian_fields.get("State", "unknown") or "unknown"
    parsed["guardian"]["pid"] = parse_int(guardian_fields.get("Pid"))
    parsed["guardian"]["raw"] = guardian_fields.get("Raw", "")

    daemon_fields = parse_key_values(sections.get("Daemon", []))
    daemon_state = daemon_fields.get("State", "unknown") or "unknown"
    parsed["daemon"]["state"] = daemon_state
    parsed["daemon"]["mainPid"] = parse_int(daemon_fields.get("MainPID"))
    parsed["daemon"]["raw"] = daemon_fields.get("Raw", "")
    parsed["daemon"]["activeState"] = daemon_fields.get("ActiveState", daemon_state)
    parsed["daemon"]["subState"] = daemon_fields.get("SubState", "unknown")

    autostart_fields = parse_key_values(sections.get("Autostart", []))
    parsed["autostart"]["state"] = autostart_fields.get("State", "unknown") or "unknown"
    parsed["autostart"]["raw"] = autostart_fields.get("Raw", "")

    loop_fields = parse_key_values(sections.get("Loop", []))
    parsed["loop"]["state"] = loop_fields.get("State", "unknown") or "unknown"
    parsed["loop"]["pid"] = parse_int(loop_fields.get("Pid"))
    parsed["loop"]["raw"] = "\n".join(sections.get("Loop", [])).strip()
    parsed["loop"]["daemonSummary"] = loop_fields.get("DaemonSummary", "unknown")

    state_file_fields = parse_key_values(sections.get("State File", []))
    parsed["loop"]["engine"] = state_file_fields.get("ENGINE", "")
    parsed["loop"]["model"] = state_file_fields.get("MODEL", "")
    parsed["loop"]["lastRun"] = state_file_fields.get("LAST_RUN", "")
    parsed["loop"]["errorCount"] = state_file_fields.get("ERROR_COUNT", "")
    parsed["loop"]["loopCount"] = state_file_fields.get("LOOP_COUNT", "")

    parsed["consensusPreview"] = "\n".join(sections.get("Latest Consensus", [])).strip()
    parsed["recentLog"] = "\n".join(sections.get("Recent Log", [])).strip()
    return parsed


def read_state_file_pairs() -> dict[str, str]:
    state_text = read_text_file(STATE_FILE, "").strip()
    state_pairs: dict[str, str] = {}
    if state_text:
        for row in state_text.splitlines():
            if "=" in row:
                key, value = row.split("=", 1)
                state_pairs[key.strip()] = value.strip()
    return state_pairs


def run_status_command(system_name: str | None = None) -> dict[str, Any]:
    profile = get_host_profile(system_name)
    runner = profile["runner"]
    return runner(profile["status_script"], timeout=90)


def run_dashboard_action(action: str, system_name: str | None = None) -> dict[str, Any]:
    profile = get_host_profile(system_name)
    if action == "start":
        return profile["runner"](
            profile["start_script"], args=profile["start_args"], timeout=120
        )
    if action == "stop":
        return profile["runner"](
            profile["stop_script"], args=profile["stop_args"], timeout=120
        )
    if action == "refresh":
        return profile["runner"](profile["status_script"], timeout=90)
    raise ValueError(f"Unsupported dashboard action: {action}")


def parse_status_output(raw: str, system_name: str | None = None) -> dict[str, Any]:
    profile = get_host_profile(system_name)
    return profile["parser"](raw)


def gather_status_payload(system_name: str | None = None) -> dict[str, Any]:
    result = run_status_command(system_name)
    parsed = parse_status_output(result["output"], system_name)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ok": result["ok"],
        "exitCode": result["exitCode"],
        "elapsedMs": result["elapsedMs"],
        "hostKind": detect_host_kind(system_name),
        "raw": result["output"],
        "parsed": parsed,
        "stateFile": read_state_file_pairs(),
        "consensusHead": read_text_file(CONSENSUS_FILE, "(no consensus file)")[:3000],
        "consensusBytes": len(read_text_file(CONSENSUS_FILE, "").encode("utf-8")),
        "hold": read_hold(),
        "logTail": read_tail(LOG_FILE, lines=180),
        "directive": read_directive(),
        "cost": read_cost_summary(),
        "router": read_engine_runtime(),
        "graft": read_graft_freshness(),
    }


def read_graft_freshness() -> dict[str, Any]:
    """Freshness of the git-tracked graft cards, written by scripts/graft-auto-refresh.py
    at each session start. Local-only: the cards and their commits-behind are a git fact on
    the operator's Mac, so the container cockpit (no .git, no local hook) reports n/a."""
    try:
        data = json.loads(
            (REPO_ROOT / "logs" / "graft-freshness.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return {"available": False}
    return data if isinstance(data, dict) else {"available": False}


class DashboardHandler(BaseHTTPRequestHandler):
    def _json(self, payload: dict[str, Any], code: int = 200) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _text(
        self, text: str, code: int = 200, content_type: str = "text/plain; charset=utf-8"
    ) -> None:
        raw = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self._text("Not found", code=404)
            return
        self._text(path.read_text(encoding="utf-8"), content_type=content_type)

    def do_GET(self) -> None:  # noqa: N802
        try:
            self._do_GET()
        except Exception:
            sentry_client.capture_exception(extra={"method": "GET", "path": self.path})
            raise

    def _do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._serve_file(DASHBOARD_DIR / "index.html", "text/html; charset=utf-8")
            return
        if path == "/app.js":
            self._serve_file(
                DASHBOARD_DIR / "app.js",
                "application/javascript; charset=utf-8",
            )
            return
        if path == "/styles.css":
            self._serve_file(DASHBOARD_DIR / "styles.css", "text/css; charset=utf-8")
            return
        if path == "/favicon.svg":
            self._serve_file(DASHBOARD_DIR / "favicon.svg", "image/svg+xml")
            return
        if path == "/api/status":
            self._json(gather_status_payload())
            return
        if path == "/api/log-tail":
            qs = parse_qs(parsed.query)
            lines = parse_positive_int(qs.get("lines", ["180"])[0], default=180)
            self._json(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "lines": lines,
                    "logTail": read_tail(LOG_FILE, lines=lines),
                }
            )
            return
        if path == "/api/ideas":
            self._json(read_ideas())
            return
        if path == "/api/tool-usage":
            self._json(read_tool_usage())
            return
        if path == "/api/consensus":
            # The status payload carries a 3000-char HEAD only (it is polled every few
            # seconds; shipping the whole 27KB file on every poll would be wasteful).
            # This endpoint serves the full file for the panel's "show all" toggle —
            # fetched on demand, never on the poll path.
            text = read_text_file(CONSENSUS_FILE, "(no consensus file)")
            self._json({"bytes": len(text.encode("utf-8")), "text": text})
            return
        if path == "/api/analysis":
            self._json(read_analysis())
            return
        if path == "/api/settings":
            self._json(read_settings())
            return
        if path == "/api/operator-requests":
            self._json(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **read_operator_requests(),
                }
            )
            return

        if path == "/api/directive-templates":
            self._json(read_directive_templates())
            return

        self._text("Not found", code=404)

    def _read_body(self, limit: int = 64 * 1024) -> bytes:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0:
            return b""
        return self.rfile.read(min(length, limit))

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._do_POST()
        except Exception:
            sentry_client.capture_exception(extra={"method": "POST", "path": self.path})
            raise

    def _do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/directive":
            self._handle_directive()
            return

        if path == "/api/settings":
            self._handle_settings()
            return

        if path == "/api/operator-decision":
            self._handle_operator_decision()
            return

        if path in {"/api/hold", "/api/hold/release"}:
            arm = path == "/api/hold"
            reason = ""
            if arm:
                try:
                    length = int(self.headers.get("Content-Length") or 0)
                    if length:
                        reason = str(json.loads(self.rfile.read(length)).get("reason") or "")[:200]
                except (ValueError, json.JSONDecodeError):
                    reason = ""
            result = set_hold(arm, reason)
            result["timestamp"] = datetime.now(timezone.utc).isoformat()
            self._json(result, code=HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/wake":
            result = wake_loop()
            result["timestamp"] = datetime.now(timezone.utc).isoformat()
            self._json(result, code=HTTPStatus.OK if result.get("ok") else HTTPStatus.CONFLICT)
            return

        if path == "/api/analyst/run":
            result = analyst_run_now()
            result["timestamp"] = datetime.now(timezone.utc).isoformat()
            self._json(result, code=HTTPStatus.OK if result.get("ok") else HTTPStatus.CONFLICT)
            return

        if path == "/api/redeploy":
            result = trigger_redeploy()
            result["timestamp"] = datetime.now(timezone.utc).isoformat()
            self._json(result, code=HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST)
            return

        if path not in {"/api/action/start", "/api/action/stop", "/api/action/refresh"}:
            self._text("Not found", code=404)
            return

        action = path.rsplit("/", 1)[-1]
        result = run_dashboard_action(action)
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "ok": result["ok"],
            "exitCode": result["exitCode"],
            "elapsedMs": result["elapsedMs"],
            "output": result["output"],
        }
        self._json(payload, code=HTTPStatus.OK if result["ok"] else HTTPStatus.BAD_REQUEST)

    def _handle_operator_decision(self) -> None:
        body = self._read_body()
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
            if not isinstance(data, dict):
                data = {}
        except (ValueError, UnicodeDecodeError):
            data = {}

        raw_fields = data.get("fields")
        fields = {
            label: str(raw_fields.get(label, ""))
            for label in AUTH_LABELS
            if isinstance(raw_fields, dict)
        }
        try:
            result = write_operator_decision(
                str(data.get("id", "")),
                str(data.get("decision", "")),
                fields,
                str(data.get("reason", "")),
            )
        except ValueError as exc:
            self._json(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "ok": False,
                    "error": str(exc),
                },
                code=HTTPStatus.BAD_REQUEST,
            )
            return

        self._json(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ok": True,
                "result": result,
                **read_operator_requests(),
            }
        )

    def _handle_directive(self) -> None:
        body = self._read_body()
        text = ""
        allow_pending = False
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
            if isinstance(data, dict):
                text = str(data.get("directive", ""))
                allow_pending = bool(data.get("allowPending", False))
        except (ValueError, UnicodeDecodeError):
            text = ""

        try:
            directive = write_directive(text, allow_pending=allow_pending)
        except DirectiveRefused as exc:
            # 409, not 400: the request was well-formed and the writer refused it.
            # Only a PENDING refusal is retryable with allowPending (the panel asks
            # first); size-brake and section-reference refusals are not.
            self._json(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "ok": False,
                    "refused": True,
                    "needsAllowPending": "PENDING" in str(exc),
                    "error": str(exc),
                },
                code=HTTPStatus.CONFLICT,
            )
            return
        except ValueError as exc:
            self._json(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "ok": False,
                    "error": str(exc),
                },
                code=HTTPStatus.BAD_REQUEST,
            )
            return

        self._json(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ok": True,
                "directive": directive,
            }
        )

    def _handle_settings(self) -> None:
        body = self._read_body()
        incoming: dict[str, Any] = {}
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
            if isinstance(data, dict):
                incoming = data.get("values", data) if isinstance(data.get("values", data), dict) else {}
        except (ValueError, UnicodeDecodeError):
            incoming = {}

        try:
            settings = write_settings(incoming)
        except ValueError as exc:
            self._json(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "ok": False,
                    "error": str(exc),
                },
                code=HTTPStatus.BAD_REQUEST,
            )
            return

        self._json(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ok": True,
                "settings": settings,
            }
        )

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        _ = (fmt, args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto Company web dashboard server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    try:
        host_kind = detect_host_kind()
    except RuntimeError as exc:
        print(f"[dashboard] {exc}")
        raise SystemExit(1) from exc

    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"[dashboard] serving on http://{args.host}:{args.port}")
    print(f"[dashboard] repo: {REPO_ROOT}")
    print(f"[dashboard] host: {host_kind}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("[dashboard] stopped")


if __name__ == "__main__":
    os.chdir(REPO_ROOT)
    main()
