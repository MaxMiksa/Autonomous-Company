"""Execution-domain reads and human recovery using real POSIX locks/guards, no models."""
import importlib.util
import base64
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
SPEC = importlib.util.spec_from_file_location("control_runner", ROOT / "scripts/core/center_runner.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@unittest.skipUnless(sys.platform == "linux", "Real POSIX locks and guards; run under WSL")
class RunnerControlsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        self.environment = patch.dict(os.environ, {"XDG_STATE_HOME": str(Path(self.temp.name) / "state")})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        for name in runner.CONTROL_FILES:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        shutil.copytree(ROOT / "scripts/core", self.root / "scripts/core", dirs_exist_ok=True)
        shutil.copytree(ROOT / "i18n", self.root / "i18n", dirs_exist_ok=True)
        for script in (self.root / "scripts/core").glob("*.sh"):
            script.chmod(0o755)
        (self.root / "memories").mkdir()
        shutil.copy2(ROOT / "memories/consensus.template.md", self.root / "memories")
        (self.root / "projects").mkdir()
        (self.root / "projects/registry.tsv").write_text("name\tpath\tlifecycle\tcreated_at_utc\n")
        self.marker = {"protocolVersion": 2, "centerId": "center_controls", "runtimeId": "runtime_controls",
                       "entryId": "entry_controls", "sourceId": "source_controls"}
        runner.atomic_json(self.root / runner.MARKER, self.marker)
        self.manifest = Path(self.temp.name) / "manifest.json"
        self.owner = {**self.marker, "root": str(self.root), "state": "terminal", "cleanupConfirmed": True}
        runner.atomic_json(runner.owner_dir(self.marker) / "owner.json", self.owner)
        self.assertEqual(self.guard("init").returncode, 0)

    def guard(self, action, *args):
        return subprocess.run(["bash", str(self.root / "scripts/core/consensus-guard.sh"), action, *args],
            env={**os.environ, "AUTONOMOUS_COMPANY_ROOT": str(self.root)}, capture_output=True, text=True, timeout=15)

    def action(self, action, **extra):
        runner.atomic_json(self.manifest, {**self.marker, "root": str(self.root), "action": action, "expectedDispatchId": "dispatch_controls", **extra})
        return runner.source_control(self.manifest)

    def interrupt(self):
        started = self.guard("begin", "1")
        self.assertEqual(started.returncode, 0, started.stderr)
        consensus = self.root / "memories/consensus.md"
        consensus.write_text(consensus.read_text() + "\nTransient business changes\n")
        self.assertEqual(self.guard("recover").returncode, 42)

    def test_original_guard_recovery_then_explicit_confirmation(self):
        self.interrupt()
        original = (self.root / "memories/consensus.md").read_bytes()
        review = self.action("review_recovery")
        self.assertTrue(review["writersStopped"])
        self.assertTrue(review["recoveryComplete"])
        with self.assertRaisesRegex(ValueError, "human_review_required"):
            self.action("confirm_recovery", reviewToken=review["reviewToken"])
        result = self.action("confirm_recovery", reviewToken=review["reviewToken"],
                             productCodeReviewed=True, externalEffectsReviewed=True)
        self.assertFalse(result["resumed"])
        self.assertFalse((self.root / ".auto-loop-paused").exists())
        self.assertEqual((self.root / "memories/consensus.md").read_bytes(), original)

    def test_live_loop_lock_and_unclean_owner_refuse_human_review(self):
        self.interrupt()
        descriptor = runner.lock_file(self.root / ".auto-loop.pid")
        try:
            with self.assertRaisesRegex(ValueError, "external_loop_active"):
                self.action("review_recovery")
        finally:
            os.close(descriptor)
        runner.atomic_json(runner.owner_dir(self.marker) / "owner.json", {**self.owner, "cleanupConfirmed": False})
        with self.assertRaisesRegex(ValueError, "owner_recovery_required"):
            self.action("review_recovery")

    def test_existing_p1_and_budget_pause_cannot_be_cleared(self):
        self.interrupt()
        consensus = self.root / "memories/consensus.md"
        consensus.write_text(consensus.read_text().replace("## Priority Issues", "## Priority Issues\n- [ ] P1: original unresolved issue"))
        with self.assertRaisesRegex(ValueError, "unresolved_p1"):
            self.action("review_recovery")
        self.assertTrue((self.root / ".auto-loop-paused").exists())
        (self.root / ".auto-loop-budget-paused").write_text('{"reason":"hard_limit"}')
        with self.assertRaisesRegex(ValueError, "budget_pause"):
            self.action("review_recovery")
        self.assertTrue((self.root / ".auto-loop-budget-paused").exists())

    def test_product_or_governance_changes_invalidate_review(self):
        self.interrupt()
        review = self.action("review_recovery")
        (self.root / "projects/unregistered-code.txt").write_text("human changes after review")
        with self.assertRaisesRegex(ValueError, "recovery_review_changed"):
            self.action("confirm_recovery", reviewToken=review["reviewToken"],
                        productCodeReviewed=True, externalEffectsReviewed=True)
        self.assertTrue((self.root / ".auto-loop-paused").exists())

    def test_configuration_writer_and_marker_change_refuse_recovery(self):
        self.interrupt()
        (self.root / ".autonomous-company.local.lock").mkdir()
        with self.assertRaisesRegex(ValueError, "configuration_writer_active"):
            self.action("review_recovery")
        (self.root / ".autonomous-company.local.lock").rmdir()
        runner.atomic_json(self.manifest, {**self.marker, "entryId": "entry_different", "root": str(self.root), "action": "review_recovery"})
        with self.assertRaisesRegex(ValueError, "ownership_changed"):
            runner.source_control(self.manifest)

    def test_status_keeps_running_source_compatible_and_config_from_owner(self):
        runner.atomic_json(self.manifest, {**self.marker, "root": str(self.root), "environment": {
            "ENGINE": "codex", "MODEL": "gpt-6.1-sol", "CODEX_REASONING_EFFORT": "high",
            "AUTONOMOUS_COMPANY_LANGUAGE": "zh-CN", "OPENAI_API_KEY": "never expose"}})
        runner.atomic_json(runner.owner_dir(self.marker) / "owner.json", {**self.owner,
            "runner": runner.identity(os.getpid()), "manifest": str(self.manifest), "state": "running"})
        descriptor = runner.lock_file(self.root / ".auto-loop.pid")
        try:
            result = runner.source_query(self.root, center_id=self.marker["centerId"])
            self.assertTrue(result["compatible"])
            self.assertEqual(result["parsed"]["loop"]["processState"], "running")
            self.assertEqual(result["settings"]["CODEX_REASONING_EFFORT"], "high")
            self.assertNotIn("OPENAI_API_KEY", result["settings"])
        finally:
            os.close(descriptor)

    def test_log_pages_and_path_registration_boundary(self):
        folder = self.root / "logs"
        folder.mkdir(exist_ok=True)
        (folder / "cycle-valid.log").write_text("abcdefghij")
        (folder / "cycle-valid.json").write_text('{"status":"running"}')
        result = runner.source_query(self.root, "log", relative_path="logs/cycle-valid.log", offset=3, limit=4)
        self.assertEqual((result["content"], result["nextOffset"], result["totalBytes"], result["eof"]), ("defg", 7, 10, False))
        for path in ("../PROMPT.md", "logs/../PROMPT.md", ".autonomous-company.local", "logs/not-cycle.log"):
            with self.assertRaises(ValueError):
                runner.source_query(self.root, "log", relative_path=path)
        (folder / "cycle-valid.log").write_text("中文记录")
        offset, combined, raw_bytes = 0, "", b""
        while True:
            page = runner.source_query(self.root, "log", relative_path="logs/cycle-valid.log", offset=offset, limit=1)
            combined += page["content"]
            raw_bytes += base64.b64decode(page["bytesBase64"])
            self.assertIn(":", page["revision"])
            offset = page["nextOffset"]
            if page["eof"]:
                break
        self.assertEqual(combined, "中文记录")
        self.assertEqual(raw_bytes, "中文记录".encode("utf-8"))
        (folder / "cycle-unregistered.log").write_text("not registered")
        with self.assertRaisesRegex(ValueError, "cycle_not_recorded"):
            runner.source_query(self.root, "log", relative_path="logs/cycle-unregistered.log")

    def test_active_log_without_final_json_requires_current_pending_identity(self):
        from product_identity import reserve_cycle, update_cycle
        folder = self.root / "logs"
        folder.mkdir(exist_ok=True)
        cycle = reserve_cycle(self.root, "", "attempt-active-check", 1, "codex", "fixture")["cycleId"]
        update_cycle(self.root, cycle, "dispatching")
        (folder / (cycle + ".log")).write_bytes(b"redacted live log")
        runner.atomic_json(folder / (cycle + ".context.json"), {"cycleId": cycle, "project": ""})
        runner.atomic_json(folder / "usage.jsonl.pending", {"cycle_id": cycle})
        (self.root / ".auto-loop-state").write_text("STATUS=running\nPRODUCT_CYCLE_ID=" + cycle + "\n")
        descriptor = runner.lock_file(self.root / ".auto-loop.pid")
        try:
            result = runner.source_query(self.root, "log", relative_path="logs/" + cycle + ".log")
            self.assertEqual(result["content"], "redacted live log")
            runner.atomic_json(folder / (cycle + ".context.json"), {"cycleId": cycle, "project": "projects/other"})
            with self.assertRaisesRegex(ValueError, "cycle_not_recorded"):
                runner.source_query(self.root, "log", relative_path="logs/" + cycle + ".log")
            runner.atomic_json(folder / (cycle + ".context.json"), {"cycleId": cycle, "project": ""})
            runner.atomic_json(folder / "usage.jsonl.pending", {"cycle_id": "cycle-other"})
            with self.assertRaisesRegex(ValueError, "cycle_not_recorded"):
                runner.source_query(self.root, "log", relative_path="logs/" + cycle + ".log")
        finally:
            os.close(descriptor)

    def test_recovery_queries_do_not_write_or_recover(self):
        self.interrupt()
        def snapshot():
            return {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        before = snapshot()
        for query in ("status", "config", "capabilities", "recovery"):
            self.assertTrue(runner.source_query(self.root, query, self.marker["centerId"])["ok"])
        self.assertEqual(snapshot(), before)
        self.assertFalse((self.root / runner.REVIEW_FILE).exists())
        product_lock = self.root / ".autonomous-company/product-state.lock"
        product_lock.mkdir(parents=True)
        result = runner.source_query(self.root, "recovery", self.marker["centerId"])
        self.assertEqual(result["productLock"], {"emptyDirectory": True, "directoryOwnerKnown": False})
        (product_lock / "writer").write_text("unknown owner")
        self.assertFalse(runner.source_query(self.root, "recovery", self.marker["centerId"])["productLock"]["emptyDirectory"])

    def test_changed_owner_nonce_does_not_supply_effective_configuration(self):
        runner.atomic_json(self.manifest, {**self.marker, "root": str(self.root), "nonce": "new-nonce", "environment": {"MODEL": "wrong-config"}})
        runner.atomic_json(runner.owner_dir(self.marker) / "owner.json", {**self.owner, "nonce": "old-nonce", "manifest": str(self.manifest)})
        self.assertNotEqual(runner.source_query(self.root, "config", self.marker["centerId"])["settings"].get("MODEL"), "wrong-config")
        for query in ("status", "config", "log", "recovery"):
            with self.assertRaisesRegex(ValueError, "ownership_changed"):
                runner.source_query(self.root, query, "center_different", relative_path="logs/auto-loop.log")

    def test_dependency_selection_validates_model_effort_and_language_without_provider_run(self):
        with patch.object(runner.subprocess, "run", wraps=subprocess.run) as called:
            result = runner.dependency_checks(engine="codex", model="gpt-6.1-sol", effort="wrong", product_language="zh-CN", require_isolation=False)
        self.assertFalse(result["ok"])
        self.assertEqual(result["diagnostic"], "invalid_reasoning_effort")
        self.assertTrue(all("--version" in call.args[0] for call in called.call_args_list))
        valid = runner.dependency_checks(engine="codex", model="gpt-6.1-sol", effort="high", product_language="zh-CN", require_isolation=False)
        self.assertTrue(valid["ok"])
        config = next(item for item in valid["checks"] if item["name"] == "configuration")
        self.assertEqual((config["model"], config["effort"], config["productLanguage"]), ("gpt-6.1-sol", "high", "zh-CN"))



    def test_dependency_versions_and_enforcement_errors_are_structured(self):
        fake = Path(self.temp.name) / "bwrap"
        fake.write_text("#!/bin/sh\ncase \"$1\" in --help) echo '--disable-userns --assert-userns-disabled';; --version) echo 'bubblewrap 0.8.0';; esac\n")
        fake.chmod(0o755)
        with patch.dict(os.environ, {"AUTONOMOUS_COMPANY_BWRAP": str(fake)}):
            result = runner.dependency_checks(require_isolation=True)
        self.assertFalse(result["ok"])
        self.assertIn("observed bubblewrap 0.8.0", result["diagnostic"])
        basic = runner.dependency_checks(require_isolation=False)
        self.assertTrue(basic["ok"])
        self.assertEqual({row["name"] for row in basic["checks"]}, {"python", "git", "bash"})

    def test_managed_center_recovery_reconciles_and_approves_harness_with_slot_lock(self):
        from company_harness import HarnessStore
        import company_harness_runner as hrunner
        from product_identity import reserve_cycle
        import hashlib

        tstore = HarnessStore(self.root, create=True)
        id1 = reserve_cycle(self.root, "", "managed-good", 1)["cycleId"]
        hrunner.prepare(tstore, self.root, id1)
        a1 = tstore.begin_attempt(id1, "managed-good-1", {"dispatchId": "owned"})
        ev_good = tstore.bind_evidence(id1, "ev-good", "good research note", source={"attemptId": "managed-good-1"})
        ev_ref = {"evidenceId": ev_good["evidenceId"], "sha256": ev_good["sha256"]}
        hoff = {"nextContract": {"objective": "Bounded managed direction", "workKind": "direction",
                                 "scope": ["dir"], "inputRefs": [ev_ref], "prerequisiteRefs": [],
                                 "completionOrHandoff": "direction doc"}}
        hoff_ev = tstore.bind_evidence(id1, "hoff-good", json.dumps(hoff),
                                       source={"attemptId": "managed-good-1"}, media_type="application/json")
        hoff_ref = {"evidenceId": hoff_ev["evidenceId"], "sha256": hoff_ev["sha256"], "path": "docs/harness/h.json"}
        tstore.submit(a1["context"], "sub-good", {
            "result": "completed", "unfinishedItems": [], "evidenceRefs": [ev_ref, hoff_ref],
            "primaryEvidenceId": ev_ref["evidenceId"], "handoffRef": hoff_ref,
        })
        tstore.finish_attempt(a1["context"], {"outcome": "completed", "exitCode": 0}, writers_stopped=True, observation="ok")
        tstore.close_cycle(id1, "close-good", outcome="completed",
            verification={"writersStopped": True, "submittedVersionUnchanged": True,
                          "attemptResults": ["managed-good-1"], "evidenceRefs": [ev_ref, hoff_ref],
                          "checkedAt": hrunner.now()},
            continuation_decision={"allowed": True, "reason": "handoff_validated",
                                   "basis": {"governance": "verified"}, "checkedAt": hrunner.now()},
            submission_id="sub-good")
        hrunner.sync_identity(self.root, hrunner.row(tstore, id1))

        scope = {"productId": None, "explorationId": tstore.snapshot()["cycles"][0]["explorationId"]}
        id2 = reserve_cycle(self.root, "", "managed-crashed", 2)["cycleId"]
        tstore.create_cycle({
            "cycleId": id2, "explorationId": scope["explorationId"], "sequenceNumber": 2, "runCycleNumber": 2,
            "objective": "Crashed managed cycle", "workKind": "direction", "artifactKind": "direction",
            "scope": ["dir"], "inputRefs": [ev_ref], "prerequisiteRefs": [], "completionOrHandoff": "dir doc",
        })
        tstore.begin_attempt(id2, "managed-crash-1", {"dispatchId": "owned"})

        # Direct call without the managed slot lock FD must be refused.
        unowned = subprocess.run([sys.executable, str(self.root / "scripts/core/company_harness_runner.py"),
                                  "--root", str(self.root), "reconcile-crash"], capture_output=True, text=True)
        self.assertNotEqual(unowned.returncode, 0)
        self.assertIn("recoveryAdmission", unowned.stderr)

        self.interrupt()
        review = self.action("review_recovery")
        self.assertTrue(review["recoveryComplete"])
        reconciled = tstore.snapshot()["cycles"][-1]
        self.assertEqual((reconciled["protocolState"], reconciled["outcome"]), ("closed", "interrupted"))

        confirm = self.action("confirm_recovery", reviewToken=review["reviewToken"],
                              productCodeReviewed=True, externalEffectsReviewed=True)
        self.assertFalse(confirm["resumed"])
        self.assertFalse((self.root / ".auto-loop-paused").exists())
        approved = tstore.snapshot()["cycles"][-1]
        self.assertTrue(approved["continuationDecision"]["allowed"])
        self.assertEqual(approved["continuationDecision"]["reason"], "human_recovery_approved")
        self.assertEqual(approved["continuationDecision"]["basis"]["boundNextContract"]["workKind"], "direction")

        startup = subprocess.run([sys.executable, str(self.root / "scripts/core/company_harness_runner.py"),
                                  "--root", str(self.root), "startup"],
                                 env={**os.environ, "CODEX_SANDBOX_MODE": "danger-full-access"},
                                 capture_output=True, text=True)
        self.assertEqual(startup.returncode, 0, startup.stderr)
        planned = hrunner.next_contract(tstore, scope, root=self.root)
        self.assertEqual(planned["workKind"], "direction")
        self.assertEqual(planned["objective"], "Bounded managed direction")


if __name__ == "__main__":
    unittest.main()
