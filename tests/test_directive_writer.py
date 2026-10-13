#!/usr/bin/env python3
"""directive_writer.py — write / append / archive / status / show --sections.

Runs the real script as a subprocess against a temp AC_APP_DIR (no /app, no
Telegram: telegram-notify.sh is absent in the temp tree, so notify() is a no-op).
Usage: python3 tests/test_directive_writer.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITER = ROOT / "scripts" / "core" / "directive_writer.py"
FAILS: list[str] = []


def check(name: str, cond: bool, extra: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


class Env:
    def __init__(self, app: Path, **env: str):
        self.app = app
        self.env = {**os.environ, "AC_APP_DIR": str(app), "AC_ACTOR": "test", **env}
        (app / "memories").mkdir(parents=True, exist_ok=True)

    def run(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(WRITER), *argv], capture_output=True,
                              text=True, env=self.env)

    def live(self) -> str:
        return (self.app / "memories" / "human-directive.md").read_text(encoding="utf-8")

    def audit(self) -> str:
        p = self.app / "memories" / "directive-audit.log"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def show(self) -> dict[str, str]:
        out = self.run("show").stdout
        return dict(l.split("=", 1) for l in out.splitlines() if "=" in l)

    def f(self, name: str, text: str) -> str:
        p = self.app / name
        p.write_text(text, encoding="utf-8")
        return str(p)


BODY = ("## Kaynak belgeler ve konumları\n\nTablo.\n\n# ANA DİREKTİF\n## WOWCAR 2.0 ŞİRKET\n\n### 1. Görev\n"
        "Metin.\n\n## Operatör açıklaması (direktifle birlikte verilen)\n\nNot.\n\n"
        "## KAPSAM DÜZELTMESİ — eski kuyruk\n\nKalıcı kural.\n\n"
        "## SPONSOR KARARI — OPREQ-X-001\n\nResolves: OPREQ-X-001\n"
        "Decision for OPREQ-X-001: ACCEPTED — gerekçe.\n\nAçıklama.\n\n"
        "## İŞ A (2026-10-12)\n\nMadde 1.\nMadde 2.\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        e = Env(Path(td))

        # --- write baseline
        r = e.run("write", "--body-file", e.f("b.md", BODY))
        check("write ok", r.returncode == 0, r.stderr)
        sha0 = e.show()["body_sha256"]

        # --- append: must start with '## '
        r = e.run("append", "--section-file", e.f("bad.md", "metin başlıksız\n"), "--allow-pending")
        check("append refuses non-heading section (rc 3)", r.returncode == 3, r.stderr)

        # --- append: PENDING gate
        r = e.run("append", "--section-file", e.f("s1.md", "## İŞ B (2026-10-13)\n\nYeni madde.\n"))
        check("append refused by PENDING gate without --allow-pending (rc 2)", r.returncode == 2, r.stderr)
        check("audit has append-refused", "action=append-refused" in e.audit())

        # --- append: undefined § in merged body
        r = e.run("append", "--section-file", e.f("s2.md", "## İŞ C\n\nBkz. §9.\n"), "--allow-pending")
        check("append refuses undefined § in merged body (rc 2)", r.returncode == 2, r.stderr)

        # --- append ok
        r = e.run("append", "--section-file", str(e.app / "s1.md"), "--allow-pending")
        check("append ok", r.returncode == 0, r.stderr)
        live = e.live()
        check("append keeps old body and adds new section",
              "## İŞ A (2026-10-12)" in live and live.rstrip().endswith("Yeni madde."))
        check("append sets Status PENDING", re.search(r"^## Status\nPENDING$", live, re.M) is not None)
        check("append audit line", "action=append" in e.audit() and "section='## İŞ B" in e.audit())
        check("append backup exists", any(p.name.endswith("-preappend.md")
                                          for p in (e.app / "memories" / "human-directive-backups").iterdir()))
        sha1 = e.show()["body_sha256"]
        check("append changes body sha", sha1 != sha0)
        check("append prints body_sha256", f"body_sha256={sha1}" in r.stdout)

        # --- status: stale sha refused, fresh sha ok, then back to PENDING via append
        r = e.run("status", "--expect-status", "PENDING", "--to", "DONE", "--expect-body-sha256", sha0)
        check("status with stale sha refused (rc 2)", r.returncode == 2, r.stderr)
        r = e.run("status", "--expect-status", "PENDING", "--to", "DONE", "--expect-body-sha256", sha1)
        check("status with fresh sha ok", r.returncode == 0, r.stderr)
        r = e.run("append", "--section-file", e.f("s3.md", "## İŞ D\n\nBaşka iş.\n"))
        check("append on DONE directive needs no --allow-pending", r.returncode == 0, r.stderr)

        # --- show --sections
        out = e.run("show", "--sections").stdout
        check("show --sections lists first chunk and headings",
              "(ANA DİREKTİF + önsöz)" in out and "## İŞ A (2026-10-12)" in out and "body_bytes=" in out)

        # --- archive: resolver guard
        r = e.run("archive", "--drop-prefix", "## SPONSOR KARARI — OPREQ-X-001",
                  "--summary-file", e.f("sum0.md", "## ARŞİV 9\n\n- OPREQ-X kapandı.\n"), "--allow-pending")
        check("archive refuses dropping resolver section without lines (rc 2)", r.returncode == 2, r.stderr)
        r = e.run("archive", "--drop-prefix", "## YOK BÖYLE", "--summary-file", str(e.app / "sum0.md"),
                  "--allow-pending")
        check("archive with no matching prefix rc 3", r.returncode == 3, r.stderr)
        # status is PENDING now (after append) → gate
        r = e.run("archive", "--drop-prefix", "## İŞ A", "--summary-file", str(e.app / "sum0.md"))
        check("archive refused by PENDING gate (rc 2)", r.returncode == 2, r.stderr)

        # --- archive ok: drop İŞ A + İŞ B + resolver section (summary repeats lines); status preserved
        summ = ("## ARŞİV 9 — kapanan işler\n\n- İŞ A ve İŞ B bitti.\n"
                "Resolves: OPREQ-X-001\nDecision for OPREQ-X-001: ACCEPTED — gerekçe.\n")
        r = e.run("archive", "--drop-prefix", "## İŞ A", "--drop-prefix", "## İŞ B",
                  "--drop-prefix", "## SPONSOR KARARI — OPREQ-X-001",
                  "--summary-file", e.f("sum1.md", summ), "--allow-pending")
        check("archive ok", r.returncode == 0, r.stderr)
        live = e.live()
        check("archive keeps first chunk", "## WOWCAR 2.0 ŞİRKET" in live and "## Kaynak belgeler" in live)
        check("archive drops sections", "Madde 1." not in live and "Yeni madde." not in live)
        check("archive keeps untouched sections", "## KAPSAM DÜZELTMESİ" in live and "## İŞ D" in live)
        check("archive inserts summary at first dropped position",
              live.index("## ARŞİV 9") < live.index("## İŞ D") and live.index("## KAPSAM") < live.index("## ARŞİV 9"))
        check("archive keeps Status PENDING (unchanged)", re.search(r"^## Status\nPENDING$", live, re.M) is not None)
        arch = (e.app / "memories" / "human-directive-archive.md").read_text(encoding="utf-8")
        check("archive file has verbatim text + stamp", "Madde 2." in arch and "<!-- archived " in arch
              and "section_sha16=" in arch)
        check("archive audit line", "action=archive" in e.audit() and "dropped=3" in e.audit())
        check("resolver lines preserved in body", "Resolves: OPREQ-X-001" in live)

        # --- size brake
        big = "## BÜYÜK\n\n" + ("x" * 3000 + "\n") * 3
        e2 = Env(Path(td) / "two", DIRECTIVE_BODY_WARN_BYTES="1000", DIRECTIVE_BODY_MAX_BYTES="5000")
        e2.run("write", "--body-file", e2.f("b.md", BODY))
        r = e2.run("append", "--section-file", e2.f("w.md", "## ORTA\n\n" + "y" * 1500 + "\n"), "--allow-pending")
        check("size brake warns above WARN", r.returncode == 0 and "warn: directive body is" in r.stderr, r.stderr)
        r = e2.run("append", "--section-file", e2.f("big.md", big), "--allow-pending")
        check("size brake refuses above MAX (rc 2)", r.returncode == 2 and "DIRECTIVE_BODY_MAX_BYTES" in r.stderr, r.stderr)
        r = e2.run("append", "--section-file", str(e2.app / "big.md"), "--allow-pending", "--force-size")
        check("--force-size overrides MAX", r.returncode == 0, r.stderr)

    print(f"\n{len(FAILS)} failure(s)" if FAILS else "\nALL PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
