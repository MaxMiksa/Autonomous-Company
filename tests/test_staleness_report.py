#!/usr/bin/env python3
"""staleness-report.py — mechanical flags on a synthetic app tree. Usage: python3 tests/test_staleness_report.py"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ops" / "staleness-report.py"
FAILS: list[str] = []


def check(name: str, cond: bool, extra: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        app = Path(td)
        (app / "memories").mkdir()
        (app / "docs" / "operations").mkdir(parents=True)
        (app / "memories" / "human-directive.md").write_text(
            "# Human Directive\n\n## Status\nDONE\n\n## Updated\nx\n\n## Directive\n"
            "## Kaynak belgeler\n\nt\n\n# ANA\n## WOWCAR 2.0 X\n\nana\n\n"
            "## KAPSAM DÜZELTMESİ (2026-09-02, sponsor)\n\nstanding kuyruk YASAK her cycle IDLE ETME\n\n"
            "## YENİ İŞ (2026-10-12)\n\nkısa\n", encoding="utf-8")
        (app / "memories" / "operator-requests.md").write_text(
            "## OPREQ-A\n- Status: RESOLVED\n" + "x" * 9000 + "\n## OPREQ-B\n- Status: OPEN\nkısa\n", encoding="utf-8")
        (app / "memories" / "operator-decisions.md").write_text(
            "".join(f"## Karar {i} (2026-07-{10+i:02d})\n\nmetin\n\n" for i in range(6)) +
            "## Karar yeni (2026-10-01)\n\nmetin\n", encoding="utf-8")
        (app / "memories" / "consensus.md").write_text(
            "## What We Did\n" + "y" * 9000 + "\n(Prior, Cycle 1)\n(Prior, Cycle 2)\n## Next Action\nz\n", encoding="utf-8")
        (app / "docs" / "operations" / "wowcar-gate0-source-of-truth-and-conflict-ledger-2026-08-24.md").write_text(
            "# L\n\n**Version:** 3.05-controlled-draft (Cycle 722, x)\n\n## §7FP (Cycle 722)\n\na\n\n## §7GI (Cycle 973)\n\nb\n",
            encoding="utf-8")
        (app / "PROMPT.md").write_text("## A\n" + "p" * 26000 + "\ntender discovery WTP\n", encoding="utf-8")
        for w in (35, 36, 41):
            (app / "docs" / "operations" / f"wowcar-weekly-2026-W{w}.md").write_text("w", encoding="utf-8")
        (app / "memories" / "human-directive-backups").mkdir()
        for i in range(70):
            (app / "memories" / "human-directive-backups" / f"b{i}.md").write_text("b", encoding="utf-8")

        r = subprocess.run([sys.executable, str(SCRIPT), "--app", str(app), "--today", "2026-10-13"],
                           capture_output=True, text=True)
        check("runs ok", r.returncode == 0, r.stderr)
        rep = (app / "memories" / "staleness-report.md").read_text(encoding="utf-8")
        check("directive standing section flagged as archive candidate",
              "KAPSAM DÜZELTMESİ" in rep and "ARŞİV ADAYI" in rep)
        check("recent short section ok", "| D | YENİ İŞ (2026-10-12) |" in rep and
              [l for l in rep.splitlines() if "YENİ İŞ (2026-10-12)" in l][0].rstrip("| ").endswith("ok"))
        check("ANA directive chunk not listed", "WOWCAR 2.0 X" not in rep)
        check("OPREQ resolved text flagged", "RESOLVED metni gövdede" in rep and "'OPEN': 1" in rep)
        check("decisions pre-recharter flagged", "BÖLÜMLE" in rep and "re-charter öncesi 6" in rep)
        check("consensus big section + Prior count", "(Prior=2" in rep and "What We Did" in rep)
        check("ledger header stale flagged", "BAŞLIK BAYAT" in rep)
        check("PROMPT flagged KÜÇÜLT with legacy words", "KÜÇÜLT" in rep and "eski-çağ sözcükleri 3" in rep)
        check("weekly gap W37-40 flagged", "BOŞLUK: W37,38,39,40" in rep)
        check("backups cleanup flagged", "TEMİZLİK" in rep)
        check("flag summary line", "Bayraklı satır:" in rep)
        r2 = subprocess.run([sys.executable, str(SCRIPT), "--app", str(app), "--today", "2026-10-13", "--stdout"],
                            capture_output=True, text=True)
        check("--stdout prints report", r2.returncode == 0 and r2.stdout.startswith("# Staleness report"))
    print(f"\n{len(FAILS)} failure(s)" if FAILS else "\nALL PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
