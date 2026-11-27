"""Current-cycle work reports cross the real collection transaction only."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/core"))
from cycle_reports import LIMIT, write_report
from product_identity import read_state, register_project, reserve_cycle
if os.name == "posix":
    import isolation_workspace as workspace
    from project_isolation import IsolationError

FIELDS = {"title": "Current task", "summary": "Actual reported work.",
          "phase": "review", "blocker": "", "final": True}


@unittest.skipUnless(os.name == "posix", "CompanyView requires POSIX no-follow files and native Git; run under WSL")
class WorkReportCollectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root, self.view = self.make_view("product", "projects/sample")

    def make_view(self, name, project):
        root = self.base / name
        (root / "projects").mkdir(parents=True)
        rows = "name\tpath\tlifecycle\tcreated_at_utc\n"
        if project:
            (root / project).mkdir()
            (root / project / "value.txt").write_text("original")
            rows += "sample\tprojects/sample\tlocal\t2026-10-06\n"
        (root / "projects/registry.tsv").write_text(rows)
        (root / "memories").mkdir()
        (root / "memories/consensus.md").write_text(
            "# Consensus\n\n## Current Phase\nPlanning\n\n## Human Overrides\n- keep\n\n## Priority Issues\n- none\n")
        cycle = reserve_cycle(root, project, "report-attempt", 1)["cycleId"]
        view = workspace.CompanyView(root, project, cycle)
        self.addCleanup(shutil.rmtree, view.folder, ignore_errors=True)
        # Public template contents are irrelevant to collection. Identity,
        # private files, host fingerprints and transaction locks remain real.
        with patch.object(workspace, "TEMPLATES", ()):
            view.prepare()
        return root, view

    def report(self, view=None):
        view = view or self.view
        write_report(view.workspace, view.cycle, FIELDS, view.project)
        return view.workspace / "logs" / (view.cycle + ".work.json")

    def assert_refused(self):
        state = (self.root / ".autonomous-company/product-state.json").read_bytes()
        consensus = (self.root / "memories/consensus.md").read_bytes()
        (self.view.workspace / "projects/sample/value.txt").write_text("candidate")
        with self.assertRaises((IsolationError, ValueError, OSError)):
            self.view.collect()
        self.assertFalse(self.view.collected)
        self.assertTrue(self.view.folder.exists())
        self.assertEqual((self.root / "projects/sample/value.txt").read_text(), "original")
        self.assertEqual((self.root / ".autonomous-company/product-state.json").read_bytes(), state)
        self.assertEqual((self.root / "memories/consensus.md").read_bytes(), consensus)
        self.assertFalse((self.root / ".autonomous-company/isolation-pending.json").exists())

    def assert_report_rejected(self, root, view, reason):
        source = view.workspace / "logs" / (view.cycle + ".work.json")
        original = source.read_bytes()
        original_state = (root / ".autonomous-company/product-state.json").read_bytes()
        (view.workspace / "projects/sample/value.txt").write_text("candidate")
        updated_consensus = "# Consensus\n\n## Current Phase\nUpdated\n\n## Human Overrides\n- keep\n\n## Priority Issues\n- none\n"
        (view.workspace / "memories/consensus.md").write_text(updated_consensus)
        session = view.home / ".codex/sessions/session.jsonl"
        session.parent.mkdir(parents=True)
        session.write_text("retained session")
        view.collect()
        self.assertTrue(view.collected)
        self.assertTrue(view.retain_view)
        self.assertEqual(source.read_bytes(), original)
        self.assertFalse((root / "logs" / source.name).exists())
        self.assertEqual((root / "projects/sample/value.txt").read_text(), "candidate")
        self.assertEqual((root / "memories/consensus.md").read_text(), updated_consensus)
        # Collection may serialize unchanged state with different whitespace.
        self.assertEqual(read_state(root), json.loads(original_state))
        record = json.loads((view.store / "last-run.json").read_text())
        rejection, = record["uncollectedWorkReports"]
        self.assertEqual(rejection["path"], "logs/" + source.name)
        self.assertIn(reason, rejection["reason"])
        self.assertEqual((Path(record["sessions"]) / session.name).read_text(), "retained session")
        self.assertFalse((root / ".autonomous-company/isolation-pending.json").exists())

    def test_current_report_preserves_original_bytes_and_joins_collection_journal(self):
        source = self.report()
        data = source.read_bytes()
        original = data + b" " * (LIMIT - len(data))
        source.write_bytes(original)
        (self.view.workspace / "logs/cycle-foreign.work.json").write_text("foreign")
        (self.root / "logs").mkdir()
        (self.root / "logs/cycle-old.work.json").write_text("historical")
        self.view.collect()
        target = self.root / "logs" / source.name
        self.assertEqual(target.read_bytes(), original)
        self.assertFalse((self.root / "logs/cycle-foreign.work.json").exists())
        self.assertEqual((self.root / "logs/cycle-old.work.json").read_text(), "historical")
        journal, = self.view.store.glob("collect-*/collection.json")
        operations = json.loads(journal.read_text())["operations"]
        report_operation, = [item for item in operations if item["target"] == "logs/" + source.name]
        self.assertTrue(report_operation["started"])
        self.assertFalse(report_operation["existed"])

    def test_exploration_report_keeps_original_empty_project_after_product_creation(self):
        root, view = self.make_view("exploration", "")
        project = "projects/new-sample"
        (view.workspace / project).mkdir()
        (view.workspace / project / "README.md").write_text("New product")
        with (view.workspace / "projects/registry.tsv").open("a") as stream:
            stream.write("new-sample\tprojects/new-sample\tlocal\t2026-10-06\n")
        created = register_project(view.workspace, project, view.cycle)
        source = self.report(view)
        original = source.read_bytes()
        view.collect()
        self.assertEqual((root / "logs" / source.name).read_bytes(), original)
        self.assertEqual(json.loads(original)["project"], "")
        self.assertEqual(read_state(root)["paths"][project], created["id"])

    def test_other_cycle_and_other_project_in_current_filename_are_refused(self):
        for index, change in enumerate(({"cycle_id": "cycle-other"}, {"project": "projects/other"}, {"project": ""})):
            with self.subTest(change=change):
                root, view = self.make_view("wrong-scope-" + str(index), "projects/sample")
                source = self.report(view)
                original = json.loads(source.read_text())
                source.write_text(json.dumps({**original, **change}))
                self.assert_report_rejected(root, view, "match")

    def test_current_scope_requires_original_reserved_identity(self):
        self.report()
        self.view.scope = "f" * 32
        self.assert_report_rejected(self.root, self.view, "identity")
        root, view = self.make_view("missing-reservation", "projects/sample")
        self.report(view)
        del view.initial["cycles"][view.cycle]
        workspace.write_json(view.workspace / ".autonomous-company/product-state.json", view.initial)
        self.assert_report_rejected(root, view, "identity")

    def test_malformed_utf8_protocol_and_size_are_rejected_without_blocking_product_work(self):
        report = write_report(self.view.workspace, self.view.cycle, FIELDS, self.view.project)
        for index, raw in enumerate((b'{"partial":', b'\xff', b'null', b'x' * (LIMIT + 1),
                                    json.dumps({**report, "version": 99}).encode(),
                                    json.dumps({**report, "extra": True}).encode())):
            with self.subTest(raw=raw[:30]):
                root, view = self.make_view("malformed-" + str(index), "projects/sample")
                source = self.report(view)
                source.write_bytes(raw)
                self.assert_report_rejected(root, view, "")

    def test_current_report_symlink_and_hardlink_are_refused(self):
        source = self.report()
        candidate = self.view.workspace / "logs/retained-report.json"
        source.rename(candidate)
        source.symlink_to(candidate.name)
        self.assert_refused()
        source.unlink()
        os.link(candidate, source)
        self.assert_refused()

    def test_linked_log_directory_and_nonregular_report_keep_original_safety_refusal(self):
        self.report()
        logs = self.view.workspace / "logs"
        observations = self.view.workspace / "observations"
        logs.rename(observations)
        logs.symlink_to(observations.name, target_is_directory=True)
        self.assert_refused()
        logs.unlink()
        observations.rename(logs)
        source = logs / (self.view.cycle + ".work.json")
        source.unlink()
        os.mkfifo(source)
        self.assert_refused()

    def test_existing_host_report_is_not_overwritten(self):
        source = self.report()
        original = source.read_bytes()
        target = self.root / "logs" / source.name
        target.parent.mkdir()
        target.write_text("retained original observation")
        (self.view.workspace / "projects/sample/value.txt").write_text("candidate")
        self.view.collect()
        self.assertEqual(target.read_text(), "retained original observation")
        self.assertEqual((self.root / "projects/sample/value.txt").read_text(), "candidate")
        self.assertTrue(self.view.collected)
        self.assertTrue(self.view.retain_view)
        record = json.loads((self.view.store / "last-run.json").read_text())
        rejection, = record["uncollectedWorkReports"]
        self.assertIn("overwritten", rejection["reason"])
        self.assertEqual(source.read_bytes(), original)

    def test_sigterm_after_report_install_preserves_report_candidate_and_real_recovery(self):
        # Signal a real subprocess after the report rename, while the durable
        # transaction still holds the product-state lock.
        root = self.base / "signal"
        shutil.copytree(self.root / "projects", root / "projects")
        shutil.copytree(self.root / "memories", root / "memories")
        (root / ".autonomous-company").mkdir()
        shutil.copy2(self.root / ".autonomous-company/product-state.json", root / ".autonomous-company/product-state.json")
        code = """
