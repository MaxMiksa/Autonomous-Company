#!/usr/bin/env python3
"""Deterministic staleness ("bayatlık") measurements for the Program Auditor.

Why (2026-10-13): the operator noticed the live directive still carried September
"standing queues" and BOŞ-CYCLE rules as binding text; the body had grown to 82 KB
and the loop re-read it every cycle. Nobody measures rot unless a script does, so
this one does, read-only, stdlib only, and writes `memories/staleness-report.md`.
The auditor INTERPRETS this file (archive / leave / ask) and never recomputes it.

Measured surfaces (each a table row with a mechanical flag):
  D  directive sections: bytes, age (date in heading), standing-rule vocabulary
  O  operator-requests.md: OPREQ count by Status; bytes of RESOLVED text
  K  operator-decisions.md: bytes, decision count, pre-recharter (< 2026-08-24) count
  C  consensus.md: section bytes, '(Prior' count
  L  ledger: bytes, header version line vs number of '## ' sections, last section
  P  PROMPT.md: bytes, section bytes, legacy-vocabulary hits
  W  weekly reports: ISO weeks present vs expected since the first report
  B  backups/receipts: counts and bytes under memories/
Flags are suggestions for a reader, not actions. Usage:
  staleness-report.py [--app /app] [--out memories/staleness-report.md] [--stdout]
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

# Turkish + English (K-2, 2026-10-16: the live directive is English from now on).
STANDING_WORDS = re.compile(r"standing|kuyru[kğ]|YASAK|her cycle|BOŞ-CYCLE|IDLE ETME"
                            r"|\bqueue\b|FORBIDDEN|every cycle|EMPTY-CYCLE|DO NOT IDLE", re.I)
MAIN_PREFIXES = ("## Kaynak belgeler", "## WOWCAR 2.0", "## Operatör açıklaması",
                 "## Source documents", "## Operator note")
ARCHIVE_PREFIXES = ("## ARŞİV", "## ARCHIVE")
LEGACY_WORDS = re.compile(r"tender|discovery|WTP|candidate-registry|EKAP|GLOBAL_SAFETY", re.I)
DATE_RE = re.compile(r"(20\d\d)-(\d\d)-(\d\d)")
RECHARTER = dt.date(2026, 8, 24)


def _bytes(s: str) -> int:
    return len(s.encode("utf-8"))


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _sections(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, list[str]]] = []
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            out.append((line.rstrip("\n"), [line]))
        elif out:
            out[-1][1].append(line)
    return [(h, "".join(ls)) for h, ls in out]


def _heading_date(h: str) -> dt.date | None:
    m = DATE_RE.search(h)
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def directive_rows(app: Path, today: dt.date) -> list[str]:
    text = _read(app / "memories" / "human-directive.md")
    i = text.find("\n## Directive\n")
    body = text[i + len("\n## Directive\n"):] if i >= 0 else ""
    rows = [f"| D0 | direktif gövdesi | {_bytes(body)} B | {'ÜST SINIR' if _bytes(body) > 50000 else 'ok'} |"]
    for h, t in _sections(body):
        if h.startswith(MAIN_PREFIXES):
            continue
        d = _heading_date(h)
        age = (today - d).days if d else None
        standing = len(STANDING_WORDS.findall(t))
        flag = "ok"
        if age is not None and age > 21 and standing >= 3 and not h.startswith(ARCHIVE_PREFIXES):
            flag = "ARŞİV ADAYI: >21 gün + standing dili"
        elif _bytes(t) > 6000 and not h.startswith(ARCHIVE_PREFIXES):
            flag = "büyük bölüm"
        rows.append(f"| D | {h[3:70]} | {_bytes(t)} B, {age if age is not None else '?'} gün, "
                    f"standing={standing} | {flag} |")
    return rows


def opreq_rows(app: Path) -> list[str]:
    text = _read(app / "memories" / "operator-requests.md")
    statuses = re.findall(r"^- Status:\s*([A-Z-]+)", text, re.M)
    counts = {s: statuses.count(s) for s in sorted(set(statuses))}
    resolved_bytes = 0
    for h, t in _sections(text):
        if re.search(r"^- Status:\s*RESOLVED", t, re.M):
            resolved_bytes += _bytes(t)
    flag = "ARŞİV ADAYI: RESOLVED metni gövdede" if resolved_bytes > 8000 else "ok"
    return [f"| O | operator-requests.md | {_bytes(text)} B, OPREQ {len(statuses)}, {counts}, "
            f"RESOLVED metni {resolved_bytes} B | {flag} |"]


def decisions_rows(app: Path) -> list[str]:
    text = _read(app / "memories" / "operator-decisions.md")
    secs = _sections(text)
    old = sum(1 for h, t in secs if (_heading_date(h) or _heading_date(t[:400]) or RECHARTER) < RECHARTER)
    flag = "BÖLÜMLE: re-charter öncesi kararlar arşive" if old >= 5 else "ok"
    return [f"| K | operator-decisions.md | {_bytes(text)} B, {len(secs)} karar, re-charter öncesi {old} | {flag} |"]


def consensus_rows(app: Path) -> list[str]:
    text = _read(app / "memories" / "consensus.md")
    rows = [f"| C0 | consensus.md | {_bytes(text)} B, (Prior={text.count('(Prior')} | "
            f"{'ÜST SINIR' if _bytes(text) > 50000 else 'ok'} |"]
    for h, t in _sections(text):
        if _bytes(t) > 8000:
            rows.append(f"| C | {h[3:50]} | {_bytes(t)} B | büyük bölüm (prune tavanını kontrol et) |")
    return rows


def ledger_rows(app: Path) -> list[str]:
    cands = sorted((app / "docs" / "operations").glob("*conflict-ledger*.md")) if (app / "docs" / "operations").exists() else []
    if not cands:
        return ["| L | ledger | yok | - |"]
    p = cands[0]
    text = _read(p)
    m = re.search(r"^\*\*Version:\*\*\s*([^\n]+)", text, re.M)
    ver = (m.group(1)[:60] if m else "?")
    secs = _sections(text)
    last = secs[-1][0][3:60] if secs else "?"
    # Match on the SECTION CODE (§7GJ), not the cycle number: the header's own cycle is when
    # the header was written (997), the last section's cycle is when it was appended (974) —
    # comparing those flagged a correct header as stale (auditor 2026-10-13 §8.C).
    full = m.group(1) if m else ""
    last_code = re.match(r"(§[0-9A-Z]+)", secs[-1][0][3:].strip()) if secs else None
    header_codes = set(re.findall(r"§[0-9A-Z]+", full))
    if last_code and header_codes:
        stale = last_code.group(1) not in header_codes
    else:  # no section codes to compare: fall back to the older cycle heuristic
        stale = bool(ver and last and "Cycle" in ver
                     and ver.split("Cycle")[1].strip(" ,)")[:3] not in last)
    flag = "BAŞLIK BAYAT: sürüm satırı son bölümü yansıtmıyor" if stale else "ok"
    return [f"| L | {p.name[:50]} | {_bytes(text)} B, {len(secs)} bölüm, sürüm '{ver}', son bölüm '{last}' | {flag} |"]


def prompt_rows(app: Path) -> list[str]:
    text = _read(app / "PROMPT.md")
    rows = [f"| P0 | PROMPT.md | {_bytes(text)} B, eski-çağ sözcükleri {len(LEGACY_WORDS.findall(text))} | "
            f"{'KÜÇÜLT' if _bytes(text) > 25000 else 'ok'} |"]
    for h, t in _sections(text):
        if _bytes(t) > 4000:
            rows.append(f"| P | {h[3:50]} | {_bytes(t)} B | büyük bölüm |")
    return rows


def weekly_rows(app: Path, today: dt.date) -> list[str]:
    d = app / "docs" / "operations"
    weeks = sorted({int(m.group(1)) for p in (d.glob("wowcar-weekly-2026-W*.md") if d.exists() else [])
                    for m in [re.search(r"W(\d\d)", p.name)] if m})
    if not weeks:
        return ["| W | haftalık raporlar | yok | - |"]
    cur = today.isocalendar()[1]
    expected = list(range(weeks[0], cur))
    accepted = _accepted_weekly_gaps(app)
    missing = [w for w in expected if w not in weeks and w not in accepted]
    acc = sorted(w for w in accepted if w in expected and w not in weeks)
    acc_s = f", kabul edilen boşluk W{','.join(map(str, acc))}" if acc else ""
    flag = f"BOŞLUK: W{','.join(map(str, missing))} — geriye yazılmaz, direktifle kapat" if missing else "ok"
    return [f"| W | haftalık raporlar | var {weeks}, bugün W{cur}{acc_s} | {flag} |"]


WEEK_RANGE = re.compile(r"W(\d\d)\s*[-–]\s*W?(\d\d)")
GAP_ACCEPT = re.compile(r"kabul|KAPANDI|geriye dönük yazılmaz|accepted|CLOSED|no retroactive", re.I)


def _accepted_weekly_gaps(app: Path) -> set[int]:
    """Weeks whose missing report the sponsor accepted (directive or its archive).

    A range like 'W37-W40' counts when an acceptance word ('kabul', 'KAPANDI', 'geriye
    dönük yazılmaz') appears within 200 characters of it — the live summary splits the
    sentence over two lines. Without this the row kept flagging a closed gap (auditor
    2026-10-13 §8.C).
    """
    weeks: set[int] = set()
    for name in ("human-directive.md", "human-directive-archive.md"):
        text = _read(app / "memories" / name)
        for m in WEEK_RANGE.finditer(text):
            window = text[max(0, m.start() - 200):m.end() + 200]
            a, b = int(m.group(1)), int(m.group(2))
            if a <= b and b - a < 20 and GAP_ACCEPT.search(window):
                weeks.update(range(a, b + 1))
    return weeks


BACKUP_MAX_AGE_DAYS = 30


def backup_rows(app: Path, today: dt.date) -> list[str]:
    """Real age test (auditor 2026-10-13 §8.C): the old flag fired on file COUNT > 60 while
    its label said '30 günden eski'. Flag only files whose mtime is older than 30 days."""
    mem = app / "memories"
    rows = []
    for name in ("human-directive-backups", "receipts"):
        p = mem / name
        if p.exists():
            files = [f for f in p.iterdir() if f.is_file()]
            total = sum(f.stat().st_size for f in files)
            ages = [(today - dt.datetime.fromtimestamp(f.stat().st_mtime).date()).days for f in files]
            old = sum(1 for a in ages if a > BACKUP_MAX_AGE_DAYS)
            oldest = max(ages) if ages else 0
            flag = f"TEMİZLİK: {old} dosya {BACKUP_MAX_AGE_DAYS} günden eski" if old else "ok"
            rows.append(f"| B | memories/{name} | {len(files)} dosya, {total // 1024} KB, "
                        f"en eski {oldest} gün | {flag} |")
    return rows


def build(app: Path, today: dt.date) -> str:
    rows = (directive_rows(app, today) + opreq_rows(app) + decisions_rows(app) + consensus_rows(app)
            + ledger_rows(app) + prompt_rows(app) + weekly_rows(app, today) + backup_rows(app, today))
    head = (f"# Staleness report — {today.isoformat()} (generated by scripts/ops/staleness-report.py; read-only)\n\n"
            "Mekanik ölçüm; bayraklar öneridir (ARŞİV ADAYI / BÖLÜMLE / BAŞLIK BAYAT / KÜÇÜLT / BOŞLUK / TEMİZLİK).\n"
            "Auditor bunları yorumlar; şirket yalnız direktifle hareket eder.\n\n"
            "| Kod | Yüzey | Ölçüm | Bayrak |\n|---|---|---|---|\n")
    flagged = sum(1 for r in rows if not r.rstrip("| ").endswith("ok") and not r.endswith("| - |"))
    return head + "\n".join(rows) + f"\n\nBayraklı satır: {flagged} / {len(rows)}\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--app", default=os.environ.get("AC_APP_DIR", "/app"))
    ap.add_argument("--out", default="memories/staleness-report.md")
    ap.add_argument("--stdout", action="store_true")
    ap.add_argument("--today", help="YYYY-MM-DD (tests)")
    a = ap.parse_args(argv)
    app = Path(a.app)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    report = build(app, today)
    if a.stdout:
        sys.stdout.write(report)
    else:
        out = app / a.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"ok: {out} ({_bytes(report)} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
