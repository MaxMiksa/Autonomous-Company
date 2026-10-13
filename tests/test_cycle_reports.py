"""Work report isolation, validation, compatibility and failure boundaries."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/core"))
sys.path.insert(0, str(ROOT / "dashboard"))
from cycle_reports import PROMPT, decode, read_report, write_report
from journal_data import JournalSource


class CycleReportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = JournalSource(self.root, "en")
        self.cycle = {"id": "cycle-test", "active": False, "status": "interrupted"}
        self.fields = {"title": "验证 CSV 重复键", "summary": "已补充重复键检查，等待验收。",
                       "phase": "review", "blocker": "", "final": True}

    def write(self, **changes):
        return write_report(self.root, self.cycle["id"], {**self.fields, **changes}, "projects/probe")

    def test_metadata_and_unicode_round_trip(self):
        report = self.write()
        self.assertEqual(read_report(self.source, self.cycle)["workReport"], report)
        self.assertEqual(report["source"], "model_report")
        self.assertEqual(report["project"], "projects/probe")
        self.assertEqual(report["version"], 2)
        self.assertNotIn("next_action", report)
        self.assertIn("+00:00", report["recorded_at"])
        self.assertEqual(self.cycle["status"], "interrupted")

    def test_invalid_updates_preserve_last_valid_report(self):
        self.write()
        original = (self.root / "logs/cycle-test.work.json").read_bytes()
        for changes in ({"title": ""}, {"title": "x" * 61}, {"summary": []}, {"phase": []},
                        {"phase": "done"}, {"phase": "blocked"}, {"blocker": "unexpected"},
                        {"next_action_kind": "none"}, {"next_action": ""}, {"final": "true"},
                        {"summary": "two\nlines"}, {"title": " leading"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.write(**changes)
            self.assertEqual((self.root / "logs/cycle-test.work.json").read_bytes(), original)

    def test_blocked_report_requires_a_reason(self):
        report = self.write(phase="blocked", blocker="Need example input")
        self.assertEqual(report["blocker"], "Need example input")

    def test_legacy_report_projects_remaining_fields_without_rewriting_history(self):
        current = self.write()
        legacy = {**current, "version": 1, "next_action": "retired", "next_action_kind": "planned"}
        path = self.root / "logs/cycle-test.work.json"
        path.write_text(json.dumps(legacy), encoding="utf-8")
        original = path.read_bytes()
        self.assertEqual(read_report(self.source, self.cycle)["workReport"], current)
        self.assertEqual(path.read_bytes(), original)
        for changes in ({"cycle_id": "other"}, {"summary": []}, {"unexpected": True}, {"version": True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                decode(json.dumps({**legacy, **changes}), self.cycle["id"])
        del legacy["next_action_kind"]
        with self.assertRaises(ValueError):
            decode(json.dumps(legacy), self.cycle["id"])

    def test_prompt_no_longer_requests_retired_fields(self):
        self.assertNotIn("--next-", PROMPT)
        self.assertIn("consensus headings", PROMPT)

    def test_reader_rejects_wrong_cycle_version_unknown_keys_and_truncation(self):
        report = self.write()
        for changes in ({"cycle_id": "cycle-other"}, {"version": 3}, {"version": True},
                        {"source": "verified"}, {"project": "../outside"}, {"extra": "ignored?"},
                        {"recorded_at": "2026-09-19T10:00:00"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                decode(json.dumps({**report, **changes}), self.cycle["id"])
        path = self.root / "logs/cycle-test.work.json"
        for raw in ('{"partial":', 'x' * 20000, 'null'):
            path.write_text(raw)
            self.assertEqual(read_report(self.source, self.cycle)["workReportStatus"], "invalid")

    def test_failed_replace_keeps_previous_report_and_removes_temporary(self):
        self.write()
        original = (self.root / "logs/cycle-test.work.json").read_bytes()
        with patch("cycle_reports.os.replace", side_effect=OSError("disk failure")), self.assertRaises(OSError):
            self.write(summary="new")
        self.assertEqual((self.root / "logs/cycle-test.work.json").read_bytes(), original)
        self.assertEqual(len(list((self.root / "logs").iterdir())), 1)

    def test_legacy_missing_report_keeps_original_cycle_outcome(self):
        (self.root / "logs").mkdir()
        entry = {"schema_version": 1, "kind": "cycle_usage", "cycle_id": "cycle-test", "cycle_number": 1,
                 "status": "interrupted", "engine": "codex", "model": "fixture",
                 "started_at": "2026-09-19T01:00:00Z", "ended_at": "2026-09-19T01:01:00Z", "usage": {}}
        (self.root / "logs/usage.jsonl").write_text(json.dumps(entry) + "\n")
        (self.root / "logs/cycle-test.json").write_text(json.dumps({"result": "Existing report"}))
        snapshot = self.source.snapshot()
        cycle = snapshot["cycles"][0]
        self.assertEqual(cycle["workReportStatus"], "missing")
        self.assertEqual(cycle["report"], "Existing report")
        self.write()
        cycle = self.source.snapshot()["cycles"][0]
        self.assertEqual(cycle["status"], "interrupted")
        self.assertTrue(cycle["workReport"]["final"])
        self.assertEqual(cycle["usage"]["status"], "unavailable")

    def test_cli_uses_runtime_context_and_reports_error_without_writing(self):
        env = {**os.environ, "AUTONOMOUS_COMPANY_ROOT": str(self.root),
               "AUTONOMOUS_COMPANY_CYCLE_ID": "cycle-test", "ACTIVE_PROJECT": "projects/probe"}
        command = [sys.executable, str(ROOT / "scripts/core/cycle_reports.py"), "write",
                   "--title", "Quote ' and 中文", "--summary", "Fixture", "--phase", "review", "--final"]
        outcome = subprocess.run(command, env=env, capture_output=True)
        self.assertEqual(outcome.returncode, 0, outcome.stderr)
        self.assertEqual(read_report(self.source, self.cycle)["workReport"]["title"], "Quote ' and 中文")
        env["AUTONOMOUS_COMPANY_CYCLE_ID"] = "../../outside"
        self.assertEqual(subprocess.run(command, env=env, capture_output=True).returncode, 2)
        self.assertEqual(len(list((self.root / "logs").iterdir())), 1)

    @unittest.skipIf(os.name == "nt", "POSIX link boundary checked under WSL")
    def test_linked_directory_and_report_are_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "logs").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.write()
        self.assertEqual(read_report(self.source, self.cycle)["workReportStatus"], "invalid")
        (self.root / "logs").unlink()
        (self.root / "logs").mkdir()
        (outside / "report.json").write_text("sentinel")
        (self.root / "logs/cycle-test.work.json").symlink_to(outside / "report.json")
        with self.assertRaises(ValueError):
            self.write()
        self.assertEqual((outside / "report.json").read_text(), "sentinel")

    def test_rotation_removes_only_expired_paired_report(self):
        self.write()
        logs = self.root / "logs"
        (logs / "cycle-test.log").write_text("old")
        (logs / "cycle-new.log").write_text("new")
        (logs / "cycle-new.work.json").write_text("retain")
        os.utime(logs / "cycle-test.log", (1, 1))
        spec = importlib.util.spec_from_file_location("rotation", ROOT / "scripts/core/rotate-logs.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.rotate(logs, 1), 1)
        self.assertFalse((logs / "cycle-test.work.json").exists())
        self.assertEqual((logs / "cycle-new.work.json").read_text(), "retain")


if __name__ == "__main__":
    unittest.main()