import shutil, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import isolation_workspace as w
from cycle_reports import write_report
from product_identity import read_state
w.TEMPLATES = ()
root = Path(sys.argv[2])
cycle, = read_state(root)['cycles']
view = w.CompanyView(root, 'projects/sample', cycle)
view.prepare()
write_report(view.workspace, cycle, {'title':'Current task','summary':'Actual reported work.',
    'phase':'review','blocker':'','final':True}, 'projects/sample')
(view.workspace / 'projects/sample/value.txt').write_text('candidate')
original = Path.rename
def after_report(path, target):
    result = original(path, target)
    if Path(target) == root / 'logs' / (cycle + '.work.json'):
        print('report-installed', flush=True)
        time.sleep(60)
    return result
Path.rename = after_report
try:
    view.collect()
finally:
    shutil.rmtree(view.folder, ignore_errors=True)
"""
        process = subprocess.Popen([sys.executable, "-c", code, str(ROOT / "scripts/core"), str(root)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        if process.stdout.readline().strip() != "report-installed":
            _, stderr = process.communicate(timeout=4)
            self.fail("Report collection did not reach the real signal boundary: " + stderr)
        target = root / "logs" / (self.view.cycle + ".work.json")
        original_report = target.read_bytes()
        self.assertTrue((root / ".autonomous-company/product-state.lock").is_dir())
        process.send_signal(signal.SIGTERM)
        _, stderr = process.communicate(timeout=4)
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("Collection interrupted", stderr)
        self.assertFalse((root / ".autonomous-company/product-state.lock").exists())
        pending = root / ".autonomous-company/isolation-pending.json"
        journal = pending.read_bytes()
        operation, = [item for item in json.loads(journal)["operations"]
                      if item["target"] == "logs/" + target.name]
        self.assertTrue(operation["started"])
        with self.assertRaises(IsolationError):
            workspace.CompanyView(root, "projects/sample", "next")
        workspace.recover_collection(root)
        self.assertFalse(target.exists())
        self.assertFalse(pending.exists())
        self.assertEqual((root / operation["source"]).read_bytes(), original_report)
        self.assertEqual((root / "projects/sample/value.txt").read_text(), "original")
        rejected, = (root / ".autonomous-company/isolation").glob("*/collect-*/sample.rejected/value.txt")
        self.assertEqual(rejected.read_text(), "candidate")
        recovered, = (root / ".autonomous-company").glob("isolation-recovered-*.json")
        self.assertEqual(recovered.read_bytes(), journal)


if __name__ == "__main__":
    unittest.main()
