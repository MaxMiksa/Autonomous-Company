"""Run the real rotation helpers without starting the loop or an engine."""

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


@unittest.skipIf(os.name == "nt", "rotation contracts execute in POSIX/WSL CI")
class LogRotationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="autonomous-company-rotation-")
        self.addCleanup(self.temp.cleanup)
        self.logs = Path(self.temp.name)
        source = (REPO / "scripts/core/auto-loop.sh").read_text()
        helpers = [re.search(r"^" + name + r"\(\) \{\n.*?^\}", source, re.M | re.S).group()
                   for name in ("log", "get_file_size_bytes", "rotate_logs")]
        self.shell = "set -euo pipefail\n" + "\n".join(helpers) + "\nrotate_logs\n"
        self.sentinels = {"usage.jsonl": "ledger\n", "usage.jsonl.pending": "pending\n",
                          "unrelated.json": "unrelated\n", "cycle-orphan.json": "orphan\n"}
        for name, content in self.sentinels.items():
            (self.logs / name).write_text(content)

    def seed(self, stem, mtime):
        for extension in (".log", ".json", ".context.json", ".work.json", ".events.jsonl"):
            path = self.logs / (stem + extension)
            path.write_text(stem)
            os.utime(path, (mtime, mtime))

    def rotate(self, maximum):
        result = subprocess.run(["bash", "-c", self.shell], capture_output=True, text=True,
                                env=dict(os.environ, LOG_DIR=str(self.logs), MAX_LOGS=str(maximum),
                                         SCRIPT_DIR=str(REPO / "scripts/core")), timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        logs = {p.stem for p in self.logs.glob("cycle-*.log")}
        sidecars = {p.stem for p in self.logs.glob("cycle-*.json") if p.name != "cycle-orphan.json"
                    and not p.name.endswith((".context.json", ".work.json"))}
        self.assertEqual(logs, sidecars)
        for extension in (".context.json", ".work.json", ".events.jsonl"):
            paired = {p.name.removesuffix(extension) for p in self.logs.glob("cycle-*" + extension)}
            self.assertEqual(logs, paired)
        for name, content in self.sentinels.items():
            self.assertEqual((self.logs / name).read_text(), content)
        return logs

    def restart_case(self, maximum):
        old = [f"cycle-{n:04d}-20260917-120000-old" for n in range(2, maximum + 2)]
        for index, stem in enumerate(old):
            self.seed(stem, 1000 + index)
        newest = "cycle-0001-20260918-120000-new"
        self.seed(newest, 2000)
        self.assertEqual(self.rotate(maximum), set(old[1:] + [newest]))

    def test_restart_keeps_newest_pair(self):
        self.restart_case(2)

    def test_restart_with_default_retention(self):
        self.restart_case(200)

    def test_five_digit_cycle_number(self):
        names = [f"cycle-{n}-20260918-120000-run" for n in (9998, 9999, 10000)]
        for index, stem in enumerate(names):
            self.seed(stem, 1000 + index)
        self.assertEqual(self.rotate(2), set(names[1:]))

    def test_legacy_names_and_equal_mtime_use_stable_name_order(self):
        self.seed("cycle-0001", 1000)
        self.seed("cycle-0002-20260101-000000", 1000)
        self.seed("cycle-0003-20260101-000000-run", 1000)
        self.assertEqual(self.rotate(2), {"cycle-0002-20260101-000000",
                                         "cycle-0003-20260101-000000-run"})

    def test_mtime_wins_over_filename_date(self):
        self.seed("cycle-9000-20260101-000000", 2000)
        self.seed("cycle-9999-20260918-000000", 1000)
        self.assertEqual(self.rotate(1), {"cycle-9000-20260101-000000"})

    def test_below_limit_preserves_logs_and_main_log_rotation(self):
        self.seed("cycle-0001", 1000)
        (self.logs / "auto-loop.log").write_bytes(b"x" * (10485760 + 1))
        self.assertEqual(self.rotate(2), {"cycle-0001"})
        self.assertEqual((self.logs / "auto-loop.log.old").stat().st_size, 10485761)


if __name__ == "__main__":
    unittest.main()
