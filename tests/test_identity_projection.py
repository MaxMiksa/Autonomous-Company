"""Synthetic identity transitions across ledger, artifacts and document access."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get("AUTONOMOUS_COMPANY_TEST_SOURCE", Path(__file__).resolve().parents[1]))
sys.path[:0] = [str(ROOT / "scripts/core"), str(ROOT / "dashboard")]
import product_identity as products
from journal_data import JournalSource
from runtime_artifacts import base_record, save


class IdentityProjectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = "projects/probe"
        self.write("projects/probe/DELIVERY.md", "# Synthetic fixture; no model run\n")
        self.write("memories/consensus.md", "# Synthetic fixture\n")
        self.select(self.project)
        self.source = JournalSource(self.root)

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def select(self, project):
        self.write(".autonomous-company.local", f"ACTIVE_PROJECT={project}\n")

    def cycle(self, attempt="original", project=None):
        project = self.project if project is None else project
        row = products.reserve_cycle(self.root, project, attempt, 1, "fixture", "no-model")
        products.update_cycle(self.root, row["cycleId"], "completed")
        return row

    def artifact(self, cycle, kind="document", project=None, product_id=None):
        project = project or self.project
        path = project + ("/report.json" if kind == "check" else "/DELIVERY.md")
        if kind == "check":
            self.write(path, '{"synthetic": true}')
        record = base_record(project, kind)
        record.update(cycleId=cycle, path=path, sha256=hashlib.sha256((self.root / path).read_bytes()).hexdigest())
        if kind == "check":
            record.update(state="completed", exitCode=0, reportStatus="fresh",
                          tests={"tests": 2, "failures": 0, "errors": 0, "skipped": 0})
        if kind == "preview":
            record.update(state="running", url="http://127.0.0.1:1/", token="a" * 32)
        if product_id:
            record["productId"] = product_id
        save(self.root, record)
        return record

    def relocate(self, row):
        (self.root / self.project).rename(self.root / "projects/moved")
        products.relocate_identity(self.root, row["productId"], "projects/moved")
        self.select("projects/moved")

    def replace(self):
        (self.root / "projects/probe/.autonomous-company/identity.json").unlink()
        return products.register_project(self.root, self.project)

    def test_relocation_preserves_historical_path_and_current_cycle(self):
        row = self.cycle()
        self.relocate(row)
        data = self.source.snapshot()
        cycle, = data["cycles"]
        self.assertEqual(cycle["projectId"], self.project)
        self.assertEqual(cycle["projectIdentity"]["project"], self.project)
        self.assertEqual(cycle["stableProductId"], data["project"]["stableId"])
        self.assertTrue(cycle["belongsToCurrentProject"])
        self.assertEqual(data["latestProjectCycleId"], row["cycleId"])

    def test_relocation_includes_history_outside_detail_window(self):
        rows = [self.cycle(str(index)) for index in range(32)]
        self.relocate(rows[0])
        data = self.source.snapshot()
        self.assertEqual(len(data["cycles"]), 32)
        self.assertTrue(all(row["belongsToCurrentProject"] for row in data["cycles"]))
        self.assertEqual(data["cycles"][-1]["detailStatus"], "limited")

    def test_relocated_document_and_checks_use_current_files_keep_original_paths(self):
        row = self.cycle()
        document = self.artifact(row["cycleId"])
        check = self.artifact(row["cycleId"], "check")
        original = (self.root / "logs/artifacts" / (document["id"] + ".json")).read_bytes()
        self.relocate(row)
        data = self.source.snapshot()
        items = {item["id"]: item for item in data["artifacts"]}
        self.assertIn(document["id"], items)
        self.assertEqual(items[document["id"]]["path"], "projects/moved/DELIVERY.md")
        self.assertEqual(items[document["id"]]["recordedPath"], self.project + "/DELIVERY.md")
        self.assertTrue(items[document["id"]]["available"])
        self.assertEqual(data["latestCheck"]["id"], check["id"])
        self.assertEqual(data["cycles"][0]["checks"][0]["tests"]["tests"], 2)
        self.assertIn("Synthetic fixture", self.source.document("projects/moved/DELIVERY.md")[0])
        with self.assertRaises(ValueError):
            self.source.document(self.project + "/DELIVERY.md")
        self.assertEqual((self.root / "logs/artifacts" / (document["id"] + ".json")).read_bytes(), original)
        self.write("projects/moved/DELIVERY.md", "Changed")
        with self.assertRaises(ValueError):
            self.source.document("projects/moved/DELIVERY.md")

    def test_same_path_replacement_excludes_old_documents_checks_and_preview(self):
        row = self.cycle()
        for kind in ("document", "check", "preview"):
            self.artifact(row["cycleId"], kind)
        replacement = self.replace()
        with patch("observability_data.preview_available", return_value=True) as probe:
            data = self.source.snapshot()
        self.assertNotEqual(replacement["id"], row["productId"])
        self.assertFalse(data["cycles"][0]["belongsToCurrentProject"])
        self.assertEqual(data["artifacts"], [])
        self.assertIsNone(data["latestCheck"])
        probe.assert_not_called()
        with self.assertRaises(ValueError):
            self.source.document(self.project + "/DELIVERY.md")

    def test_legacy_without_stable_identity_remains_available(self):
        self.artifact("old-format-cycle")
        data = self.source.snapshot()
        self.assertTrue(data["artifacts"][0]["available"])
        self.assertEqual(data["artifacts"][0]["associationStatus"], "bound")

    def test_unproven_legacy_cannot_attach_to_current_stable_identity(self):
        self.artifact("old-format-cycle")
        self.artifact("old-format-cycle", "check")
        self.cycle()
        data = self.source.snapshot()
        self.assertTrue(all(not item["available"] for item in data["artifacts"]))
        self.assertTrue(all(item["associationStatus"] == "unknown" for item in data["artifacts"]))
        self.assertIsNone(data["latestCheck"])
        with self.assertRaises(ValueError):
            self.source.document(self.project + "/DELIVERY.md")

    def test_missing_marker_and_corrupt_ledger_fail_closed(self):
        row = self.cycle()
        self.artifact(row["cycleId"])
        (self.root / "projects/probe/.autonomous-company/identity.json").unlink()
        self.assertFalse(any(item["available"] for item in self.source.snapshot()["artifacts"]))
        self.write(".autonomous-company/product-state.json", "{broken")
        self.assertFalse(any(item["available"] for item in self.source.snapshot()["artifacts"]))

    def test_unassociated_newer_record_does_not_hide_verified_current_document(self):
        row = self.cycle()
        current = self.artifact(row["cycleId"])
        unbound = self.artifact("unknown-legacy-cycle")
        unbound["recordedAt"] = "2099-01-01T00:00:00+00:00"
        save(self.root, unbound)
        document, = self.source.snapshot()["artifacts"]
        self.assertEqual(document["id"], current["id"])
        self.assertTrue(document["available"])

    def test_wrong_cycle_product_path_or_conflicting_product_id_is_not_bound(self):
        row = self.cycle()
        self.write("projects/other/DELIVERY.md", "Other synthetic fixture")
        other = products.register_project(self.root, "projects/other")
        self.artifact(row["cycleId"], project="projects/other")
        self.artifact(row["cycleId"], "check", product_id=other["id"])
        self.assertEqual(self.source.snapshot()["artifacts"], [])
        self.select("projects/other")
        self.assertFalse(any(item["available"] for item in self.source.snapshot()["artifacts"]))

    def test_linked_exploration_and_operator_documents_survive_relocation_with_recorded_id(self):
        exploration = products.reserve_cycle(self.root, "", "exploration", 1)
        identity = products.register_project(self.root, self.project, exploration["cycleId"])
        products.update_cycle(self.root, exploration["cycleId"], "completed")
        self.artifact(exploration["cycleId"], product_id=identity["id"])
        self.relocate({"productId": identity["id"]})
        data = self.source.snapshot()
        self.assertTrue(data["cycles"][0]["belongsToCurrentProject"])
        self.assertEqual(len(data["artifacts"]), 1)
        self.assertTrue(data["artifacts"][0]["available"])
        self.artifact(None, "check", "projects/moved", identity["id"])
        self.assertTrue(all(item["available"] for item in self.source.snapshot()["artifacts"]))

    def test_legacy_creation_artifact_and_report_keep_historical_location_after_relocation(self):
        from cycle_reports import write_report
        from runtime_artifacts import write_context
        exploration = products.reserve_cycle(self.root, "", "exploration", 1)
        identity = products.register_project(self.root, self.project, exploration["cycleId"])
        self.artifact(exploration["cycleId"])
        write_context(self.root, exploration["cycleId"], "")
        write_report(self.root, exploration["cycleId"], {"title": "Synthetic product", "summary": "Synthetic report",
                     "phase": "review", "blocker": "", "final": True}, self.project)
        products.update_cycle(self.root, exploration["cycleId"], "completed")
        # A product cycle supplies independent historical path evidence that
        # the exploration's creation link alone cannot provide.
        self.cycle("product-path-evidence")
        self.relocate({"productId": identity["id"]})
        data = self.source.snapshot()
        self.assertEqual(len(data["artifacts"]), 1)
        self.assertTrue(data["artifacts"][0]["available"])
        cycle = next(row for row in data["cycles"] if row["id"] == exploration["cycleId"])
        self.assertTrue(cycle["belongsToCurrentProject"])
        self.assertEqual(cycle["projectId"], self.project)
        self.assertEqual(cycle["workReportStatus"], "valid")
        self.assertEqual(cycle["workReport"]["project"], self.project)

    def test_exploration_creation_does_not_adopt_existing_other_product_artifacts(self):
        self.write("projects/other/DELIVERY.md", "Other fixture")
        other = products.register_project(self.root, "projects/other")
        exploration = products.reserve_cycle(self.root, "", "exploration", 1)
        identity = products.register_project(self.root, self.project, exploration["cycleId"])
        current = self.artifact(exploration["cycleId"])
        for kind in ("document", "check", "preview"):
            self.artifact(exploration["cycleId"], kind, "projects/other")
        self.artifact(exploration["cycleId"], "check", product_id=other["id"])
        products.update_cycle(self.root, exploration["cycleId"], "completed")
        self.cycle("product-path-evidence")
        self.relocate({"productId": identity["id"]})
        self.assertEqual([item["id"] for item in self.source.snapshot()["artifacts"]], [current["id"]])
        self.select("projects/other")
        self.assertFalse(any(item["available"] for item in self.source.snapshot()["artifacts"]))

    def test_exploration_creation_does_not_adopt_unregistered_legacy_product_at_another_path(self):
        self.write("projects/legacy/DELIVERY.md", (self.root / self.project / "DELIVERY.md").read_text())
        exploration = products.reserve_cycle(self.root, "", "exploration", 1)
        identity = products.register_project(self.root, self.project, exploration["cycleId"])
        for kind in ("document", "check", "preview"):
            self.artifact(exploration["cycleId"], kind, "projects/legacy")
        products.update_cycle(self.root, exploration["cycleId"], "completed")
        self.assertEqual(self.source.snapshot()["artifacts"], [])
        self.relocate({"productId": identity["id"]})
        self.assertEqual(self.source.snapshot()["artifacts"], [])
        self.select("projects/legacy")
        self.assertFalse(any(item["available"] for item in self.source.snapshot()["artifacts"]))

    def test_absent_exploration_source_is_not_proof_of_relocation(self):
        self.write("projects/legacy/DELIVERY.md", (self.root / self.project / "DELIVERY.md").read_text())
        exploration = products.reserve_cycle(self.root, "", "exploration", 1)
        identity = products.register_project(self.root, self.project, exploration["cycleId"])
        self.artifact(exploration["cycleId"], project="projects/legacy")
        self.artifact(exploration["cycleId"])
        products.update_cycle(self.root, exploration["cycleId"], "completed")
        (self.root / "projects/legacy").rename(self.root / "projects/unregistered-moved")
        self.relocate({"productId": identity["id"]})
        # Neither missing path can be attributed from creation ID + hash alone.
        self.assertEqual(self.source.snapshot()["artifacts"], [])
        with self.assertRaises(ValueError):
            self.source.document("projects/moved/DELIVERY.md")

    def test_runner_records_operator_product_identity_and_replacement_does_not_inherit(self):
        row = self.cycle()
        environment = dict(os.environ, AUTONOMOUS_COMPANY_CYCLE_ID="")
        environment.pop("AUTONOMOUS_COMPANY_CYCLE_ID")
        result = subprocess.run([sys.executable, str(ROOT / "scripts/core/runtime_artifacts.py"),
                                 "--root", str(self.root), "--project", self.project, "document", "DELIVERY.md"],
                                capture_output=True, env=environment, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        record, = [json.loads(path.read_text()) for path in (self.root / "logs/artifacts").glob("*.json")]
        self.assertEqual(record.get("productId"), row["productId"])
        self.assertTrue(self.source.snapshot()["artifacts"][0]["available"])
        self.replace()
        self.assertEqual(self.source.snapshot()["artifacts"], [])


if __name__ == "__main__":
    unittest.main()
