#!/usr/bin/env python3
"""work-window.py — a mechanical brake against the recurring empty-cycle STALL.

The failure it targets: when a tracked surface changes (an OPREQ resolves, the
Wowcar source set is re-based, an operator decision lands), `state-snapshot.py`
emits `DELTA: changed=<fields>` for exactly ONE cycle. The loop works the first
piece of that change, then the next cycle sees `DELTA: none` and — per Runtime
Guardrail 10 — legitimately emits an "EMPTY CYCLE" confirmation while the change's
FOLLOW-ON work is still orphaned. Observed twice (source re-base; §5 OPREQ resolve).

The brake: any `DELTA: changed` opens a K-cycle WORK WINDOW. While the window is
open, the harness (a) does not IDLE-SKIP and (b) injects an order into
<cycle_orders> stating that an empty-cycle confirmation is NOT valid — the model
must advance one queued item, or explicitly enumerate what is blocked-by-authority.

Contract with the harness (`scripts/core/auto-loop.sh`):
  stdin  : the captured state-snapshot block (must contain a `DELTA:` line)
  args   : --cycle N (current loop counter), --app PATH, --ttl K
  stdout : the injection line if the window is OPEN, else empty
  exit   : 10 = window OPEN (brake engaged), 0 = window CLOSED (normal idle allowed)

Fail-closed: an unreadable/corrupt state file, or a snapshot with no parseable
DELTA line, is treated as window OPEN (exit 10) — not-measuring is itself a brake
condition. The discretionary-spend cap remains the money backstop, so a stuck-open
window cannot burn unboundedly. Kill switch: WORK_WINDOW_ENABLED=0.

This script writes ONLY logs/work-window.json (atomic tmp+rename); it never fails
the loop (any internal error still exits 10 with a generic line, fail-closed).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DELTA_RE = re.compile(r"^DELTA:\s*(none|first snapshot|changed=(.+?))\s*(?:—.*)?$", re.MULTILINE)
STATE_REL = "logs/work-window.json"
DEFAULT_TTL = 5
# Directive-closed rule (operator decision 2026-10-13). When the ONLY fields that moved are
# the directive's own (status/sha) AND the snapshot reports Status DONE, the change is the
# liaison pulling DONE or archiving a finished section: there is no follow-on work for the
# company, so the window must not open, and a window still open from the directive's PENDING
# phase is closed. A new directive append flips Status back to PENDING and opens it as before.
# Unparseable status = not DONE (fail-closed: window opens).
DIRECTIVE_FIELDS = {"directive_status", "directive_sha16"}
# Auditor rule (operator decision 2026-10-13, same day). A new auditor report
# (`auditor_hash`) carries no company work by itself: auditor proposals reach the company
# only after the sponsor says "işle" (directive K7), and that arrives as a directive append,
# which opens the window on its own. So an auditor-only change neither opens nor closes a
# window (an existing directive window stays as it is); together with a DONE-only directive
# change it closes like the directive rule. Observed: cycles 1004-1008 forced non-idle.
NO_WORK_FIELDS = {"auditor_hash"}
DIRECTIVE_STATUS_RE = re.compile(r"^directive:\s*status=([A-Z_-]+)", re.MULTILINE)


def _app_dir(arg: str | None) -> Path:
    if arg:
        return Path(arg).resolve()
    # scripts/ops/work-window.py -> repo root is parents[2]
    return Path(__file__).resolve().parents[2]


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _parse_delta(block: str) -> tuple[str, str]:
    """Return (kind, fields) where kind in {none, first, changed, unknown}."""
    m = DELTA_RE.search(block or "")
    if not m:
        return ("unknown", "")
    if m.group(1) == "none":
        return ("none", "")
    if m.group(1).startswith("first"):
        return ("first", "")
    return ("changed", (m.group(2) or "").strip())


def _read_state(path: Path) -> tuple[dict | None, bool]:
    """Return (state, corrupt). Missing file is (None, False); unreadable is (None, True)."""
    if not path.is_file():
        return (None, False)
    try:
        return (json.loads(path.read_text(encoding="utf-8")), False)
    except Exception:
        return (None, True)


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _line(reason: str, age: int, ttl: int) -> str:
    reason = reason or "a tracked surface"
    return (
        f"WORK-WINDOW OPEN — a tracked surface changed ({reason}) {age} cycle(s) ago "
        f"(window {age + 1}/{ttl}). The follow-on work from that change is likely "
        f"incomplete, so an EMPTY-CYCLE confirmation is NOT a valid output this cycle: "
        f"advance exactly ONE item from the Next Action queue (research→CFO→critic→CEO, "
        f"evidence-gated). You may skip work ONLY if EVERY remaining item is genuinely "
        f"blocked-by-authority (sponsor/counsel/author) — and then you MUST list each "
        f"blocked item and its blocker explicitly, never a bare empty-cycle line."
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycle", type=int, required=True)
    ap.add_argument("--app", default=None)
    ap.add_argument("--ttl", type=int, default=None)
    args = ap.parse_args()

    # Kill switch — behave as if the brake does not exist.
    if os.environ.get("WORK_WINDOW_ENABLED", "1").strip() == "0":
        return 0

    ttl = args.ttl if args.ttl is not None else _env_int("WORK_WINDOW_TTL_CYCLES", DEFAULT_TTL)
    if ttl < 1:
        ttl = DEFAULT_TTL
    app = _app_dir(args.app)
    state_path = app / STATE_REL

    try:
        block = sys.stdin.read()
    except Exception:
        block = ""
    kind, fields = _parse_delta(block)

    state, corrupt = _read_state(state_path)
    if corrupt:
        # Fail-closed: cannot trust the window bookkeeping -> keep the brake engaged.
        sys.stdout.write(_line("unreadable work-window state", 0, ttl) + "\n")
        return 10

    cycle = args.cycle

    # Directive-closed + auditor rules: changes that carry no company work.
    if kind == "changed":
        moved = {f.strip() for f in fields.split(",") if f.strip()}
        sm = DIRECTIVE_STATUS_RE.search(block or "")
        if moved and moved <= NO_WORK_FIELDS:
            kind = "none"  # behave as if nothing moved: the stored window (if any) decides
        elif (moved and moved <= DIRECTIVE_FIELDS | NO_WORK_FIELDS and moved & DIRECTIVE_FIELDS
              and sm and sm.group(1) == "DONE"):
            try:
                _write_state(state_path, {"opened_at_cycle": cycle, "reason_fields": fields,
                                          "ttl_cycles": 0, "updated_at_cycle": cycle,
                                          "closed_reason": "directive DONE"})
            except Exception:
                pass  # closed either way: an unwritten state only risks an old window lingering
            return 0

    # A fresh change (re)opens the window at this cycle.
    if kind == "changed":
        new_state = {"opened_at_cycle": cycle, "reason_fields": fields, "ttl_cycles": ttl,
                     "updated_at_cycle": cycle}
        try:
            _write_state(state_path, new_state)
        except Exception:
            pass  # never fail the loop; window is still OPEN below
        sys.stdout.write(_line(fields, 0, ttl) + "\n")
        return 10

    if kind == "unknown":
        # No parseable DELTA -> fail-closed OPEN, but do not disturb stored window.
        sys.stdout.write(_line("snapshot DELTA unreadable", 0, ttl) + "\n")
        return 10

    # kind in {none, first}: window open only if a stored window is still within TTL.
    if state:
        opened = int(state.get("opened_at_cycle", -10**9))
        stored_ttl = int(state.get("ttl_cycles", ttl))
        age = cycle - opened
        if 0 <= age < stored_ttl:
            sys.stdout.write(_line(state.get("reason_fields", ""), age, stored_ttl) + "\n")
            return 10

    # Window closed — normal idle behaviour permitted.
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Absolute fail-closed: any unexpected error keeps the brake engaged.
        sys.stdout.write("WORK-WINDOW OPEN — internal error in work-window.py; "
                         "empty-cycle NOT valid this cycle, advance one Next Action item.\n")
        sys.exit(10)
