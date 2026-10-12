#!/usr/bin/env python3
"""consensus-prune.py v2.1 — mechanical archive of per-cycle narrative in consensus.md.

v2.1 (2026-10-12, prod 2026-10-11 fixture showed three leaks):
  * Prior shapes: a paragraph whose first line starts `(Prior` or `**(Prior)` is an
    entry when, after the `**`/`(Prior...)` prefix, the line carries `Cycle N`
    (`(Prior, Cycle N) **Cycle N ...`, `(Prior) **Cycle N ...`, `**(Prior) Cycle N ...`);
    or when the line is only the prefix and the next line starts `**Cycle N`
    (`(Prior, Cycle N queue)` + `**Cycle N`; N from the second line); or when it is a
    single-line paragraph with `Cycle N` inside the parens. A bare `(Prior)` stays a
    non-entry. PARA_RE itself is unchanged (`**CORRECTED Cycle N` remains a non-entry).
  * Duplicate cycle numbers no longer skip a section: entries are deduped on (n, line)
    and archived in (n, line) order — both copies go.
  * EC pass for `## Execution Controls`: each top-level `- ` bullet (with its indented /
    lazy continuation lines) is one entry, keyed by the first `Cycle N` on its FIRST line.
    Bullets with no cycle number there (Program State, External Actions, Standing rules,
    Context7, Linear, ...) are pinned and never archived; numbered bullets go smallest-N
    first until the section is under CAP_EC (default 6144). No keep-one floor (pinned
    bullets remain). If pinned bullets alone exceed the cap the section stays over it.
    Kill switch CONSENSUS_PRUNE_EC=0.

Why (2026-10-08, v1). The [PROMPT-SIZE] brake in auto-loop.sh fired on EVERY cycle from
2026-09-04 on: consensus.md had grown to 127 KB, the brake dropped it from the inline
prompt and told the model to "prune stale material into docs/" — a ritual no cycle ever
performed. This script is that ritual as a harness mechanism (loop-brake-design:
intent != mechanism; fail-closed for data, fail-open for the loop, never silent).

Why v2 (2026-10-09, three-reviewer spec). v1 only pruned "What We Did" bullets. Within a
day the model moved its per-cycle diary elsewhere: `**Cycle N` paragraphs under Next
Action / Current Phase / Company State, trailing `## Cycle N` top-level sections, and
duplicate copies of canonical headers at the top of the file (296 KB total). v2 keeps
v1's safety core and adds section-level and paragraph-level pruning:

  1. The file is split at top-level `^## ` lines. The preamble (everything before the
     first section, i.e. the `# Auto Company Consensus` title) is never touched.
  2. The PRIMARY BLOCK is the byte-largest run of consecutive sections that are all
     CANONICAL (exact-text header allowlist) and pairwise distinct. Everything outside
     it — duplicate canonical copies, `## Cycle N`, `## Execution Controls (Cycle N)`,
     `## Last Updated (Cycle N)` — is archivable as a whole section (header included,
     byte-exact). Exception: the KEEP_TAIL largest-numbered ones (first `\\d+` in the
     header) stay in place; unnumbered ones never stay. (TAIL pass)
  3. Inside the primary block, Next Action / Current Phase / Company State paragraphs
     starting `**Cycle N` and "What We Did" bullets `- **Cycle N` are entries. Entries
     are archived from the SMALLEST cycle number up until the section is under its byte
     cap (CAP_NA/CP/CS/WWD); at least one entry always remains; What We Did additionally
     keeps at most KEEP (v1). Non-entry paragraphs/lines stay in place, same order, same
     bytes. A duplicate cycle number or a code fence inside an entry skips THAT section
     only. (NA / CP / CS / WWD passes)
  4. Key Decisions Made is never touched; its size is reported.
  5. Data safety: every removed block is recorded as (offset, length); before writing,
     rebuild(stripped, blocks) must equal the original bytes or the run is skipped. The
     archive (docs/operations/consensus-archive-YYYY-MM.md) is appended and sha-verified
     BEFORE consensus is rewritten atomically; a block whose sha is already there is not
     appended twice; consensus is re-hashed right before the write. On any skip the guard
     state (pre_sha16/post_sha16/post_metrics) is NOT updated.
  6. Visibility: one log line per run; `insufficient` tag when the result is still over
     80 KB; a skip-streak alarm line (3 consecutive skips while over threshold) that the
     harness forwards to Telegram; a bloat warning when one section grew >10 KB across
     3 runs or a new kind of non-canonical header appears outside the primary block.
     `--dry-run` prints a per-section before/after byte table and writes nothing.

Runs only when the file is >= CONSENSUS_PRUNE_MIN_BYTES (default 70000). Env (process env,
overridden by logs/runtime.env for every CONSENSUS_PRUNE_* key — live, no redeploy):
  CONSENSUS_PRUNE_ENABLED=0                 global kill switch
  CONSENSUS_PRUNE_TAIL|NA|CP|CS|WWD|EC=0    per-pass kill switches
  CONSENSUS_PRUNE_CAP_NA=8192 CAP_CP=6144 CAP_CS=6144 CAP_WWD=8192 CAP_EC=6144   section byte caps
  CONSENSUS_PRUNE_KEEP=8 (What We Did secondary bound)  CONSENSUS_PRUNE_KEEP_TAIL=2
  CONSENSUS_PRUNE_MIN_BYTES=70000  CONSENSUS_PRUNE_SKIP_ALARM=3
Exit code is always 0 (informational helper; the loop never fails over it).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

STATE_REL = "logs/consensus-prune.json"
CONSENSUS_REL = "memories/consensus.md"
ARCHIVE_DIR_REL = "docs/operations"

CANONICAL = (
    "## Last Updated", "## Current Phase", "## What We Did This Cycle", "## Key Decisions Made",
    "## Execution Controls", "## Active Projects", "## Awaiting Operator", "## WTP Evidence",
    "## Next Action", "## Company State", "## Open Questions",
)
H_WWD = "## What We Did This Cycle"
H_NA = "## Next Action"
H_CP = "## Current Phase"
H_CS = "## Company State"
H_KD = "## Key Decisions Made"
H_EC = "## Execution Controls"
CYCLE_NUM_RE = re.compile(r"Cycle\s+(\d+)")
# v2.1 prefix: optional `**`, then `(Prior...)`, then optional whitespace/`**`.
PRIOR_LEAD_RE = re.compile(r"^(?:\*\*)?\(Prior\b[^)]*\)\s*(?:\*\*)?")

ENTRY_RE = re.compile(r"^- \*\*Cycle\s+(\d+)")        # What We Did bullet entry
PARA_RE = re.compile(r"^\*\*Cycle\s+(\d+)")           # paragraph entry (NA/CP/CS)
TOP_BULLET_RE = re.compile(r"^- ")
HEADER_NUM_RE = re.compile(r"\d+")
FENCE = "```"
# Prefix-only on purpose (2026-10-08, first prod week): the model wrote its own multi-line
# archive note and the strict `..._$` form refused the whole section for 24 cycles. Any
# line starting like an archive note — ours or the model's — is a note; its continuation
# lines are dropped with it and ONE fresh note is written back.
NOTE_RE = re.compile(r"^- _Archive note \(cycle \d+\):")
REQUIRED = ("# Auto Company Consensus", "## Next Action", "## Company State")
# Mirror of ledger-guard.INCIDENT_RE — the note must NOT match it (tested).
INCIDENT_WORDS_RE = re.compile(
    r"incident|restored|restore|inadvertent|geri getir|kay[ıi]p|lost|erased|truncat|overwr|reconstruct|prune|compacted",
    re.IGNORECASE,
)
INSUFFICIENT_BYTES = 80000
HISTORY_RUNS = 4
BLOAT_BYTES = 10 * 1024

_RUNTIME_ENV: dict = {}


def _load_runtime_env(app: Path) -> None:
    """logs/runtime.env is the operator's live override file (same idiom as
    IDLE_SKIP_ENABLED in auto-loop.sh): a key there beats the process env, so caps /
    switches can be tuned without a redeploy. Flat KEY=VALUE lines only."""
    try:
        for ln in (app / "logs/runtime.env").read_text(encoding="utf-8", errors="replace").splitlines():
            ln = ln.strip()
            if ln.startswith("CONSENSUS_PRUNE_") and "=" in ln:
                k, v = ln.split("=", 1)
                _RUNTIME_ENV[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass


def _env_int(name: str, default: int) -> int:
    try:
        v = int((_RUNTIME_ENV.get(name) or os.environ.get(name, "")).strip())
        return v if v > 0 else default
    except (ValueError, TypeError):
        return default


def _env_flag(name: str, default: str) -> str:
    return (_RUNTIME_ENV.get(name) or os.environ.get(name, default)).strip()


def _app(arg: str | None) -> Path:
    return Path(arg).resolve() if arg else Path(__file__).resolve().parents[2]


def _sha16(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def _load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(path: Path, state: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        pass


class Skip(Exception):
    pass


# ----------------------------------------------------------------------------- model
class Section:
    """One top-level `## ` section: header line index `start`, exclusive end `end`."""

    def __init__(self, header: str, start: int, end: int, nbytes: int):
        self.header = header
        self.start = start
        self.end = end
        self.bytes = nbytes
        self.canonical = header in CANONICAL
        m = HEADER_NUM_RE.search(header)
        self.number = int(m.group(0)) if m else None
        self.primary = False

    @property
    def kind(self) -> str:
        return HEADER_NUM_RE.sub("N", self.header)


class Removal:
    """A contiguous line range [a, b) removed from the file; archived unless `archive` is
    False (dropped archive notes are rebuilt-checked but not archived)."""

    def __init__(self, a: int, b: int, pass_name: str, section: str, cycle: int | None, archive: bool = True):
        self.a, self.b = a, b
        self.pass_name = pass_name
        self.section = section
        self.cycle = cycle
        self.archive = archive


def _split_sections(lines: list[str]) -> tuple[int, list[Section]]:
    """Return (first_section_line, sections). Lines before the first `## ` are preamble."""
    heads = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
    secs: list[Section] = []
    for k, i in enumerate(heads):
        j = heads[k + 1] if k + 1 < len(heads) else len(lines)
        nbytes = sum(len(l.encode("utf-8")) for l in lines[i:j])
        secs.append(Section(lines[i].rstrip("\r\n"), i, j, nbytes))
    return (heads[0] if heads else len(lines)), secs


def _mark_primary(secs: list[Section]) -> list[Section]:
    """Byte-largest run of consecutive, canonical, pairwise-distinct sections."""
    best: list[Section] = []
    run: list[Section] = []
    seen: set[str] = set()

    def flush():
        nonlocal best
        if sum(s.bytes for s in run) > sum(s.bytes for s in best):
            best = list(run)

    for s in secs:
        if s.canonical and s.header not in seen:
            run.append(s); seen.add(s.header)
            continue
        flush(); run, seen = [], set()
        if s.canonical:
            run.append(s); seen.add(s.header)
    flush()
    for s in best:
        s.primary = True
    return best


# ----------------------------------------------------------------------------- passes
def _tail_pass(secs: list[Section], keep_tail: int) -> list[Removal]:
    others = [s for s in secs if not s.primary]
    numbered = sorted((s for s in others if s.number is not None), key=lambda s: s.number, reverse=True)
    stay = {id(s) for s in numbered[:keep_tail]}
    return [Removal(s.start, s.end, "tail", s.header, s.number) for s in others if id(s) not in stay]


def _entries_wwd(lines: list[str], sec: Section) -> tuple[list[tuple[int, int, int]], list[Removal]]:
    """What We Did (v1 shape): entries = `- **Cycle N` bullets + continuation lines; any
    other top-level bullet = unknown shape = Skip; old archive notes are dropped."""
    entries: list[tuple[int, int, int]] = []  # (cycle, a, b)
    drops: list[Removal] = []
    cur_a = None; cur_n = None
    note_a = None
    i = sec.start + 1
    while i < sec.end:
        ln = lines[i]
        m = ENTRY_RE.match(ln)
        if m:
            if cur_a is not None:
                entries.append((cur_n, cur_a, i))
            if note_a is not None:
                drops.append(Removal(note_a, i, "wwd", sec.header, None, archive=False)); note_a = None
            cur_n, cur_a = int(m.group(1)), i
        elif NOTE_RE.match(ln):
            if cur_a is not None:
                entries.append((cur_n, cur_a, i)); cur_a = None
            if note_a is not None:
                drops.append(Removal(note_a, i, "wwd", sec.header, None, archive=False))
            note_a = i
        elif TOP_BULLET_RE.match(ln):
            raise Skip(f"unrecognised top-level bullet: {ln.strip()[:60]!r}")
        elif note_a is not None and ln.strip() == "":
            drops.append(Removal(note_a, i, "wwd", sec.header, None, archive=False)); note_a = None
        i += 1
    if cur_a is not None:
        entries.append((cur_n, cur_a, sec.end))
    if note_a is not None:
        drops.append(Removal(note_a, sec.end, "wwd", sec.header, None, archive=False))
    return entries, drops


def _entries_para(lines: list[str], sec: Section) -> list[tuple[int, int, int]]:
    """Paragraph sections: a paragraph is a run of non-blank lines; an entry starts with
    `**Cycle N` (so `**CORRECTED Cycle N` is not one). The removable block is the
    paragraph plus the blank lines that follow it, so the neighbours keep their spacing."""
    entries: list[tuple[int, int, int]] = []
    i = sec.start + 1
    while i < sec.end:
        if lines[i].strip() == "":
            i += 1; continue
        a = i
        while i < sec.end and lines[i].strip() != "":
            i += 1
        while i < sec.end and lines[i].strip() == "":
            i += 1
        m = PARA_RE.match(lines[a])
        if m:
            entries.append((int(m.group(1)), a, i))
            continue
        first = lines[a]
        if not (first.startswith("(Prior") or first.startswith("**(Prior)")):
            continue
        pm = PRIOR_LEAD_RE.match(first)
        if pm is None:  # `(Prior` without a closing paren on the line: not a known shape
            continue
        rest = first[pm.end():]
        m1 = CYCLE_NUM_RE.search(rest)          # `(Prior) **Cycle N`, `**(Prior) Cycle N`
        nonblank = [k for k in range(a, i) if lines[k].strip() != ""]
        if m1:
            entries.append((int(m1.group(1)), a, i))
        elif rest.strip() == "" and len(nonblank) >= 2 and PARA_RE.match(lines[a + 1]):
            entries.append((int(PARA_RE.match(lines[a + 1]).group(1)), a, i))   # lead-in line
        elif len(nonblank) == 1:
            m3 = CYCLE_NUM_RE.search(pm.group(0))  # single line, N inside the parens
            if m3:
                entries.append((int(m3.group(1)), a, i))
    return entries


def _entries_bullets(lines: list[str], sec: Section) -> list[tuple[int, int, int]]:
    """Execution Controls: each top-level `- ` bullet plus its continuation lines (indented
    lines, lazy non-bullet lines, blank lines followed by more indented text) is one block.
    Only bullets whose FIRST line carries `Cycle N` are entries; the rest are pinned.
    Trailing blank lines are not part of the block."""
    entries: list[tuple[int, int, int]] = []
    i = sec.start + 1
    while i < sec.end:
        if not TOP_BULLET_RE.match(lines[i]):
            i += 1; continue
        a = i
        last = i
        i += 1
        while i < sec.end and not TOP_BULLET_RE.match(lines[i]):
            ln = lines[i]
            if ln.strip() == "":
                i += 1; continue
            if ln[:1] in (" ", "\t") or i == last + 1:
                last = i; i += 1; continue
            break  # column-0 text after a blank line: a separate, pinned paragraph
        i = last + 1
        m = CYCLE_NUM_RE.search(lines[a])
        if m:
            entries.append((int(m.group(1)), a, last + 1))
    return entries


def _select(lines: list[str], sec: Section, entries: list[tuple[int, int, int]],
            cap: int, keep: int | None, pass_name: str, floor: int = 1) -> list[Removal]:
    """Archive from the smallest cycle number until the section is under `cap` bytes
    (then under `keep` entries if given). At least `floor` entries always remain.
    v2.1: duplicate cycle numbers no longer skip; dedupe on (n, a), order by (n, a)."""
    entries = sorted(set(entries), key=lambda e: (e[0], e[1]))
    for _, a, b in entries:
        if any(FENCE in l for l in lines[a:b]):
            raise Skip(f"{pass_name}: code fence inside an entry")
    size = sec.bytes
    remaining = len(entries)
    gone: list[Removal] = []
    for n, a, b in entries:
        if remaining <= floor:
            break
        over_cap = size > cap
        over_keep = keep is not None and remaining > keep
        if not (over_cap or over_keep):
            break
        size -= sum(len(l.encode("utf-8")) for l in lines[a:b])
        remaining -= 1
        gone.append(Removal(a, b, pass_name, sec.header, n))
    return gone


# ----------------------------------------------------------------------------- rebuild
def _line_offsets(lines: list[str]) -> list[int]:
    offs = [0]
    for l in lines:
        offs.append(offs[-1] + len(l.encode("utf-8")))
    return offs


def _strip_and_blocks(data: bytes, lines: list[str], removals: list[Removal]) -> tuple[bytes, list[tuple[int, bytes]]]:
    """Return (stripped_bytes, [(offset, bytes)]) and assert the removals do not overlap."""
    offs = _line_offsets(lines)
    rs = sorted(removals, key=lambda r: r.a)
    blocks: list[tuple[int, bytes]] = []
    out = bytearray()
    pos = 0
    for r in rs:
        oa, ob = offs[r.a], offs[r.b]
        if oa < pos:
            raise Skip("overlapping removals")
        out += data[pos:oa]
        blocks.append((oa, data[oa:ob]))
        pos = ob
    out += data[pos:]
    return bytes(out), blocks


def _rebuild(stripped: bytes, blocks: list[tuple[int, bytes]]) -> bytes:
    """Inverse of _strip_and_blocks: re-insert every block at its ORIGINAL offset."""
    out = bytearray(); pos = 0; spos = 0
    for off, blk in blocks:  # ascending original offsets
        take = off - pos
        out += stripped[spos:spos + take]; spos += take
        out += blk
        pos = off + len(blk)
    out += stripped[spos:]
    return bytes(out)


# ----------------------------------------------------------------------------- main
def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycle", type=int, required=True)
    ap.add_argument("--app", default=None)
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    app = _app(args.app)
    _load_runtime_env(app)
    if _env_flag("CONSENSUS_PRUNE_ENABLED", "1") == "0":
        return 0

    keep = _env_int("CONSENSUS_PRUNE_KEEP", 8)
    keep_tail = _env_int("CONSENSUS_PRUNE_KEEP_TAIL", 2)
    caps = {
        "na": _env_int("CONSENSUS_PRUNE_CAP_NA", 8192),
        "cp": _env_int("CONSENSUS_PRUNE_CAP_CP", 6144),
        "cs": _env_int("CONSENSUS_PRUNE_CAP_CS", 6144),
        "wwd": _env_int("CONSENSUS_PRUNE_CAP_WWD", 8192),
        "ec": _env_int("CONSENSUS_PRUNE_CAP_EC", 6144),
    }
    on = {k: _env_flag(f"CONSENSUS_PRUNE_{k.upper()}", "1") != "0"
          for k in ("tail", "na", "cp", "cs", "wwd", "ec")}
    min_bytes = _env_int("CONSENSUS_PRUNE_MIN_BYTES", 70000)
    skip_alarm = _env_int("CONSENSUS_PRUNE_SKIP_ALARM", 3)
    cpath = app / CONSENSUS_REL
    spath = app / STATE_REL
    state = _load_state(spath)
    streak = int(state.get("skipped_streak", 0) or 0)

    def finish_skip(reason: str, over: bool) -> int:
        # Guard-facing keys (pre_sha16/post_sha16/post_metrics) are never touched here.
        nonlocal streak
        streak = streak + 1 if over else 0
        if not args.dry_run:
            state["skipped_streak"] = streak
            state["last_cycle"] = args.cycle
            state["last_skip_reason"] = reason
            _save_state(spath, state)
        if over and streak >= skip_alarm:
            sys.stdout.write(
                f"⚠ CONSENSUS-PRUNE — Cycle #{args.cycle}: {streak} ardışık atlama ({reason}); "
                f"consensus.md eşik üstünde kalıyor, [PROMPT-SIZE] freni kapanmıyor. "
                f"Elle bak: scripts/ops/consensus-prune.py --dry-run.\n")
        elif over:
            sys.stdout.write(f"[CONSENSUS-PRUNE] skipped: {reason} (streak {streak})\n")
        return 0

    try:
        data = cpath.read_bytes()
    except Exception as e:
        return finish_skip(f"cannot read consensus: {e.__class__.__name__}", True)
    over = len(data) >= min_bytes
    if not over:
        if streak and not args.dry_run:
            state["skipped_streak"] = 0
            _save_state(spath, state)
        return 0

    try:
        text = data.decode("utf-8")  # strict on purpose
    except UnicodeDecodeError:
        return finish_skip("consensus is not valid UTF-8", over)

    lines = text.splitlines(keepends=True)
    _, secs = _split_sections(lines)
    primary = _mark_primary(secs)
    if not primary:
        return finish_skip("no canonical section found", over)
    by_header = {s.header: s for s in primary}

    removals: list[Removal] = []
    skips: list[str] = []
    moved = {"tail": 0, "na": 0, "cp": 0, "cs": 0, "wwd": 0, "ec": 0}
    wwd_gone: list[Removal] = []

    if on["tail"]:
        r = _tail_pass(secs, keep_tail)
        removals += r; moved["tail"] = len(r)

    for key, header, parser in (("na", H_NA, _entries_para), ("cp", H_CP, _entries_para),
                                ("cs", H_CS, _entries_para), ("wwd", H_WWD, None),
                                ("ec", H_EC, _entries_bullets)):
        if not on[key]:
            continue
        sec = by_header.get(header)
        if sec is None:
            # What We Did is mandatory every cycle (v1 contract): missing = skip reason.
            # The paragraph sections are optional carriers of diary text: missing = 0 moved.
            if key == "wwd":
                skips.append("wwd: section not in primary block")
            continue
        try:
            if key == "wwd":
                entries, drops = _entries_wwd(lines, sec)
                gone = _select(lines, sec, entries, caps[key], keep, key)
                if gone:
                    removals += gone + drops
                    wwd_gone = gone
            else:
                entries = parser(lines, sec)
                gone = _select(lines, sec, entries, caps[key], None, key,
                               floor=0 if key == "ec" else 1)
                removals += gone
            moved[key] = len(gone)
        except Skip as ex:
            skips.append(str(ex))

    # per-section before/after sizes (for the table, the log line and the bloat history)
    removed_lines = set()
    for r in removals:
        removed_lines.update(range(r.a, r.b))
    offs = _line_offsets(lines)

    def after_bytes(s: Section) -> int:
        return sum(offs[i + 1] - offs[i] for i in range(s.start, s.end) if i not in removed_lines)

    first_primary = primary[0].start
    last_primary = primary[-1].end
    head_after = sum(after_bytes(s) for s in secs if not s.primary and s.start < first_primary)
    tail_after = sum(after_bytes(s) for s in secs if not s.primary and s.start >= last_primary)
    sizes = {
        "wwd": after_bytes(by_header[H_WWD]) if H_WWD in by_header else 0,
        "na": after_bytes(by_header[H_NA]) if H_NA in by_header else 0,
        "cp": after_bytes(by_header[H_CP]) if H_CP in by_header else 0,
        "cs": after_bytes(by_header[H_CS]) if H_CS in by_header else 0,
        "kd": after_bytes(by_header[H_KD]) if H_KD in by_header else 0,
        "ec": after_bytes(by_header[H_EC]) if H_EC in by_header else 0,
        "tail": tail_after, "head": head_after,
    }
    kinds_now = sorted({s.kind for s in secs if not s.primary})

    def record_history() -> list[str]:
        """Append this run's sizes to the state history; return bloat warnings."""
        hist = state.get("section_history") or []
        hist = (hist + [sizes])[-HISTORY_RUNS:]
        warns = []
        if len(hist) >= 3:
            base = hist[-3]
            for k, v in sizes.items():
                if k not in base:  # key added in a later version (v2.1 "ec"): no baseline yet
                    continue
                if v - int(base.get(k, 0) or 0) > BLOAT_BYTES:
                    warns.append(f"{k} +{(v - int(base.get(k, 0) or 0)) // 1024}KB in 3 runs")
        prev_kinds = state.get("noncanonical_kinds")
        if prev_kinds is not None:
            new_kinds = [k for k in kinds_now if k not in prev_kinds]
            if new_kinds:
                warns.append("new non-canonical header(s) outside primary block: " + ", ".join(new_kinds))
        state["section_history"] = hist
        state["noncanonical_kinds"] = kinds_now
        return warns

    def emit_warns(warns: list[str]) -> None:
        if warns:
            sys.stdout.write(f"⚠ CONSENSUS-PRUNE — yeni şişme yeri: " + "; ".join(warns) + "\n")

    if args.dry_run:
        sys.stdout.write(f"{'section':44s} {'before':>8s} {'after':>8s}\n")
        for s in secs:
            tag = "" if s.primary else "  [outside primary]"
            sys.stdout.write(f"{s.header[:44]:44s} {s.bytes:8d} {after_bytes(s):8d}{tag}\n")

    if not removals:
        if skips:
            return finish_skip("; ".join(skips), over)
        warns = record_history()
        if not args.dry_run:
            state["skipped_streak"] = 0
            state["last_cycle"] = args.cycle
            _save_state(spath, state)
        sys.stdout.write(f"[CONSENSUS-PRUNE] insufficient: nothing to archive, file still {len(data)//1024}KB "
                         f"(wwd={sizes['wwd']//1024}KB na={sizes['na']//1024}KB cp={sizes['cp']//1024}KB "
                         f"cs={sizes['cs']//1024}KB kd={sizes['kd']//1024}KB ec={sizes['ec']//1024}KB tail={sizes['tail']//1024}KB "
                         f"head={sizes['head']//1024}KB){' [dry-run]' if args.dry_run else ''}\n")
        emit_warns(warns)
        return 0

    try:
        stripped, blocks = _strip_and_blocks(data, lines, removals)
        if _rebuild(stripped, blocks) != data:
            raise Skip("rebuild invariant failed")
    except Skip as ex:
        return finish_skip(str(ex), over)

    # Archive blocks: one per removed SECTION (tail pass, header included, byte-exact) and
    # one per pruned section's ENTRIES (removed paragraphs/bullets concatenated in file order).
    now = _dt.datetime.now(_dt.timezone.utc)
    apath = app / ARCHIVE_DIR_REL / f"consensus-archive-{now:%Y-%m}.md"
    arel = f"{ARCHIVE_DIR_REL}/{apath.name}"
    groups: dict[tuple, list[Removal]] = {}
    for r in sorted(removals, key=lambda r: r.a):
        if r.archive:
            key = (r.pass_name, r.section, r.a if r.pass_name == "tail" else 0)
            groups.setdefault(key, []).append(r)
    archive_blocks: list[tuple[str, str]] = []  # (header, body)
    for (pass_name, section, _), rs in groups.items():
        body = "".join("".join(lines[r.a:r.b]) for r in rs)
        if not body.endswith("\n"):
            body += "\n"
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        nums = [r.cycle for r in rs if r.cycle is not None]
        cyc = f"cycles {min(nums)}..{max(nums)}" if nums else "cycles n/a"
        kind = "section" if pass_name == "tail" else "entries"
        header = (f"\n## Archived at cycle {args.cycle} ({now:%Y-%m-%dT%H:%M:%SZ}) — {kind} — "
                  f"{section[3:]} — {cyc} — {len(rs)} blocks — sha256:{sha}\n\n")
        archive_blocks.append((header, body))

    new_text = stripped.decode("utf-8")
    if wwd_gone:
        nums = [r.cycle for r in wwd_gone]
        note = (f"- _Archive note (cycle {args.cycle}): {len(wwd_gone)} older entries (cycles {min(nums)}..{max(nums)}) "
                f"moved to {arel}. Not for routine reading — grep by cycle number only._\n")
        assert not INCIDENT_WORDS_RE.search(note), "archive note must not match INCIDENT_RE"
        nl = new_text.splitlines(keepends=True)
        # Removals are whole-line ranges, so the primary header's index in the stripped
        # file is its original index minus the removed lines that preceded it.
        wi = by_header[H_WWD].start - sum(1 for i in removed_lines if i < by_header[H_WWD].start)
        assert nl[wi].rstrip("\r\n") == H_WWD
        we = next((j for j in range(wi + 1, len(nl)) if nl[j].startswith("## ")), len(nl))
        body = nl[wi + 1:we]
        if body and not body[-1].endswith("\n"):
            body[-1] += "\n"
        if body and body[-1].strip() != "":
            body.append("\n")
        body += [note, "\n"]
        nl = nl[:wi + 1] + body + nl[we:]
        new_text = "".join(nl)
    for req in REQUIRED:
        if req not in new_text:
            return finish_skip(f"result would lose required marker {req!r}", over)
    new_data = new_text.encode("utf-8")

    tail_kb = sum(offs[r.b] - offs[r.a] for r in removals if r.pass_name == "tail") // 1024
    summary = (f"[CONSENSUS-PRUNE] cycle {args.cycle}: moved tail={moved['tail']} sections ({tail_kb}KB), "
               f"na={moved['na']} paras, cp={moved['cp']}, cs={moved['cs']}, wwd={moved['wwd']}, ec={moved['ec']}; "
               f"before={len(data)//1024}KB after={len(new_data)//1024}KB; sections: "
               f"wwd={sizes['wwd']//1024}KB na={sizes['na']//1024}KB cp={sizes['cp']//1024}KB "
               f"cs={sizes['cs']//1024}KB kd={sizes['kd']//1024}KB ec={sizes['ec']//1024}KB tail={sizes['tail']//1024}KB "
               f"head={sizes['head']//1024}KB; archive {arel}")
    if skips:
        summary += "; skipped: " + "; ".join(skips)
    if len(new_data) > INSUFFICIENT_BYTES:
        summary += " insufficient: still >80KB after archive"
    if args.dry_run:
        sys.stdout.write(f"{'TOTAL':44s} {len(data):8d} {len(new_data):8d}\n")
        sys.stdout.write(summary + " [dry-run]\n")
        emit_warns(record_history())
        return 0

    # 1) archive first, verified, idempotent per block
    try:
        apath.parent.mkdir(parents=True, exist_ok=True)
        existing = apath.read_bytes() if apath.is_file() else b""
        with open(apath, "ab") as fh:
            for header, body in archive_blocks:
                sha = header.rsplit("sha256:", 1)[1].strip()
                if f"sha256:{sha}".encode() not in existing:
                    fh.write(header.encode("utf-8") + body.encode("utf-8"))
            fh.flush(); os.fsync(fh.fileno())
        written = apath.read_bytes()
        for header, _ in archive_blocks:
            sha = header.rsplit("sha256:", 1)[1].strip()
            if f"sha256:{sha}".encode() not in written:
                return finish_skip("archive verification failed", over)
    except Exception as ex:
        return finish_skip(f"archive write failed: {ex.__class__.__name__}", over)

    # 2) consensus, atomically, only if nobody wrote it meanwhile
    try:
        if cpath.read_bytes() != data:
            return finish_skip("consensus changed during run", over)
        tmp = cpath.with_name(cpath.name + ".prune-tmp")
        tmp.write_bytes(new_data)
        os.replace(tmp, cpath)
    except Exception as ex:
        return finish_skip(f"consensus write failed: {ex.__class__.__name__}", over)

    # post_metrics mirrors ledger-guard._metrics so the guard can rebase its baseline.
    post_metrics = {
        "sections": len(re.findall(r"(?m)^## ", new_text)),
        "rows": len(set(re.findall(r"OPEX Kalemleri!A\d+", new_text))),
        "bytes": len(new_data),
        "sha16": _sha16(new_data),
        "incident": bool(INCIDENT_WORDS_RE.search(new_text)),
    }
    warns = record_history()
    state.update({
        "last_prune_cycle": args.cycle,
        "pre_sha16": _sha16(data),
        "post_sha16": _sha16(new_data),
        "post_metrics": post_metrics,
        "bytes_before": len(data),
        "bytes_after": len(new_data),
        "archive": arel,
        "block_sha256": [h.rsplit("sha256:", 1)[1].strip() for h, _ in archive_blocks],
        "moved": moved,
        "skipped_streak": 0,
        "last_cycle": args.cycle,
    })
    _save_state(spath, state)
    sys.stdout.write(summary + "\n")
    emit_warns(warns)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as ex:  # fail-open for the loop, fail-closed for the data
        sys.stdout.write(f"[CONSENSUS-PRUNE] error: {ex.__class__.__name__} — nothing written\n")
        sys.exit(0)
