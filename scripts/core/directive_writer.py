#!/usr/bin/env python3
"""The ONE way `memories/human-directive.md` is written.

Five writers used to touch this file, each its own way, none of them locking and
only one refusing to clobber in-flight work. On 2026-07-29 a census found the
worst of them — the analyst's snapshot/restore — able to silently revert an
operator's PENDING instruction for up to ~50 minutes, logged under a message that
described the opposite of what it did. Backing the file up first would have made
that loss recoverable; it would not have stopped it happening.

So every write goes through this pipeline, operator-specified:

    lock → read current status+hash → in-flight gate → persistent backup
    → temp file → atomic rename → read-back + hash verify → audit → notify

Two rules the pipeline exists to enforce, both of them fail-closed:

  * **In-flight work is not clobbered.** A PENDING directive is a live
    instruction. Overwriting it needs `--allow-pending`, which is a choice
    someone makes, not a default.
  * **The body is immutable after acceptance.** The only permitted change to an
    accepted directive is its `## Status` value, and only via `status`, which is
    a compare-and-swap: it verifies the body is byte-identical to what the caller
    was given before it moves anything. A model must never write this file; it
    produces a receipt and calls this.

Subcommands
  write   --body-file F [--allow-pending] [--actor NAME]
  append  --section-file F [--allow-pending] [--force-size]
  archive --drop-prefix P [--drop-prefix P ...] --summary-file S [--allow-pending]
  status  --expect-status S --to S2 --expect-body-sha256 H [--receipt F]
  restore --from-file SNAP --expect-sha256 H [--actor NAME]
  show    [--sections]

`append` / `archive` (2026-10-13). `write` REPLACES the whole body, so for two
months every operator addendum re-sent the entire live body with a section
glued on; closed sections never left, the body reached 166 KB (10-11) and 82 KB
again (10-13), and the loop — which reads this file every cycle — kept treating
stale "standing queues" as binding. `append` adds ONE `## ` section to the live
body through the same lock → gate → backup → atomic → verify → audit pipeline
(so the loop's directive_unaudited check stays green) and sets Status PENDING.
`archive` moves closed sections VERBATIM into `memories/human-directive-archive.md`
and puts a short summary in their place; the first chunk (everything before the
first `## ` heading after `## Directive` — the ANA DİREKTİF) is never touched,
and a section carrying `Resolves:` / `Decision for …:` lines (OPREQ resolver
input) can only go if the summary carries the same lines. Status is NOT changed
by `archive`. Size brake: a body over DIRECTIVE_BODY_WARN_BYTES (50000) warns
on stderr + Telegram; over DIRECTIVE_BODY_MAX_BYTES (90000) `append` refuses
unless --force-size. `show --sections` prints heading + bytes.

Exit codes: 0 ok · 2 refused by a gate (in-flight, hash mismatch, size) · 3 I/O
or verification failure. A refusal is a normal outcome and says why on stderr.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

APP = Path(os.environ.get("AC_APP_DIR", "/app"))
DIRECTIVE = APP / "memories" / "human-directive.md"
BACKUPS = APP / "memories" / "human-directive-backups"
RECOVERY = APP / "memories" / "human-directive-recovery"
AUDIT = APP / "memories" / "directive-audit.log"
LOCK = APP / "memories" / ".human-directive.lock"
NOTIFY = APP / "scripts" / "core" / "telegram-notify.sh"
ARCHIVE = APP / "memories" / "human-directive-archive.md"

STATUS_RE = re.compile(r"^## Status\s*\n(\S+)\s*$", re.MULTILINE)
DIRECTIVE_MARK = "\n## Directive\n"
RESOLVER_LINE_RE = re.compile(r"^(Resolves:|Decision for )", re.MULTILINE)

# Size brake (2026-10-13). The loop reads the whole file every cycle; measured
# 2026-10-11: 166 KB body → prompt over the 120 KB argv cap for 11 cycles.
WARN_BYTES = int(os.environ.get("DIRECTIVE_BODY_WARN_BYTES", "50000"))
MAX_BYTES = int(os.environ.get("DIRECTIVE_BODY_MAX_BYTES", "90000"))

# OPREQ-GOV-DIRECTIVE-BODY-001 (operator-authorized 2026-08-11 via the cockpit
# operator-decision panel — memories/operator-decisions.md). Two consecutive
# directive revisions shipped structurally broken: revision 11 referenced §6
# (twice) and §7 (three times) with neither section defined anywhere in its own
# body, which made its Completion condition (e) unsatisfiable and froze it in
# PENDING with no company-reachable exit. This check catches exactly that shape
# before a body is ever written: every "§N" REFERENCE must have a matching
# "## §N" HEADER somewhere in the same body. It is intentionally narrow — it
# says nothing about whether the section's CONTENT is correct, only whether the
# number it points at exists at all.
SECTION_HEADER_RE = re.compile(r"^##\s*§(\d+)\b", re.MULTILINE)
SECTION_REF_RE = re.compile(r"§(\d+)\b")


def undefined_section_refs(body: str) -> list[str]:
    """Section numbers referenced via '§N' with no matching '## §N' header.

    Sorted numerically, empty when the body is clean. Pure text check, no I/O,
    no live-state dependency, no judgment of policy content — see the OPREQ
    comment above.
    """
    defined = {m.group(1) for m in SECTION_HEADER_RE.finditer(body)}
    referenced = {m.group(1) for m in SECTION_REF_RE.finditer(body)}
    return sorted(referenced - defined, key=int)


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_live() -> tuple[str, str, str]:
    """(text, sha256, status) — empty strings when the file is absent."""
    if not DIRECTIVE.exists():
        return "", "", ""
    text = DIRECTIVE.read_text(encoding="utf-8")
    m = STATUS_RE.search(text)
    return text, sha(text), (m.group(1) if m else "")


def body_of(text: str) -> str:
    """Everything except the Status VALUE — what must not change on a transition.

    The status line is normalized to a placeholder rather than deleted, so a
    caller cannot smuggle a body edit past the comparison by also deleting the
    heading.
    """
    return STATUS_RE.sub("## Status\n\x00", text)


def audit(action: str, actor: str, before: str, after: str, detail: str) -> None:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    line = (f"{now()}\taction={action}\tactor={actor}"
            f"\tbefore_sha={before[:16] or '-'}\tafter_sha={after[:16] or '-'}\t{detail}\n")
    with AUDIT.open("a", encoding="utf-8") as fh:
        fh.write(line)
    normalize_ownership(AUDIT)


def _telegram_env() -> dict[str, str]:
    """Telegram creds, from the process env or — failing that — runtime.env.

    The writer is invoked three ways: by the dashboard (a child of the entrypoint, so
    the env is there), by `docker exec` from apply-directive.sh, and by the analyst.
    A `docker exec` gets a FRESH shell that never sourced runtime.env, so both vars are
    empty and notify() returned silently — measured 2026-08-01: every refusal on the
    apply-directive.sh path was invisible to the operator, including the in-flight gate
    firing on a directive they believed had been applied. Read the file as a fallback so
    the alerting does not depend on which door the writer came through.
    """
    env = {k: os.environ.get(k, "") for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")}
    if all(env.values()):
        return env
    try:
        for line in open(APP / "logs" / "runtime.env", encoding="utf-8", errors="replace"):
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            k, _, v = line.strip().partition("=")
            if k in env and not env[k]:
                env[k] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return env


def notify(msg: str) -> None:
    env = _telegram_env()
    if not all(env.values()):
        return
    if not NOTIFY.exists():
        return
    try:
        subprocess.run(["bash", str(NOTIFY), msg], capture_output=True, timeout=25,
                       env={**os.environ, **env})
    except Exception:  # noqa: BLE001 — a failed notification must never fail a write
        pass


def _why_pending(live_text: str) -> str:
    """A compact 'why is the live one still PENDING' for the refusal notification.

    Operator feedback 2026-08-01: the refusal told them WHAT happened but not why the
    slot was occupied, so a directive they believed applied sat unexplained for 31h.
    The honest answer is the directive's OWN Completion clause — the conditions it set
    for itself — plus how long it has been waiting. Quoted, never paraphrased: a
    summary of a completion condition is how a gate gets softened by accident.
    """
    import re as _re
    from datetime import datetime as _dt, timezone as _tz

    age = ""
    m = _re.search(r"^##\s*Updated\s*\n+(\S+)", live_text, _re.MULTILINE)
    if m:
        try:
            then = _dt.fromisoformat(m.group(1).strip().replace("Z", "+00:00"))
            age = f" for {(_dt.now(_tz.utc) - then).total_seconds() / 3600:.1f}h"
        except ValueError:
            pass

    body = ""
    m2 = _re.search(r"^##\s*Completion\s*$(.+?)(?=^##\s|\Z)", live_text,
                    _re.MULTILINE | _re.DOTALL)
    if m2:
        body = " ".join(m2.group(1).split())
        if len(body) > 700:
            body = body[:700].rsplit(" ", 1)[0] + " …"
    return age, body


def backup(text: str, reason: str) -> Path | None:
    """Persist the about-to-be-destroyed content. Failure here BLOCKS the write.

    Ordered before the write on purpose: believing you have recoverability you do
    not have is worse than knowing you have none.
    """
    if not text:
        return None
    BACKUPS.mkdir(parents=True, exist_ok=True)
    p = BACKUPS / f"human-directive-{now().replace(':', '')}-{reason}.md"
    p.write_text(text, encoding="utf-8")
    if p.read_text(encoding="utf-8") != text:
        raise OSError(f"backup verify failed: {p}")
    normalize_ownership(p)
    return p


def normalize_ownership(p: Path) -> None:
    """Make the file readable by the loop/dashboard user regardless of invoker.

    The writer is exec'd through more than one identity: the dashboard runs it as
    `app`, but the operator's host-side channel reaches it via `docker exec`,
    whose default user is root on this image. mkstemp creates 0600 files owned by
    the invoker, and os.replace carries that onto the live slot — measured
    2026-07-29: a root-invoked write left human-directive.md root:root 0600, the
    app-uid loop could not even hash it, and the cockpit showed an empty PENDING.
    So after every write, chown to the memories directory's owner (the app user)
    and open the mode to 0644. chown needs root; when the invoker IS the app
    user the file is already right, so failure here is fine to ignore.

    TEMPORARY OWNERSHIP COMPATIBILITY (operator mandate, verbatim, 2026-07-29):

        The current `normalize_ownership()` behavior is a pre-isolation
        compatibility fix only. It MUST NOT preserve `app:app` ownership after
        OS isolation.

        During migration:

        - canonical directive, audit ledger, backups, and recovery artifacts
          must remain owned by the dedicated writer UID;
        - uid 10001 may receive read access only;
        - the protected parent directory must not permit uid 10001 to replace,
          rename, or unlink files;
        - a root-invoked operator write must preserve writer-UID ownership
          rather than converting protected files back to app ownership;
        - production acceptance tests must verify ownership and EPERM again
          after both an agent status transition and a host/root operator write.

    In other words: this function chowns to the *directory owner*, and today the
    memories directory is owned by `app`. When the isolation lands, the protected
    directory's owner becomes the writer UID — at that point this function must
    follow it (it already will, since it stats the parent), and any hardcoded
    notion of "app owns these files" would silently undo the isolation. Do not
    add one.
    """
    try:
        st = os.stat(DIRECTIVE.parent)
        os.chown(p, st.st_uid, st.st_gid)
    except (PermissionError, OSError):
        pass
    try:
        os.chmod(p, 0o644)
    except OSError:
        pass


def atomic_write(text: str) -> None:
    DIRECTIVE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(DIRECTIVE.parent), prefix=".hd-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        normalize_ownership(Path(tmp))
        os.replace(tmp, DIRECTIVE)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def verify_written(expected: str) -> str:
    back = DIRECTIVE.read_text(encoding="utf-8")
    if back != expected:
        raise OSError("read-back mismatch: the file on disk is not what was written")
    return sha(back)


class Refused(Exception):
    """A gate said no. Not an error — the point of the gate."""


# ---- body structure helpers (append / archive / show --sections) ------------

def live_body(text: str) -> str:
    """The directive body: everything after the '## Directive' line. '' if absent."""
    i = text.find(DIRECTIVE_MARK)
    return "" if i < 0 else text[i + len(DIRECTIVE_MARK):]


def split_body(body: str) -> tuple[str, list[tuple[str, str]]]:
    """(first_chunk, [(heading_line, section_text), ...]) split on '^## '.

    The first chunk is everything before the first '## ' line that follows the
    ANA DİREKTİF block. The directive's own preamble starts with '## Kaynak
    belgeler' and the main text with '# ANA DİREKTİF' / '## WOWCAR …' /
    '## Operatör açıklaması'; those three headings are treated as part of the
    first chunk so the main directive is never split or archived.
    """
    protected = ("## Kaynak belgeler", "## WOWCAR 2.0", "## Operatör açıklaması")
    first: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    for line in body.splitlines(keepends=True):
        if line.startswith("## ") and not line.startswith(protected):
            sections.append((line.rstrip("\n"), [line]))
        elif sections:
            sections[-1][1].append(line)
        else:
            first.append(line)
    return "".join(first), [(h, "".join(ls)) for h, ls in sections]


def section_sizes(body: str) -> list[tuple[int, str]]:
    first, secs = split_body(body)
    out = [(len(first.encode("utf-8")), "(ANA DİREKTİF + önsöz)")]
    out += [(len(t.encode("utf-8")), h) for h, t in secs]
    return out


def size_brake(body: str, actor: str, cmd: str, force: bool) -> None:
    """Warn above WARN_BYTES; refuse `append` above MAX_BYTES unless forced."""
    n = len(body.encode("utf-8"))
    if n <= WARN_BYTES:
        return
    top = sorted(section_sizes(body), reverse=True)[:5]
    top_s = "; ".join(f"{h[:60]} {b // 1024} KB" for b, h in top)
    if n > MAX_BYTES and cmd == "append" and not force:
        raise Refused(
            f"directive body would be {n // 1024} KB > DIRECTIVE_BODY_MAX_BYTES "
            f"{MAX_BYTES // 1024} KB. Archive closed sections first "
            f"(directive_writer.py archive) or pass --force-size. Largest: {top_s}")
    print(f"warn: directive body is {n // 1024} KB (> {WARN_BYTES // 1024} KB). "
          f"Largest sections: {top_s}. Use `archive` to collapse closed sections.",
          file=sys.stderr)
    notify(f"⚠️ Direktif gövdesi {n // 1024} KB ({cmd}, {actor}) — eşik {WARN_BYTES // 1024} KB. "
           f"En büyük bölümler: {top_s}. `directive_writer.py archive` ile küçült.")


def _pending_gate(args, live: str, live_sha: str, what: str) -> bool:
    """True when the write may proceed; prints/audits/notifies the refusal otherwise."""
    _, _, live_status = read_live()
    if live_status == "PENDING" and not args.allow_pending:
        print(f"refused: the live directive is PENDING — that is in-flight work.\n"
              f"         Pass --allow-pending to {what} it deliberately.", file=sys.stderr)
        audit(f"{what}-refused", args.actor, live_sha, "", "reason=in-flight-pending")
        _age, _completion = _why_pending(live)
        _msg = (f"🚧 Directive {what} NOT applied ({args.actor}).\n\n"
                f"REFUSED, nothing written — the live directive has been PENDING{_age}. "
                "This is the in-flight gate, not an error.\n\n")
        if _completion:
            _msg += f"WHY IT IS STILL PENDING — its own Completion clause:\n{_completion}\n\n"
        _msg += "To proceed deliberately: AC_ALLOW_PENDING=1 (apply-directive.sh) / --allow-pending."
        notify(_msg)
        return False
    return True


def _refuse_section_refs(body: str) -> bool:
    missing = undefined_section_refs(body)
    if not missing:
        return False
    refs = ", ".join(f"§{n}" for n in missing)
    print(f"refused: merged directive body references {refs} with no matching "
          f"'## §N' header (OPREQ-GOV-DIRECTIVE-BODY-001). Nothing was written.",
          file=sys.stderr)
    return True


def with_lock(fn):
    def wrapper(*a, **kw):
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        with LOCK.open("w") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            try:
                return fn(*a, **kw)
            finally:
                fcntl.flock(lk, fcntl.LOCK_UN)
    return wrapper


HEADER = (
    "# Human Directive\n\n"
    "<!-- Written by scripts/core/directive_writer.py — the only writer. Do NOT\n"
    "     hand-edit and do NOT let a model edit this file: the body is immutable\n"
    "     after acceptance, and PENDING->DONE goes through `directive_writer.py\n"
    "     status`, which compare-and-swaps on the body hash. -->\n\n"
)


@with_lock
def cmd_write(args) -> int:
    body = Path(args.body_file).read_text(encoding="utf-8").rstrip() + "\n"
    if not body.strip():
        print("refused: empty directive body", file=sys.stderr)
        return 2

    missing = undefined_section_refs(body)
    if missing:
        refs = ", ".join(f"§{n}" for n in missing)
        print(
            f"refused: directive body references {refs} but defines no matching "
            f"'## §{missing[0]}'-style header for {'it' if len(missing) == 1 else 'them'} "
            "anywhere in the body (OPREQ-GOV-DIRECTIVE-BODY-001). A referenced-but-"
            "undefined section makes any Completion clause that depends on it "
            "unsatisfiable and freezes the directive in PENDING with no exit — exactly "
            "what happened to revision 11. Add the missing section(s) or remove the "
            "reference(s), then retry. Nothing was written.",
            file=sys.stderr,
        )
        return 2

    live, live_sha, live_status = read_live()

    if live_status == "PENDING" and not args.allow_pending:
        print("refused: the live directive is PENDING — that is in-flight work.\n"
              "         Pass --allow-pending to overwrite it deliberately.",
              file=sys.stderr)
        audit("write-refused", args.actor, live_sha, "", "reason=in-flight-pending")
        _age, _completion = _why_pending(live)
        _msg = (
            f"🚧 Directive NOT applied ({args.actor}).\n\n"
            "Your new directive was REFUSED and nothing was written — the live "
            f"directive has been PENDING{_age} and is unchanged. This is the "
            "in-flight gate, not an error.\n\n"
        )
        if _completion:
            _msg += f"WHY IT IS STILL PENDING — its own Completion clause:\n{_completion}\n\n"
        _msg += (
            "To replace it deliberately:\n"
            "AC_ALLOW_PENDING=1 apply-directive.sh <file>\n\n"
            "Or close the live one first: directive_writer.py status (PENDING->DONE)."
        )
        notify(_msg)
        return 2

    size_brake(body, args.actor, "write", True)
    bk = backup(live, "preoverwrite")
    new = f"{HEADER}## Status\nPENDING\n\n## Updated\n{now()}\n\n## Directive\n{body}"
    atomic_write(new)
    new_sha = verify_written(new)
    audit("write", args.actor, live_sha, new_sha,
          f"backup={bk.name if bk else '-'} allow_pending={args.allow_pending}")
    print(f"ok: directive written, status=PENDING sha256={new_sha[:16]} "
          f"backup={bk.name if bk else '(none — no previous file)'}")
    return 0


@with_lock
def cmd_append(args) -> int:
    """Add ONE '## ' section to the live body; Status becomes PENDING."""
    section = Path(args.section_file).read_text(encoding="utf-8").strip("\n") + "\n"
    if not section.startswith("## "):
        print("error: section file must start with a '## ' heading (one section per append)",
              file=sys.stderr)
        return 3
    live, live_sha, live_status = read_live()
    if not live or DIRECTIVE_MARK not in live:
        print("refused: no live directive to append to — use `write` first", file=sys.stderr)
        return 2
    body = live_body(live).rstrip("\n") + "\n\n" + section
    if _refuse_section_refs(body):
        return 2
    if not _pending_gate(args, live, live_sha, "append"):
        return 2
    size_brake(body, args.actor, "append", args.force_size)
    bk = backup(live, "preappend")
    new = f"{HEADER}## Status\nPENDING\n\n## Updated\n{now()}\n\n## Directive\n{body}"
    atomic_write(new)
    new_sha = verify_written(new)
    heading = section.splitlines()[0][:80]
    audit("append", args.actor, live_sha, new_sha,
          f"backup={bk.name if bk else '-'} section={heading!r} "
          f"body_bytes={len(body.encode('utf-8'))} allow_pending={args.allow_pending}")
    print(f"ok: section appended, status=PENDING sha256={new_sha[:16]} "
          f"body_sha256={sha(body_of(new))} body_bytes={len(body.encode('utf-8'))} "
          f"backup={bk.name if bk else '-'}")
    return 0


@with_lock
def cmd_archive(args) -> int:
    """Move closed sections verbatim to the archive file; summary takes their place.

    Status is untouched (archiving is not work for the loop). The first chunk is
    never dropped; sections carrying OPREQ resolver lines only go when the
    summary repeats those lines.
    """
    summary = Path(args.summary_file).read_text(encoding="utf-8").strip("\n") + "\n"
    if not summary.startswith("## "):
        print("error: summary file must start with a '## ' heading", file=sys.stderr)
        return 3
    live, live_sha, live_status = read_live()
    if not live or DIRECTIVE_MARK not in live:
        print("refused: no live directive", file=sys.stderr)
        return 2
    first, secs = split_body(live_body(live))
    prefixes = tuple(args.drop_prefix)
    drop = [(h, t) for h, t in secs if h.startswith(prefixes)]
    if not drop:
        print("error: no section matches the given --drop-prefix values", file=sys.stderr)
        return 3
    summary_resolvers = set(l.strip() for l in summary.splitlines() if RESOLVER_LINE_RE.match(l))
    for h, t in drop:
        needed = [l.strip() for l in t.splitlines() if RESOLVER_LINE_RE.match(l)]
        missing = [l for l in needed if l not in summary_resolvers]
        if missing:
            print(f"refused: section {h[:70]!r} carries OPREQ resolver lines the summary "
                  f"does not repeat: {missing[0][:90]!r}. Dropping it would re-open the "
                  "OPREQ. Add the lines to the summary. Nothing written.", file=sys.stderr)
            return 2
    if not _pending_gate(args, live, live_sha, "archive"):
        return 2
    kept: list[str] = [first]
    inserted = False
    for h, t in secs:
        if (h, t) in drop:
            if not inserted:
                kept.append(summary.rstrip("\n") + "\n\n")
                inserted = True
            continue
        kept.append(t if t.endswith("\n") else t + "\n")
    body = "".join(kept).rstrip("\n") + "\n"
    if _refuse_section_refs(body):
        return 2
    bk = backup(live, "prearchive")
    stamp = now()
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with ARCHIVE.open("a", encoding="utf-8") as fh:
        for h, t in drop:
            fh.write(f"\n<!-- archived {stamp} from {live_sha[:16]} section_sha16={sha(t)[:16]} -->\n")
            fh.write(t.rstrip("\n") + "\n")
    normalize_ownership(ARCHIVE)
    status_line = STATUS_RE.search(live)
    status = status_line.group(1) if status_line else "PENDING"
    new = f"{HEADER}## Status\n{status}\n\n## Updated\n{stamp}\n\n## Directive\n{body}"
    atomic_write(new)
    new_sha = verify_written(new)
    before_b, after_b = len(live_body(live).encode("utf-8")), len(body.encode("utf-8"))
    audit("archive", args.actor, live_sha, new_sha,
          f"backup={bk.name if bk else '-'} dropped={len(drop)} bytes={before_b}->{after_b} "
          f"status={status} headings={'|'.join(h[:40] for h, _ in drop)!r}")
    size_brake(body, args.actor, "archive", True)
    print(f"ok: {len(drop)} section(s) archived to {ARCHIVE.name}, body {before_b}->{after_b} bytes, "
          f"status={status} sha256={new_sha[:16]} body_sha256={sha(body_of(new))}")
    return 0


@with_lock
def cmd_status(args) -> int:
    """Compare-and-swap the Status value. The body must be untouched."""
    live, live_sha, live_status = read_live()
    if not live:
        print("refused: no directive file", file=sys.stderr)
        return 2
    if live_status != args.expect_status:
        print(f"refused: status is {live_status!r}, expected {args.expect_status!r} — "
              "someone else moved it", file=sys.stderr)
        audit("status-refused", args.actor, live_sha, "",
              f"want_from={args.expect_status} found={live_status}")
        return 2
    got_body = sha(body_of(live))
    if got_body != args.expect_body_sha256:
        print(f"refused: body hash {got_body[:16]} != expected "
              f"{args.expect_body_sha256[:16]} — the directive changed under you.\n"
              "         The body is immutable after acceptance; nothing was written.",
              file=sys.stderr)
        audit("status-refused", args.actor, live_sha, "", "reason=body-hash-mismatch")
        notify("🚧 Directive status transition REFUSED: body hash mismatch — "
               "the directive changed mid-execution. Nothing written.")
        return 2

    bk = backup(live, f"status-{args.expect_status}-to-{args.to}")
    new = STATUS_RE.sub(f"## Status\n{args.to}", live, count=1)
    if body_of(new) != body_of(live):
        print("refused: transition would alter the body — refusing", file=sys.stderr)
        return 2
    atomic_write(new)
    new_sha = verify_written(new)
    receipt = args.receipt or "-"
    audit("status", args.actor, live_sha, new_sha,
          f"{args.expect_status}->{args.to} receipt={receipt} backup={bk.name if bk else '-'}")
    print(f"ok: status {args.expect_status} -> {args.to} sha256={new_sha[:16]}")
    return 0


@with_lock
def cmd_restore(args) -> int:
    """The analyst path: put a snapshot back ONLY if nothing else has written.

    Backing up first would make a clobber recoverable; this refuses to clobber.
    If the live file moved since the snapshot was taken, the snapshot is stale by
    definition — someone with more right to the slot wrote it — so the restore
    candidate goes to a recovery file and the live file is left alone.
    """
    snap = Path(args.from_file).read_text(encoding="utf-8")
    live, live_sha, live_status = read_live()

    if live_sha == sha(snap):
        print("ok: live file identical to snapshot, nothing to restore")
        return 0

    if live_sha != args.expect_sha256:
        RECOVERY.mkdir(parents=True, exist_ok=True)
        cand = RECOVERY / f"restore-candidate-{now().replace(':', '')}.md"
        cand.write_text(snap, encoding="utf-8")
        print("refused: the live directive changed since the snapshot was taken "
              f"(live {live_sha[:16]}, expected {args.expect_sha256[:16]}).\n"
              f"         Someone else wrote it — status={live_status or 'unknown'}. "
              "Live file untouched.\n"
              f"         Restore candidate saved: {cand}", file=sys.stderr)
        audit("restore-refused", args.actor, live_sha, "",
              f"expected={args.expect_sha256[:16]} candidate={cand.name} live_status={live_status}")
        notify("🚧 Analyst restore REFUSED — the directive was written by someone else "
               f"during the analyst run (status={live_status or 'unknown'}). Live file "
               f"untouched; candidate kept at {cand.name}.")
        return 2

    bk = backup(live, "prerestore")
    atomic_write(snap)
    new_sha = verify_written(snap)
    audit("restore", args.actor, live_sha, new_sha, f"backup={bk.name if bk else '-'}")
    print(f"ok: snapshot restored sha256={new_sha[:16]}")
    return 0


def cmd_show(args) -> int:
    live, live_sha, live_status = read_live()
    print(f"status={live_status or '(none)'}")
    print(f"file_sha256={live_sha or '(none)'}")
    print(f"body_sha256={sha(body_of(live)) if live else '(none)'}")
    if live:
        body = live_body(live)
        print(f"body_bytes={len(body.encode('utf-8'))}")
        if getattr(args, "sections", False):
            for b, h in section_sizes(body):
                print(f"{b:7d}  {h}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--actor", default=os.environ.get("AC_ACTOR", "unknown"))
    sub = ap.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("write"); w.set_defaults(fn=cmd_write)
    w.add_argument("--body-file", required=True)
    w.add_argument("--allow-pending", action="store_true")

    a = sub.add_parser("append"); a.set_defaults(fn=cmd_append)
    a.add_argument("--section-file", required=True)
    a.add_argument("--allow-pending", action="store_true")
    a.add_argument("--force-size", action="store_true")

    ar = sub.add_parser("archive"); ar.set_defaults(fn=cmd_archive)
    ar.add_argument("--drop-prefix", action="append", required=True)
    ar.add_argument("--summary-file", required=True)
    ar.add_argument("--allow-pending", action="store_true")

    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    s.add_argument("--expect-status", required=True)
    s.add_argument("--to", required=True)
    s.add_argument("--expect-body-sha256", required=True)
    s.add_argument("--receipt")

    r = sub.add_parser("restore"); r.set_defaults(fn=cmd_restore)
    r.add_argument("--from-file", required=True)
    r.add_argument("--expect-sha256", required=True)

    sh = sub.add_parser("show"); sh.set_defaults(fn=cmd_show)
    sh.add_argument("--sections", action="store_true", help="heading + byte table of the body")

    # baseline / reconcile are NOT operations of this protocol, by design
    # (operator mandate, 2026-07-29): the agent must never be able to bless a
    # hash mismatch it may itself have caused. Reconciliation and baselining
    # happen ONLY through the operator's host-side channel
    # (autocompany-deploy/scripts/directive-baseline.sh), outside the container.
    # Registering them here as hard refusals makes the boundary explicit instead
    # of an argparse "invalid choice" that reads like a missing feature.
    def _refuse_forbidden(name: str):
        def fn(_args) -> int:
            raise Refused(
                f"'{name}' is not an operation of this writer and never will be: "
                "baselining/reconciling the audit ledger is operator-only, via the "
                "host-side directive-baseline.sh channel outside the container")
        return fn

    for _forbidden in ("baseline", "reconcile"):
        sub.add_parser(_forbidden).set_defaults(fn=_refuse_forbidden(_forbidden))

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
