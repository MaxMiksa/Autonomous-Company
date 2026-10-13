"""Real supported runner executions and observation failure boundaries."""
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/core"))
from check_adapters import report_summary
from project_metadata import read_metadata, write_metadata
from runtime_artifacts import base_record, finalize, preview_request, recorded_command, run_check, save, write_context


class RuntimeArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "projects/probe"
        self.project.mkdir(parents=True)
        self.env = dict(os.environ, AUTONOMOUS_COMPANY_ROOT=str(self.root), ACTIVE_PROJECT="projects/probe", AUTONOMOUS_COMPANY_CYCLE_ID="cycle-probe")

    def command(self, *arguments):
        return [sys.executable, str(ROOT / "scripts/core/runtime_artifacts.py"), *arguments]

    def invoke(self, *arguments):
        return subprocess.run(self.command(*arguments), env=self.env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)

    def records(self):
        return [json.loads(path.read_text(encoding="utf-8")) for path in (self.root / "logs/artifacts").glob("*.json")]

    def start_preview(self):
        previous = {row["id"] for row in self.records()}
        process = subprocess.Popen(self.command("preview"), env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        def clean():
            for row in self.records():
                if row["id"] not in previous and row.get("kind") == "preview":
                    preview_request(row, stop=True)
            if process.poll() is None:
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.terminate()
            process.wait(timeout=5)

        self.addCleanup(clean)
        deadline = time.monotonic() + 5
        while process.poll() is None and time.monotonic() < deadline:
            # Windows virtualenv launchers can have a different PID from the
            # Python process; the new registered identity is authoritative.
            record = next((row for row in self.records() if row["id"] not in previous and row.get("kind") == "preview"), None)
            if record and preview_request(record):
                return record
            time.sleep(0.02)
        self.fail("Foreground preview did not become available")

    def test_metadata_roundtrip_identity_and_invalid_update_preservation(self):
        value = write_metadata(self.root, "projects/probe", "检查工具", "真实项目简介")
        self.assertEqual(read_metadata(self.root, "projects/probe"), value)
        self.assertIsNotNone(datetime.fromisoformat(value["recordedAt"]).tzinfo)
        with self.assertRaises(ValueError):
            write_metadata(self.root, "projects/probe", "Bad\nname", "")
        self.assertEqual(read_metadata(self.root, "projects/probe"), value)
        path = self.project / ".autonomous-company-project.json"
        path.write_text(json.dumps({**value, "project": "projects/other"}))
        with self.assertRaises(ValueError):
            read_metadata(self.root, "projects/probe")

    def test_python_runner_executes_once_and_records_fail_skip_and_subtests(self):
        (self.project / "test_sample.py").write_text(
            "import unittest\nfrom pathlib import Path\n"
            "class Cases(unittest.TestCase):\n"
            " def test_pass(self):\n  p=Path('executions'); p.write_text(p.read_text()+'x' if p.exists() else 'x')\n"
            " @unittest.skip('not available')\n def test_skip(self): pass\n"
            " def test_fail(self):\n  for n in (1,2):\n   with self.subTest(n=n): self.assertEqual(n,0)\n")
        result = self.invoke("check", "--adapter", "python-unittest", "--", "discover", "-s", ".")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual((self.project / "executions").read_text(), "x")
        record, = self.records()
        self.assertEqual(record["tests"], {"tests": 3, "failures": 1, "errors": 0, "skipped": 1})
        self.assertEqual(record["cycleId"], "cycle-probe")
        self.assertEqual(record["state"], "completed")
        self.assertEqual(record["reportStatus"], "fresh")
        self.assertEqual(record["exitCode"], 1)
        self.assertTrue((self.root / record["path"]).is_file())

    def test_unittest_expected_failure_is_skipped_and_class_error_has_no_totals(self):
        path = self.project / "test_sample.py"
        path.write_text("import unittest\nclass Cases(unittest.TestCase):\n @unittest.expectedFailure\n def test_expected(self): self.fail('known failure')\n")
        result = self.invoke("check", "--adapter", "python-unittest", "--", "test_sample")
        self.assertEqual(result.returncode, 0, result.stderr)
        record, = self.records()
        self.assertEqual(record["tests"], {"tests": 1, "failures": 0, "errors": 0, "skipped": 1})
        path.write_text("import unittest\nclass Cases(unittest.TestCase):\n @classmethod\n def setUpClass(cls): raise RuntimeError('fixture error')\n def test_case(self): pass\n")
        result = self.invoke("check", "--adapter", "python-unittest", "--", "test_sample")
        self.assertEqual(result.returncode, 1, result.stderr)
        record = next(row for row in self.records() if row["exitCode"] == 1)
        self.assertEqual(record["reportStatus"], "unsupported")
        self.assertNotIn("tests", record)

    @unittest.skipUnless(shutil.which("node"), "Node runtime is unavailable")
    def test_node_native_reporter_runs_once_and_records_genuine_results(self):
        (self.project / "cases.test.cjs").write_text(
            "const test=require('node:test'); const assert=require('node:assert/strict'); const fs=require('node:fs');\n"
            "test('pass',()=>{fs.appendFileSync('node-executions','x');assert.equal(1,1)});\n"
            "test('fail',()=>assert.equal(1,2));test.skip('skip',()=>{});\n")
        result = self.invoke("check", "--adapter", "node-test", "--", "cases.test.cjs")
        self.assertEqual(result.returncode, 1, result.stderr)
        record, = self.records()
        self.assertEqual(record["tests"], {"tests": 3, "failures": 1, "errors": 0, "skipped": 1})
        self.assertEqual((self.project / "node-executions").read_text(), "x")

    @unittest.skipUnless(shutil.which("node"), "Node runtime is unavailable")
    def test_node_failed_todo_is_skipped_with_original_success_exit(self):
        (self.project / "todo.test.cjs").write_text(
            "const test=require('node:test'); const assert=require('node:assert/strict');\n"
            "test.todo('unfinished test',()=>assert.equal(1,2));\n")
        result = self.invoke("check", "--adapter", "node-test", "--", "todo.test.cjs")
        self.assertEqual(result.returncode, 0, result.stderr)
        record, = self.records()
        self.assertEqual(record["exitCode"], 0)
        self.assertEqual(record["tests"], {"tests": 1, "failures": 0, "errors": 0, "skipped": 1})

    def test_check_start_is_visible_and_same_identity_finishes(self):
        process = subprocess.Popen(self.command("check", "--", sys.executable, "-c", "import time; time.sleep(0.5)"), env=self.env)
        try:
            deadline = time.monotonic() + 5
            records = []
            while not records and time.monotonic() < deadline:
                records = self.records()
                time.sleep(0.01)
            self.assertEqual(records[0]["state"], "running")
            identity = records[0]["id"]
            self.assertIsNone(records[0]["exitCode"])
            self.assertEqual(process.wait(timeout=5), 0)
            record, = self.records()
            self.assertEqual(record["id"], identity)
            self.assertEqual(record["state"], "completed")
            self.assertEqual(record["reportStatus"], "unavailable")
            self.assertNotIn("tests", record)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_two_executions_remain_two_records(self):
        for _ in range(2):
            self.assertEqual(self.invoke("check", "--", sys.executable, "-c", "pass").returncode, 0)
        self.assertEqual(len({record["id"] for record in self.records()}), 2)

    def test_recorded_argv_is_bounded_and_redacts_known_credentials(self):
        with patch.dict(os.environ, {"EXAMPLE_API_KEY": "secret-value-example"}):
            recorded, truncated = recorded_command(["python", "secret-value-example", "中文" * 6000])
        self.assertTrue(truncated)
        self.assertEqual(recorded[1], "[REDACTED]")
        self.assertLess(len(json.dumps(recorded, ensure_ascii=False).encode("utf-8")), 8100)

    def test_observation_io_failure_never_masks_command_status(self):
        from argparse import Namespace
        args = Namespace(command=[sys.executable, "-c", "raise SystemExit(7)"], adapter="exit-code", report=None)
        with patch("runtime_artifacts.save", side_effect=OSError("disk unavailable")):
            self.assertEqual(run_check(self.root, self.project, base_record("projects/probe", "check"), args), 7)

    def test_malformed_or_stale_junit_never_becomes_passing_counts(self):
        (self.project / "report.xml").write_text("<testsuite><testcase/></testsuite>")
        result = self.invoke("check", "--report", "report.xml", "--", sys.executable, "-c", "pass")
        self.assertEqual(result.returncode, 0)
        record, = self.records()
        self.assertEqual(record["reportStatus"], "missing_or_stale")
        self.assertNotIn("tests", record)
        result = self.invoke("check", "--report", "report.xml", "--", sys.executable, "-c", "from pathlib import Path; Path('report.xml').write_text('PASS 200'); raise SystemExit(9)")
        self.assertEqual(result.returncode, 9)
        self.assertTrue(any(row["reportStatus"] == "unsupported" and "tests" not in row for row in self.records()))

    def test_aggregate_only_junit_is_unsupported_instead_of_zero_tests(self):
        report = '<testsuite tests="12" failures="3" errors="0" skipped="2"/>'
        script = f"from pathlib import Path; Path('report.xml').write_text({report!r}); raise SystemExit(3)"
        result = self.invoke("check", "--adapter", "junit", "--report", "report.xml", "--", sys.executable, "-c", script)
        self.assertEqual(result.returncode, 3, result.stderr)
        record, = self.records()
        self.assertEqual(record["reportStatus"], "unsupported")
        self.assertNotIn("tests", record)
        self.assertEqual(len(record["sha256"]), 64)

    def test_playwright_counts_final_tests_once_including_retries(self):
        path = self.project / "report.json"
        path.write_text(json.dumps({"suites": [{"specs": [{"tests": [{"status": "flaky", "results": [{"status": "failed"}, {"status": "passed"}]}, {"status": "skipped"}]}]}],
                                    "stats": {"expected": 0, "unexpected": 0, "flaky": 1, "skipped": 1}}))
        self.assertEqual(report_summary(path, "playwright"), {"tests": 2, "failures": 0, "errors": 0, "skipped": 1})
        value = json.loads(path.read_text())
        value["stats"]["expected"] = 9
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            report_summary(path, "playwright")

    def test_launch_failure_is_recorded_without_invented_tests(self):
        result = self.invoke("check", "--", "definitely-not-a-real-program-02937")
        self.assertEqual(result.returncode, 127)
        record, = self.records()
        self.assertEqual(record["state"], "launch_failed")
        self.assertNotIn("tests", record)

    def test_documents_record_project_cycle_hash_and_modification_time(self):
        (self.project / "DELIVERY.md").write_text("Actual delivery")
        self.assertEqual(self.invoke("document", "DELIVERY.md").returncode, 0)
        record, = self.records()
        self.assertEqual(record["project"], "projects/probe")
        self.assertEqual(record["cycleId"], "cycle-probe")
        self.assertEqual(len(record["sha256"]), 64)
        self.assertIsNotNone(datetime.fromisoformat(record["modifiedAt"]).tzinfo)

    def test_foreground_preview_health_stop_and_cycle_ownership(self):
        (self.project / "index.html").write_text("<h1>Actual static fixture</h1>")
        record = self.start_preview()
        try:
            self.assertTrue(preview_request(record))
            self.assertEqual(record["lifetime"], "cycle")
            finalize(self.root, "cycle-other")
            self.assertTrue(preview_request(record))
            finalize(self.root, "cycle-probe")
            deadline = time.monotonic() + 5
            while preview_request(record) and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertFalse(preview_request(record))
        finally:
            preview_request(record, stop=True)

    def test_preview_stop_authenticates_response_and_returns_success(self):
        record = self.start_preview()
        try:
            wrong = {**record, "token": "0" * 32}
            self.assertFalse(preview_request(wrong, stop=True))
            self.assertTrue(preview_request(record))
            result = self.invoke("preview-stop")
            self.assertEqual(result.returncode, 0, result.stderr)
            deadline = time.monotonic() + 5
            while preview_request(record) and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertFalse(preview_request(record))
            self.assertEqual(self.invoke("preview-stop").returncode, 0)
        finally:
            preview_request(record, stop=True)

    def test_finalize_marks_only_own_unfinished_check_interrupted(self):
        for cycle in ("cycle-own", "cycle-other"):
            record = base_record("projects/probe", "check")
            record.update(cycleId=cycle, state="running", endedAt=None, exitCode=None)
            save(self.root, record)
        finalize(self.root, "cycle-own")
        records = {row["cycleId"]: row for row in self.records()}
        self.assertEqual(records["cycle-own"]["state"], "interrupted")
        self.assertIsNone(records["cycle-own"]["endedAt"])
        self.assertEqual(records["cycle-other"]["state"], "running")

    def test_finalize_does_not_drop_cycle_records_after_first_500_files(self):
        for index in range(501):
            record = base_record("projects/probe", "check")
            record.update(cycleId="cycle-probe", state="running", endedAt=None, exitCode=None)
            save(self.root, record)
        preview = self.start_preview()
        try:
            finalize(self.root, "cycle-probe")
            self.assertEqual(sum(row["state"] == "interrupted" for row in self.records()), 501)
            deadline = time.monotonic() + 5
            while preview_request(preview) and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertFalse(preview_request(preview))
        finally:
            preview_request(preview, stop=True)

    def test_cycle_background_rejects_before_spawning_or_registering(self):
        result = self.invoke("preview", "--background")
        self.assertEqual(result.returncode, 2)
        self.assertIn("persistent foreground tool session", result.stderr)
        self.assertEqual(self.records(), [])

    def test_operator_background_remains_available_outside_cycle(self):
        environment = {key: value for key, value in self.env.items() if key != "AUTONOMOUS_COMPANY_CYCLE_ID"}
        result = subprocess.run(self.command("preview", "--background"), env=environment, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        record, = self.records()
        try:
            self.assertEqual(record["lifetime"], "operator")
            self.assertTrue(preview_request(record))
            finalize(self.root, "cycle-probe")
            self.assertTrue(preview_request(record))
        finally:
            preview_request(record, stop=True)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if self.records()[0].get("state") == "stopped":
                    break
                time.sleep(0.02)

    def test_cycle_context_is_explicit_and_does_not_read_consensus(self):
        write_context(self.root, "cycle-bound", "projects/probe")
        context = json.loads((self.root / "logs/cycle-bound.context.json").read_text())
        self.assertEqual(context["project"], "projects/probe")
        self.assertEqual(context["source"], "runtime_context")
        with self.assertRaises(ValueError):
            write_context(self.root, "cycle-bound", "projects/../other")
        self.assertEqual(json.loads((self.root / "logs/cycle-bound.context.json").read_text()), context)


if __name__ == "__main__":
    unittest.main()
