"""Deterministic Unix bridge, host recovery and real WSL/kernel loop tests."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/core"))
from company_harness import HarnessError, HarnessStore
from company_harness_bridge import MAX_REQUEST, running_bridge
from company_harness_client import request
import company_harness_runner as runner
from product_identity import reserve_cycle
from usage_lib import read_usage_records


@unittest.skipUnless(sys.platform == "linux", "Unix socket execution domain")
class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="harness-execution-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = HarnessStore(self.root, create=True)
        self.store.create_cycle({"cycleId": "formal-cycle", "productId": "product", "sequenceNumber": 6,
                                 "objective": "One primary output", "workKind": "research"})
        self.context = self.store.begin_attempt("formal-cycle", "attempt-one", {"dispatchId": "owned"})["context"]
        self.socket = self.root / "bridge.sock"

    def call(self, action, message_id=None, payload=None, token="bound-token"):
        return request(action, message_id, payload, socket_path=self.socket, token=token)

    def test_fixed_actions_owner_and_generation_cannot_be_overridden(self):
        with running_bridge(self.socket, self.store, self.context, "bound-token"):
            self.assertEqual(self.call("close_cycle")["errorCode"], "UNSUPPORTED_ACTION")
            self.assertEqual(self.call("status", token="wrong")["errorCode"], "UNAUTHORIZED")
            result = self.call("publish_progress", "p", {"reportRevision": 1, "title": "Title",
                "summary": "Actual result", "reportedPhase": "planning"})
            self.assertEqual(result["status"], "accepted")
            self.store.claim_controller("new-generation")
            self.assertEqual(self.call("submit", "s", {"result": "failed", "unfinishedItems": []})["errorCode"], "STALE_GENERATION")

    def test_submit_immediate_ack_before_engine_exit_and_same_id_replay(self):
        with running_bridge(self.socket, self.store, self.context, "bound-token"):
            first = self.call("submit", "stable", {"result": "failed", "unfinishedItems": []})
            self.assertEqual(first["status"], "accepted")
            self.assertEqual(self.store.snapshot()["cycles"][0]["attempts"][0]["status"], "running")
            self.assertEqual(self.call("submit", "stable", {"result": "failed", "unfinishedItems": []}), first)
            self.assertEqual(self.call("submit", "stable", {"result": "blocked", "unfinishedItems": []})["errorCode"], "ID_CONFLICT")

    def test_checkpoint_transfers_bounded_readable_worker_material(self):
        content = "An actual checkpoint"
        ref = {"evidenceId": "cp-v1", "sha256": hashlib.sha256(content.encode()).hexdigest()}
        with running_bridge(self.socket, self.store, self.context, "bound-token"):
            result = self.call("checkpoint", "cp", {"evidenceRefs": [ref], "materials": [{"evidenceId": "cp-v1", "content": content}]})
            self.assertEqual(result["status"], "accepted")
            self.assertEqual(self.store.read_evidence("cp-v1")["content"], content)

    def test_oversized_and_context_injection_requests_rejected(self):
        with running_bridge(self.socket, self.store, self.context, "bound-token"):
            with socket.socket(socket.AF_UNIX) as connection:
                connection.connect(str(self.socket))
                connection.sendall(b"x" * (MAX_REQUEST + 1) + b"\n")
                self.assertEqual(json.loads(connection.makefile("rb").readline())["errorCode"], "REQUEST_TOO_LARGE")
            with socket.socket(socket.AF_UNIX) as connection:
                connection.connect(str(self.socket))
                connection.sendall(json.dumps({"token": "bound-token", "action": "status", "context": {"cycleId": "other"}}).encode() + b"\n")
                self.assertEqual(json.loads(connection.makefile("rb").readline())["errorCode"], "INVALID_REQUEST")


@unittest.skipUnless(sys.platform == "linux", "Linux host ownership and accounting")
class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="harness-runner-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "memories").mkdir()
        shutil.copy2(ROOT / "memories/consensus.template.md", self.root / "memories/consensus.md")
        self.store = HarnessStore(self.root, create=True)
        self.identity = reserve_cycle(self.root, "", "reserved-once", 1)
        self.cycle_id = self.identity["cycleId"]
        runner.prepare(self.store, self.root, self.cycle_id)

    def test_formal_identity_not_reserved_again_for_correction(self):
        first = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, first["temporary"], ignore_errors=True)
        self.store.finish_attempt(first["context"], {"outcome": "failed", "exitCode": 1}, writers_stopped=True, observation="owned supervisor")
        # Finish the pending accounting record before another billable attempt.
        from usage_lib import recover_pending_cycle, load_budget_config
        recover_pending_cycle(self.root / "logs/usage.jsonl", budget_config=load_budget_config({}), pause_path=self.root / ".auto-loop-budget-paused")
        second = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, second["temporary"], ignore_errors=True)
        self.assertNotEqual(first["context"]["attemptId"], second["context"]["attemptId"])
        snapshot = self.store.snapshot()
        self.assertEqual(len(snapshot["cycles"]), 1)
        self.assertEqual(snapshot["cycles"][0]["sequenceNumber"], 1)

    def test_unconfirmed_writer_cannot_be_finished_or_retried(self):
        attempt = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, attempt["temporary"], ignore_errors=True)
        with self.assertRaisesRegex(HarnessError, "WRITERS_UNCONFIRMED"):
            runner.finish_attempt(self.store, self.root, attempt["context"]["attemptId"], {"exit_code": 0}, {"cleanupFailed": True})
        with self.assertRaises((HarnessError, ValueError)):
            runner.begin_attempt(self.store, self.root, self.cycle_id)

    def test_evidence_paths_exclude_other_products_and_authority(self):
        cycle = runner.row(self.store, self.cycle_id)
        receipt = {"docsRoot": str(self.root / "scoped/docs")}
        for path in (".autonomous-company/company-harness.sqlite3", "projects/other/private", "../escape", "/etc/passwd"):
            with self.assertRaises((HarnessError, ValueError)):
                runner.evidence_path(self.root, cycle, receipt, path)

    def test_actual_failures_settle_once_and_keep_logical_relationship(self):
        manifest = runner.begin_attempt(self.store, self.root, self.cycle_id)
        attempt_id = manifest["context"]["attemptId"]
        metadata = {"status": "error", "exit_code": 1, "input_tokens": 10, "output_tokens": 4, "cost_usd": 0.1}
        proof = {"cleanupFailed": False, "supervisorOwner": "owned-session", "observedAt": "now"}
        result = runner.finish_attempt(self.store, self.root, attempt_id, metadata, proof)
        self.assertEqual(result["action"], "human")
        self.assertEqual(runner.finish_attempt(self.store, self.root, attempt_id, metadata, proof), result)
        records, errors = read_usage_records(self.root / "logs/usage.jsonl")
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["cycle_id"], attempt_id)
        self.assertEqual(records[0]["logical_cycle_id"], self.cycle_id)
        self.assertEqual(records[0]["record_role"], "harness_attempt")
        self.assertEqual(self.store.snapshot()["cycles"][0]["usage"]["cost"], 0.1)

    def test_fixed_deadline_and_separate_nonresettable_recovery_budget(self):
        tick = [100.0]
        self.store = HarnessStore(self.root, create=True, clock=lambda: tick[0], boot_id="test-boot")
        from usage_lib import recover_pending_cycle, load_budget_config
        def settled(manifest):
            self.store.finish_attempt(manifest["context"], {"outcome": "failed", "exitCode": 1},
                writers_stopped=True, observation="owned supervisor")
            recover_pending_cycle(self.root / "logs/usage.jsonl", budget_config=load_budget_config({}), pause_path=self.root / ".auto-loop-budget-paused")
        first = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, first["temporary"], ignore_errors=True)
        deadline = self.store.snapshot()["cycles"][0]["deadline"]
        tick[0] += 479
        settled(first)
        correction = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, correction["temporary"], ignore_errors=True)
        self.assertEqual(correction["timeoutSeconds"], 1)
        self.assertEqual(self.store.snapshot()["cycles"][0]["deadline"], deadline)
        tick[0] += 2
        settled(correction)
        with patch.dict(os.environ, {"COMPANY_HARNESS_RECOVERY_SECONDS": "60"}):
            recovery = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, recovery["temporary"], ignore_errors=True)
        self.assertTrue(recovery["recovery"])
        self.assertEqual(recovery["timeoutSeconds"], 60)
        tick[0] += 61
        settled(recovery)
        with self.assertRaisesRegex(HarnessError, "BUDGET_EXHAUSTED"):
            runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.assertEqual(len(self.store.snapshot()["cycles"]), 1)

    def test_crash_after_dispatch_intent_does_not_relaunch_uncertain_writer(self):
        manifest = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, manifest["temporary"], ignore_errors=True)
        before = self.store.snapshot()
        with self.assertRaisesRegex(HarnessError, "UNFINISHED_HARNESS"):
            runner.recover_stopped_cycles(HarnessStore(self.root, create=True), self.root)
        after = self.store.snapshot()
        self.assertEqual(before["snapshotRevision"], after["snapshotRevision"])
        self.assertEqual(len(after["cycles"][0]["attempts"]), 1)
        self.assertTrue((self.root / "logs/usage.jsonl.pending").exists())

    def stopped_material(self, result="completed", with_handoff=False):
        manifest = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, manifest["temporary"], ignore_errors=True)
        attempt_id = manifest["context"]["attemptId"]
        docs = self.root / "collected/docs"
        docs.mkdir(parents=True)
        content = "A deterministic primary artifact"
        (docs / "result.txt").write_text(content)
        ref = {"evidenceId": "primary-v1", "sha256": hashlib.sha256(content.encode()).hexdigest(), "path": "docs/result.txt"}
        payload = {"result": result, "unfinishedItems": [], "evidenceRefs": [ref]}
        if with_handoff:
            plan = json.dumps({"nextContract": {"objective": "Continue one bounded research result", "workKind": "research",
                "scope": ["the unfinished research question"], "inputRefs": [ref], "prerequisiteRefs": [],
                "completionOrHandoff": "research note", "timeClass": "regular"}})
            (docs / "handoff.json").write_text(plan)
            handoff = {"evidenceId": "handoff-v1", "sha256": hashlib.sha256(plan.encode()).hexdigest(), "path": "docs/handoff.json"}
            payload.update(handoffRef=handoff, primaryEvidenceId=ref["evidenceId"])
            payload["evidenceRefs"].append(handoff)
        self.store.submit(manifest["context"], "accepted", payload)
        versions = {"projects": "p", "docs": "d", "memories": "m"}
        runner.write_fact(runner.host_path(self.root, attempt_id + ".acceptance.json"), {"submissionId": "accepted", "versions": versions})
        runner.write_fact(runner.host_path(self.root, attempt_id + ".collect.json"), {**{key: manifest["context"][key] for key in ("cycleId", "attemptId", "generation")},
            "collected": True, "docsRoot": str(docs), "versions": versions})
        metadata = {"exit_code": 0, "status": "success", "input_tokens": 10, "output_tokens": 4}
        runner.write_fact(self.root / "logs" / (attempt_id + ".json"), metadata)
        return manifest, metadata

    def test_crash_after_stopped_finish_replays_close_without_work_or_double_charge(self):
        manifest, metadata = self.stopped_material()
        attempt_id = manifest["context"]["attemptId"]
        original = runner.write_fact
        def crash_at_finish(path, value):
            if path.name == attempt_id + ".finish.json":
                raise OSError("deterministic crash after attempt finish commit")
            original(path, value)
        with patch.object(runner, "write_fact", side_effect=crash_at_finish):
            with self.assertRaisesRegex(OSError, "deterministic crash"):
                runner.finish_attempt(self.store, self.root, attempt_id, metadata,
                    {"cleanupFailed": False, "supervisorOwner": "verified-tree", "observedAt": "once"})
        self.assertIsNone(self.store.snapshot()["cycles"][0]["activeAttemptId"])
        restarted = HarnessStore(self.root, create=True)
        with patch.object(runner.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as deterministic_guard:
            runner.recover_stopped_cycles(restarted, self.root)
        self.assertEqual([call.args[0][2] for call in deterministic_guard.call_args_list], ["verify", "snapshot", "close"])
        closed = restarted.snapshot()
        self.assertEqual(closed["cycles"][0]["protocolState"], "closed")
        self.assertEqual(closed["cycles"][0]["outcome"], "completed")
        self.assertEqual(len(read_usage_records(self.root / "logs/usage.jsonl")[0]), 1)
        revision = closed["snapshotRevision"]
        runner.recover_stopped_cycles(restarted, self.root)
        runner.close_cycle(restarted, self.root, self.cycle_id, True)
        self.assertEqual(restarted.snapshot()["snapshotRevision"], revision)

    def test_post_submit_mutation_becomes_same_cycle_correction(self):
        manifest, metadata = self.stopped_material()
        attempt_id = manifest["context"]["attemptId"]
        collected = runner.read_fact(runner.host_path(self.root, attempt_id + ".collect.json"))
        collected["versions"]["docs"] = "changed-after-accepted"
        runner.write_fact(runner.host_path(self.root, attempt_id + ".collect.json"), collected)
        result = runner.finish_attempt(self.store, self.root, attempt_id, metadata,
            {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        self.assertEqual(result["action"], "retry")
        self.assertIn("POST_SUBMISSION_CHANGE", result["error"])
        self.assertEqual(len(self.store.snapshot()["cycles"]), 1)

    def test_finish_receipt_repairs_missing_cycle_result_after_second_write_crash(self):
        manifest, metadata = self.stopped_material()
        attempt_id = manifest["context"]["attemptId"]
        original = runner.write_fact
        def crash_at_cycle_result(path, value):
            if path.name == self.cycle_id + ".result.json":
                raise OSError("crash after durable finish receipt")
            original(path, value)
        with patch.object(runner, "write_fact", side_effect=crash_at_cycle_result):
            with self.assertRaisesRegex(OSError, "durable finish receipt"):
                runner.finish_attempt(self.store, self.root, attempt_id, metadata,
                    {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        self.assertTrue(runner.host_path(self.root, attempt_id + ".finish.json").exists())
        self.assertFalse(runner.host_path(self.root, self.cycle_id + ".result.json").exists())
        with patch.object(runner.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)):
            runner.recover_stopped_cycles(HarnessStore(self.root, create=True), self.root)
        repaired = runner.read_fact(runner.host_path(self.root, self.cycle_id + ".result.json"))
        self.assertEqual(repaired["attemptId"], attempt_id)
        self.assertEqual(self.store.snapshot()["cycles"][0]["protocolState"], "closed")
        self.assertEqual(len(read_usage_records(self.root / "logs/usage.jsonl")[0]), 1)

    def test_old_attempt_finish_replay_cannot_replace_newer_cycle_result(self):
        first, metadata = self.stopped_material()
        first_id = first["context"]["attemptId"]
        old = runner.finish_attempt(self.store, self.root, first_id, metadata,
            {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        second = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, second["temporary"], ignore_errors=True)
        newer = {**old, "attemptId": second["context"]["attemptId"], "error": "newer attempt result"}
        runner.write_fact(runner.host_path(self.root, self.cycle_id + ".result.json"), newer)
        self.assertEqual(runner.finish_attempt(self.store, self.root, first_id, metadata,
            {"cleanupFailed": False, "supervisorOwner": "verified-tree"}), old)
        self.assertEqual(runner.read_fact(runner.host_path(self.root, self.cycle_id + ".result.json")), newer)

    def test_oversized_optional_event_stream_does_not_block_real_close(self):
        from runtime_events import Recorder
        manifest, metadata = self.stopped_material()
        attempt_id = manifest["context"]["attemptId"]
        recorder = Recorder(self.root, attempt_id)
        for _ in range(300):
            recorder.emit("message", text="字" * 3000)
        self.assertGreater(recorder.path.stat().st_size, 2 * 1024 * 1024)
        result = runner.finish_attempt(self.store, self.root, attempt_id, metadata,
            {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        health = result["eventsHealth"]
        self.assertEqual(health["status"], "partial")
        self.assertTrue(health["truncated"])
        self.assertTrue(health["gaps"])
        self.assertGreater(health["recordsRead"], 0)
        self.assertEqual(health["bytesRead"], 2 * 1024 * 1024)
        self.assertEqual(runner.close_cycle(self.store, self.root, self.cycle_id, True)["outcome"], "completed")

    def test_optional_event_identity_conflict_is_not_swallowed(self):
        manifest, metadata = self.stopped_material()
        attempt_id = manifest["context"]["attemptId"]
        event = {"cycleId": "foreign-attempt", "sequence": 1, "kind": "message"}
        path = self.root / "logs" / (attempt_id + ".events.jsonl")
        path.write_text(json.dumps(event) + "\n")
        with self.assertRaisesRegex(HarnessError, "OWNER_MISMATCH"):
            runner.finish_attempt(self.store, self.root, attempt_id, metadata,
                {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        self.assertEqual(self.store.snapshot()["cycles"][0]["activeAttemptId"], attempt_id)
        path.write_text(json.dumps({**event, "cycleId": attempt_id}) + "\n" +
                        json.dumps({**event, "cycleId": attempt_id, "kind": "different-content"}) + "\n")
        with self.assertRaisesRegex(HarnessError, "ID_CONFLICT"):
            runner.finish_attempt(self.store, self.root, attempt_id, metadata,
                {"cleanupFailed": False, "supervisorOwner": "verified-tree"})

    def test_handoff_selection_excludes_sibling_products_and_product_descendants(self):
        class ScopeStore:
            def __init__(self, cycle):
                self.cycle = cycle
            def snapshot(self):
                return {"cycles": [self.cycle]}
        sibling = {"cycleId": "other", "productId": "other-product", "explorationId": "shared-exploration",
            "protocolState": "closed", "outcome": "failed", "continuationDecision": {"allowed": False}}
        for identity in ({"productId": "this-product", "explorationId": "shared-exploration"},
                         {"productId": None, "explorationId": "shared-exploration"}):
            contract = runner.next_contract(ScopeStore(sibling), identity)
            self.assertEqual(contract["workKind"], "objective_selection")

    def test_partial_handoff_can_continue_without_quality_approval(self):
        manifest, metadata = self.stopped_material(result="partial", with_handoff=True)
        finished = runner.finish_attempt(self.store, self.root, manifest["context"]["attemptId"], metadata,
            {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        self.assertTrue(finished["validSubmission"])
        result = runner.close_cycle(self.store, self.root, self.cycle_id, True)
        self.assertEqual(result["outcome"], "partial")
        self.assertTrue(result["continuationAllowed"])
        cycle = self.store.snapshot()["cycles"][0]
        self.assertEqual(cycle["qualityApplicability"], [])
        proposal = runner.next_contract(self.store, {"productId": None, "explorationId": cycle["explorationId"]})
        self.assertEqual(proposal["workKind"], "research")

    def test_completed_handoff_p1_blocks_decision_without_changing_completion(self):
        consensus = self.root / "memories/consensus.md"
        consensus.write_text(consensus.read_text().replace("## Priority Issues", "## Priority Issues\n- [ ] P1: unresolved closing blocker", 1))
        manifest, metadata = self.stopped_material(with_handoff=True)
        runner.finish_attempt(self.store, self.root, manifest["context"]["attemptId"], metadata,
            {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        result = runner.close_cycle(self.store, self.root, self.cycle_id, True)
        self.assertEqual(result["outcome"], "completed")
        self.assertFalse(result["continuationAllowed"])
        cycle = self.store.snapshot()["cycles"][0]
        self.assertEqual(cycle["continuationDecision"]["reason"], "unresolved_p1")
        self.assertEqual(cycle["continuationDecision"]["basis"]["governance"], "unresolved_p1")
        self.assertEqual(cycle["qualityApplicability"], [])

    def test_existing_human_pause_reason_is_preserved_in_closing_decision(self):
        manifest, metadata = self.stopped_material(with_handoff=True)
        runner.finish_attempt(self.store, self.root, manifest["context"]["attemptId"], metadata,
            {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        pause = self.root / ".auto-loop-paused"
        pause.write_text("PAUSE_REASON=human_override_mutated\n")
        result = runner.close_cycle(self.store, self.root, self.cycle_id, True)
        self.assertEqual(result["continuationReason"], "human_override_mutated")
        self.assertEqual(pause.read_text(), "PAUSE_REASON=human_override_mutated\n")

    def test_soft_target_and_adapter_capability_are_persisted(self):
        contract = self.store.snapshot()["cycles"][0]["contract"]
        self.assertEqual(contract["targetRangeSeconds"], [180, 300])
        self.assertEqual(contract["targetSeconds"], 300)
        self.assertFalse(contract["capabilities"]["liveTimeReminder"])

    def assert_transient_recheck(self, blocker):
        if blocker == "budget":
            configured = patch.dict(os.environ, {"USAGE_HARD_LIMIT_TOKENS": "10"})
            configured.start()
            self.addCleanup(configured.stop)
        manifest, metadata = self.stopped_material(with_handoff=True)
        runner.finish_attempt(self.store, self.root, manifest["context"]["attemptId"], metadata,
            {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        consensus = self.root / "memories/consensus.md"
        if blocker == "p1":
            consensus.write_text(consensus.read_text().replace("## Priority Issues", "## Priority Issues\n- [ ] P1: test blocker", 1))
        runner.close_cycle(self.store, self.root, self.cycle_id, True)
        closed = self.store.snapshot()
        receipt = closed["cycles"][0]["closeReceipt"]
        scope = {"productId": None, "explorationId": closed["cycles"][0]["explorationId"]}
        self.assertFalse(closed["cycles"][0]["continuationDecision"]["allowed"])
        self.assertEqual(self.store.snapshot()["snapshotRevision"], closed["snapshotRevision"])
        with self.assertRaises(HarnessError):
            runner.reassess_continuation(self.store, self.root, scope)
        if blocker == "p1":
            consensus.write_text(consensus.read_text().replace("- [ ] P1: test blocker", "- [x] P1: test blocker"))
        else:
            from usage_lib import resume_budget
            self.assertTrue(resume_budget(self.root / ".auto-loop-budget-paused"))
        runner.reassess_continuation(self.store, self.root, scope)
        refreshed = self.store.snapshot()["cycles"][0]
        self.assertTrue(refreshed["continuationDecision"]["allowed"])
        self.assertEqual(refreshed["continuationDecisionRevision"], 1)
        self.assertEqual(refreshed["closeReceipt"], receipt)
        self.assertFalse(receipt["input"]["continuationDecision"]["allowed"])
        self.assertEqual(runner.next_contract(self.store, scope)["workKind"], "research")
        if blocker == "budget":
            resume = self.root / ".auto-loop-budget-paused.resume"
            self.assertTrue(resume.exists(), "next recheck must preserve dispatch acknowledgement")
            identity = reserve_cycle(self.root, "", "next-reserved", 2)
            runner.prepare(self.store, self.root, identity["cycleId"])
            self.assertTrue(resume.exists(), "prepare recheck must preserve the same acknowledgement")
            dispatched = runner.begin_attempt(self.store, self.root, identity["cycleId"])
            self.addCleanup(shutil.rmtree, dispatched["temporary"], ignore_errors=True)
            self.assertFalse(resume.exists(), "only actual dispatch consumes the acknowledgement")
            self.assertFalse((self.root / ".auto-loop-budget-paused").exists())

    def test_p1_resolution_can_reassess_without_rewriting_close_receipt(self):
        self.assert_transient_recheck("p1")

    def test_budget_resume_can_reassess_without_rewriting_close_receipt(self):
        self.assert_transient_recheck("budget")

    def test_harness_settlement_check_preserves_valid_resume_acknowledgement(self):
        from usage_lib import resume_budget
        with patch.dict(os.environ, {"USAGE_HARD_LIMIT_TOKENS": "10"}):
            manifest, metadata = self.stopped_material(with_handoff=True)
            runner.finish_attempt(self.store, self.root, manifest["context"]["attemptId"], metadata,
                {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
            pause = self.root / ".auto-loop-budget-paused"
            self.assertTrue(resume_budget(pause))
            source = (ROOT / "scripts/core/auto-loop.sh").read_text()
            start = source.index("record_cycle_usage() {")
            function = source[start:source.index("\n}\n", start) + 3]
            result = subprocess.run(["bash", "-c", function + "\nrecord_cycle_usage\n"], capture_output=True, text=True,
                env={**os.environ, "COMPANY_HARNESS_ENABLED": "1", "USAGE_TOOL": str(ROOT / "scripts/core/usage.py"),
                     "USAGE_FILE": str(self.root / "logs/usage.jsonl"), "BUDGET_PAUSE_FILE": str(pause)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "hard_limit")
            self.assertFalse(pause.exists())
            self.assertTrue(pause.with_name(pause.name + ".resume").exists())

    def test_startup_duplicate_intents_do_not_revoke_budget_resume(self):
        from usage_lib import resume_budget, UsageError
        with patch.dict(os.environ, {"USAGE_HARD_LIMIT_TOKENS": "10"}):
            manifest, metadata = self.stopped_material(with_handoff=True)
            attempt_id = manifest["context"]["attemptId"]
            runner.finish_attempt(self.store, self.root, attempt_id, metadata,
                {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
            runner.close_cycle(self.store, self.root, self.cycle_id, True)
            pause = self.root / ".auto-loop-budget-paused"
            self.assertTrue(resume_budget(pause))
            acknowledgement = pause.with_name(pause.name + ".resume").read_bytes()
            for _ in range(2):
                with patch.object(sys, "argv", ["harness", "--root", str(self.root), "startup"]):
                    self.assertEqual(runner.main(), 0)
                self.assertFalse(pause.exists())
                self.assertEqual(pause.with_name(pause.name + ".resume").read_bytes(), acknowledgement)
                self.assertEqual(len(read_usage_records(self.root / "logs/usage.jsonl")[0]), 1)
            conflict = runner.read_fact(runner.host_path(self.root, attempt_id + ".usage.json"))
            conflict["model"] = "conflicting-model"
            with self.assertRaisesRegex(UsageError, "different usage data"):
                runner.settle_usage_intent(self.store, self.root, conflict)
            self.assertFalse(pause.exists())

    def test_replay_repairs_ledger_append_before_missing_pause_marker(self):
        with patch.dict(os.environ, {"USAGE_HARD_LIMIT_TOKENS": "10"}):
            manifest, metadata = self.stopped_material(with_handoff=True)
            attempt_id = manifest["context"]["attemptId"]
            with patch("usage_lib._write_pause_marker", side_effect=OSError("crash after ledger fsync")):
                with self.assertRaisesRegex(OSError, "crash after ledger"):
                    runner.finish_attempt(self.store, self.root, attempt_id, metadata,
                        {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
            pause = self.root / ".auto-loop-budget-paused"
            self.assertFalse(pause.exists())
            self.assertEqual(len(read_usage_records(self.root / "logs/usage.jsonl")[0]), 1)
            intent = runner.read_fact(runner.host_path(self.root, attempt_id + ".usage.json"))
            runner.settle_usage_intent(self.store, self.root, intent)
            self.assertTrue(pause.exists())
            self.assertEqual(len(read_usage_records(self.root / "logs/usage.jsonl")[0]), 1)

    def test_old_period_intent_replay_does_not_restore_expired_pause_or_clear_other_pause(self):
        from usage_lib import build_cycle_record
        manifest = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, manifest["temporary"], ignore_errors=True)
        attempt_id = manifest["context"]["attemptId"]
        intent = build_cycle_record(cycle_id=attempt_id, cycle_number=1, started_at="2000-01-01T00:00:00+00:00",
            ended_at="2000-01-01T00:01:00+00:00", status="completed", exit_code=0, engine="codex", model="fixture",
            metadata_raw='{"input_tokens":10,"output_tokens":4}')
        intent.update(record_role="harness_attempt", logical_cycle_id=self.cycle_id, attempt_id=attempt_id)
        with patch.dict(os.environ, {"USAGE_HARD_LIMIT_TOKENS": "10"}):
            runner.settle_usage_intent(self.store, self.root, intent)
            pause = self.root / ".auto-loop-budget-paused"
            self.assertFalse(pause.exists())
            pause.write_text('{"reason":"operator_hold"}')
            runner.settle_usage_intent(self.store, self.root, intent)
            self.assertEqual(pause.read_text(), '{"reason":"operator_hold"}')
            self.assertEqual(len(read_usage_records(self.root / "logs/usage.jsonl")[0]), 1)

    def test_failed_and_missing_handoff_are_not_revived(self):
        manifest, metadata = self.stopped_material(result="failed", with_handoff=True)
        runner.finish_attempt(self.store, self.root, manifest["context"]["attemptId"], metadata,
            {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        runner.close_cycle(self.store, self.root, self.cycle_id, True)
        cycle = self.store.snapshot()["cycles"][0]
        with self.assertRaisesRegex(HarnessError, "CONTINUATION_BLOCKED"):
            runner.reassess_continuation(self.store, self.root, {"productId": None, "explorationId": cycle["explorationId"]})

    def test_completed_without_handoff_cannot_be_revived(self):
        manifest, metadata = self.stopped_material()
        runner.finish_attempt(self.store, self.root, manifest["context"]["attemptId"], metadata,
            {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        runner.close_cycle(self.store, self.root, self.cycle_id, True)
        cycle = self.store.snapshot()["cycles"][0]
        with self.assertRaisesRegex(HarnessError, "CONTINUATION_BLOCKED"):
            runner.reassess_continuation(self.store, self.root, {"productId": None, "explorationId": cycle["explorationId"]})
        self.assertFalse(self.store.snapshot()["cycles"][0]["continuationDecision"]["allowed"])

    def test_late_previous_usage_cannot_select_previous_handoff(self):
        manifest, metadata = self.stopped_material(with_handoff=True)
        runner.finish_attempt(self.store, self.root, manifest["context"]["attemptId"], metadata,
            {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        runner.close_cycle(self.store, self.root, self.cycle_id, True)
        first = self.store.snapshot()["cycles"][0]
        self.store.create_cycle({**first["contract"], "cycleId": "next-open-cycle", "sequenceNumber": 2})
        self.store.record_usage(self.cycle_id, manifest["context"]["attemptId"], {
            "callId": "late-call", "coverage": "unknown", "cost": None, "inputTokens": 3,
            "outputTokens": None, "source": {"type": "late"}})
        with self.assertRaisesRegex(HarnessError, "CONTINUATION_BLOCKED"):
            runner.next_contract(self.store, {"productId": None, "explorationId": first["explorationId"]})
        self.assertEqual(self.store.snapshot()["currentCycleId"], "next-open-cycle")

    def test_unknown_termination_cannot_be_revived(self):
        self.store.close_cycle(self.cycle_id, "unknown-stop", outcome="unknown",
            verification={"writersStopped": True, "attemptResults": [], "evidenceRefs": [], "checkedAt": runner.now()},
            continuation_decision={"allowed": False, "reason": "unknown"})
        cycle = self.store.snapshot()["cycles"][0]
        with self.assertRaisesRegex(HarnessError, "CONTINUATION_BLOCKED"):
            runner.reassess_continuation(self.store, self.root, {"productId": None, "explorationId": cycle["explorationId"]})

    def test_stricter_inner_mode_refused_before_startup_or_cycle_reservation(self):
        with tempfile.TemporaryDirectory(prefix="unsupported-mode-") as folder:
            env = dict(os.environ, COMPANY_HARNESS_ENABLED="1", ENGINE="codex", CODEX_SANDBOX_MODE="read-only")
            result = subprocess.run(["bash", str(ROOT / "scripts/core/auto-loop.sh")], env={**env, "AUTONOMOUS_COMPANY_ROOT": folder}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 78)
            self.assertIn("UNSUPPORTED_INNER_SANDBOX", result.stderr)
            self.assertFalse((Path(folder) / ".autonomous-company").exists())

    def test_recovery_protocol_scope_purpose_size_and_existing_primary(self):
        from company_harness_client import PROTOCOL_LIMIT, protocol_handoff_path
        attempt = {"attemptId": "recovery-owned", "recoveryId": "recovery"}
        business = {"evidenceId": "prior-work", "path": "docs/existing.txt"}
        protocol = {"evidenceId": "handoff", "path": protocol_handoff_path(attempt["attemptId"])}
        payload = {"result": "partial", "evidenceRefs": [business, protocol], "handoffRef": protocol, "primaryEvidenceId": "prior-work"}
        runner.validate_recovery_submission(attempt, payload, lambda _: b'{"nextContract":{"workKind":"research"}}')
        for expected, modified, content in (
            ("RECOVERY_SCOPE", {**payload, "result": "completed"}, b'{}'),
            ("PROTOCOL_PURPOSE", {**payload, "primaryEvidenceId": "handoff"}, b'{}'),
            ("PROTOCOL_PURPOSE", payload, b'{"nextContract":{},"businessDocument":"new work"}'),
            ("PROTOCOL_MATERIAL_TOO_LARGE", payload, b' ' * (PROTOCOL_LIMIT + 1)),
            ("PROTOCOL_SCOPE", {**payload, "evidenceRefs": [business, {**protocol, "path": ".company-harness-protocol/other/handoff.json"}]}, b'{}'),
            ("RECOVERY_PRIMARY_REQUIRED", {**payload, "evidenceRefs": [protocol]}, b'{}'),
        ):
            with self.subTest(expected=expected), self.assertRaisesRegex(HarnessError, expected):
                runner.validate_recovery_submission(attempt, modified, lambda _: content)


@unittest.skipUnless(sys.platform == "linux" and os.environ.get("AUTONOMOUS_COMPANY_BWRAP") and shutil.which("cc"),
                     "Requires official bubblewrap and native compiler; no boundary double")
class KernelLoopTests(unittest.TestCase):
    def test_new_unresolved_p1_blocks_both_correction_and_recovery_dispatch(self):
        from isolation_workspace import TEMPLATES
        for corrections, completed in ((2, False), (0, False), (2, True)):
            with self.subTest(corrections=corrections, completed=completed), tempfile.TemporaryDirectory(prefix="harness-p1-kernel-") as temporary:
                root = Path(temporary)
                for name in TEMPLATES:
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(ROOT / name, target)
                shutil.copytree(ROOT / "scripts/core", root / "scripts/core", dirs_exist_ok=True)
                shutil.copytree(ROOT / "memories", root / "memories")
                source, binary = root / "fake.c", root / "fake-codex"
                program = '''import json,pathlib
consensus=pathlib.Path('/workspace/memories/consensus.md')
body=consensus.read_text()
if '## Next Action' not in body:
    body += chr(10)+'## Next Action'+chr(10)+'Bounded synthetic task'+chr(10)
if '## Company State' not in body:
    body += chr(10)+'## Company State'+chr(10)+'Governance boundary fixture'+chr(10)
body=body.replace('## Priority Issues','## Priority Issues'+chr(10)+'- [ ] P1: synthetic unresolved dispatch blocker',1)
consensus.write_text(body)
counter=pathlib.Path('/workspace/docs/invocations.txt')
counter.write_text((counter.read_text() if counter.exists() else '')+'invoked'+chr(10))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':2,'output_tokens':3}}),flush=True)
'''
                if completed:
                    program += '''import sys
sys.path.insert(0,'/workspace/scripts/core')
from company_harness_client import material,request
plan=pathlib.Path('/workspace/docs/handoff.json')
plan.write_text(json.dumps({'nextContract':{'objective':'Research one bounded question','workKind':'research','scope':['one question'],'inputRefs':[],'prerequisiteRefs':[],'completionOrHandoff':'research note'}}))
ref,_=material(plan)
assert request('submit','completed-with-new-p1',{'result':'completed','unfinishedItems':[],'evidenceRefs':[ref],'handoffRef':ref})['status']=='accepted'
'''
                source.write_text('#include <unistd.h>\n#include <string.h>\n#include <stdio.h>\nint main(int argc,char**argv){if(argc>1&&!strcmp(argv[1],"--version")){puts("p1-fixture");return 0;}char *args[]={"/usr/bin/python3","-c",' + json.dumps(program) + ',0};execv(args[0],args);return 1;}\n')
                subprocess.run(["cc", str(source), "-o", str(binary)], check=True, capture_output=True)
                env = dict(os.environ, COMPANY_HARNESS_ENABLED="1", COMPANY_HARNESS_CORRECTIONS=str(corrections),
                    ENGINE="codex", CODEX_BIN=str(binary), MODEL="gpt-6.1-sol", CODEX_REASONING_EFFORT="high",
                    LOOP_INTERVAL="0", BUDGET_PAUSE_POLL_SECONDS="1", CYCLE_TERM_GRACE_SECONDS="1", CYCLE_KILL_WAIT_SECONDS="1")
                output = root / "owned-output"
                with output.open("w") as stream:
                    process = subprocess.Popen(["bash", str(root / "scripts/core/auto-loop.sh")], env=env, stdout=stream, stderr=stream)
                    try:
                        deadline = time.monotonic() + 45
                        while not (root / ".auto-loop-paused").exists() and process.poll() is None and time.monotonic() < deadline:
                            time.sleep(0.1)
                        self.assertTrue((root / ".auto-loop-paused").exists(), output.read_text())
                        cycles = HarnessStore(root).snapshot()["cycles"]
                        self.assertEqual(len(cycles), 1)
                        self.assertEqual(len(cycles[0]["attempts"]), 1)
                        self.assertEqual(cycles[0]["protocolState"], "closed")
                        self.assertFalse(cycles[0]["continuationDecision"]["allowed"])
                        self.assertEqual(cycles[0]["continuationDecision"]["reason"], "unresolved_p1")
                        self.assertEqual((root / ".auto-loop-paused").read_text(), "PAUSE_REASON=unresolved_p1\n")
                        if completed:
                            self.assertEqual(cycles[0]["outcome"], "completed")
                            self.assertEqual(cycles[0]["continuationDecision"]["basis"]["governance"], "unresolved_p1")
                        self.assertIn("- [ ] P1: synthetic unresolved dispatch blocker", (root / "memories/consensus.md").read_text())
                        scoped = root / ".autonomous-company/isolation" / cycles[0]["explorationId"] / "docs/invocations.txt"
                        self.assertEqual(scoped.read_text().splitlines(), ["invoked"])
                        if not completed:
                            self.assertIn("P1_BLOCK", (root / "logs/auto-loop.log").read_text())
                    finally:
                        (root / ".auto-loop-stop").touch()
                        if process.poll() is None:
                            process.send_signal(signal.SIGTERM)
                        process.wait(timeout=15)

    def test_real_loop_corrects_missing_submit_without_new_cycle_or_duplicate_cost(self):
        self.run_owned_loop(False)

    def test_readonly_recovery_collects_attempt_handoff_and_continues_partial(self):
        self.run_owned_loop(True)

    def test_budget_only_pause_resumes_real_loop_without_extra_governance_pause(self):
        self.run_owned_loop(False, budget_resume=True)

    def run_owned_loop(self, recovery, budget_resume=False):
        from isolation_workspace import TEMPLATES
        with tempfile.TemporaryDirectory(prefix="harness-kernel-") as temporary:
            root = Path(temporary)
            for name in TEMPLATES:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
            shutil.copytree(ROOT / "scripts/core", root / "scripts/core", dirs_exist_ok=True)
            shutil.copytree(ROOT / "memories", root / "memories")
            fake_source, fake = root / "fake.c", root / "fake-codex"
            program = '''import json,os,pathlib,sys
sys.path.insert(0,'/workspace/scripts/core')
from company_harness_client import material,request
assert not pathlib.Path('/workspace/.autonomous-company/company-harness.sqlite3').exists()
assert not pathlib.Path('/home/max').exists()
status=request('status')['cycle']
recovery=os.environ.get('COMPANY_HARNESS_RECOVERY')=='1'
consensus=pathlib.Path('/workspace/memories/consensus.md')
body=consensus.read_text()
if '## Next Action' not in body:
    body += chr(10)+'## Next Action'+chr(10)+'Continue the one bounded task'+chr(10)
if '## Company State' not in body:
    body += chr(10)+'## Company State'+chr(10)+'Deterministic isolation fixture only'+chr(10)
if not recovery:
    consensus.write_text(body)
docs=pathlib.Path('/workspace/docs')
marker=docs/'correction-marker'
if not marker.exists():
    marker.write_text('first attempt had no submission')
elif recovery:
    import errno
    from company_harness_client import protocol_handoff_path
    for folder in ('docs','projects','memories'):
        try:
            (pathlib.Path('/workspace')/folder/'forbidden-recovery-write').write_text('not allowed')
            raise AssertionError(folder+' was writable')
        except OSError as error:
            assert error.errno==errno.EROFS,(folder,error)
    primary,_=material(marker)
    target=pathlib.Path('/workspace')/protocol_handoff_path(os.environ['AUTONOMOUS_COMPANY_ATTEMPT_ID'])
    target.write_text(json.dumps({'nextContract':{'objective':'Research one concrete customer problem','workKind':'research','scope':['one customer problem'],'inputRefs':[primary],'prerequisiteRefs':[],'completionOrHandoff':'research note'}}))
    handoff,_=material(target)
    payload={'result':'partial','unfinishedItems':['Selected bounded question needs research'],'evidenceRefs':[primary,handoff],'primaryEvidenceId':primary['evidenceId'],'handoffRef':handoff}
    assert request('submit','wrong-purpose',{**payload,'primaryEvidenceId':handoff['evidenceId']})['errorCode']=='PROTOCOL_PURPOSE'
    foreign={**handoff,'path':'.company-harness-protocol/another-attempt/handoff.json'}
    assert request('submit','wrong-owner',{**payload,'evidenceRefs':[primary,foreign],'handoffRef':foreign})['errorCode']=='PROTOCOL_SCOPE'
    legitimate=target.read_text()
    target.write_text(' '*16385)
    assert request('submit','oversized',payload)['errorCode']=='PROTOCOL_MATERIAL_TOO_LARGE'
    target.write_text(json.dumps({'nextContract':{},'businessDocument':'must not be collected'}))
    assert request('submit','business-document',payload)['errorCode']=='PROTOCOL_PURPOSE'
    target.write_text(legitimate)
    assert request('submit','recovered-partial',payload)['status']=='accepted'
elif status['workKind']=='objective_selection':
    selection=docs/'selection.txt'
    selection.write_text('Selected bounded research question')
    primary,_=material(selection)
    binary=docs/'synthetic-binary.bin'
    binary.write_bytes(bytes([0,255,1,2]))
    binary_ref,_=material(binary)
    target=docs/'next.json'
    target.write_text(json.dumps({'nextContract':{'objective':'Research one concrete customer problem','workKind':'research','scope':['one customer problem'],'timeClass':'regular','inputRefs':[primary,binary_ref],'prerequisiteRefs':[],'completionOrHandoff':'research note'}}))
    ref,_=material(target)
    payload={'result':'completed','unfinishedItems':[],'evidenceRefs':[primary,binary_ref,ref],'handoffRef':ref,'primaryEvidenceId':primary['evidenceId']}
    assert request('submit','stable-objective',payload)['status']=='accepted'
    assert request('submit','stable-objective',payload)['status']=='accepted'
else:
    inputs=pathlib.Path('/run/autonomous-company/harness-inputs')
    versions=json.loads((inputs/'index.json').read_text())
    assert len(versions) in (1,2)
    version=inputs/versions[0]['file']
    assert version.read_text() in ('Selected bounded research question','first attempt had no submission')
    if len(versions)==2:
        assert (inputs/versions[1]['file']).read_bytes()==bytes([0,255,1,2])
    try:
        version.write_text('must not mutate immutable input')
        raise AssertionError('input package was writable')
    except OSError:
        pass
    target=docs/'research.txt'
    target.write_text('Observed customer problem; no quality approval claimed')
    ref,_=material(target)
    assert request('submit','stable-research',{'result':'completed','unfinishedItems':[],'evidenceRefs':[ref]})['status']=='accepted'
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':4}}),flush=True)
'''
            if budget_resume:
                program = program.replace("if not marker.exists():", "if False:")
            fake_source.write_text('#include <unistd.h>\n#include <string.h>\n#include <stdio.h>\nint main(int argc,char**argv){if(argc>1 && !strcmp(argv[1],"--version")){puts("deterministic-fake");return 0;} int configured=0;for(int i=1;i<argc;i++){if(!strcmp(argv[i],"sandbox_mode=\\\"danger-full-access\\\""))configured=1;}if(!configured)return 9; char *args[]={"/usr/bin/python3","-c",' + json.dumps(program) + ',0}; execv(args[0],args); return 1;}\n')
            subprocess.run(["cc", str(fake_source), "-o", str(fake)], check=True, capture_output=True)
            env = dict(os.environ, COMPANY_HARNESS_ENABLED="1", ENGINE="codex", CODEX_BIN=str(fake), MODEL="gpt-6.1-sol",
                COMPANY_HARNESS_CORRECTIONS="0" if recovery else "2", CODEX_SANDBOX_MODE="danger-full-access",
                CODEX_REASONING_EFFORT="high", LOOP_INTERVAL="0", BUDGET_PAUSE_POLL_SECONDS="1",
                CYCLE_TERM_GRACE_SECONDS="1", CYCLE_KILL_WAIT_SECONDS="1")
            if budget_resume:
                env["USAGE_HARD_LIMIT_TOKENS"] = "10"
            output = root / "owned-loop-output"
            with output.open("w") as stream:
                process = subprocess.Popen(["bash", str(root / "scripts/core/auto-loop.sh")], env=env, stdout=stream, stderr=stream)
                try:
                    if budget_resume:
                        from usage_lib import resume_budget
                        deadline = time.monotonic() + 60
                        while process.poll() is None and time.monotonic() < deadline:
                            cycles = HarnessStore(root).snapshot()["cycles"]
                            if cycles and cycles[0]["protocolState"] == "closed" and (root / ".auto-loop-budget-paused").exists():
                                break
                            time.sleep(0.1)
                        self.assertEqual(len(cycles), 1, output.read_text())
                        self.assertEqual(cycles[0]["outcome"], "completed")
                        self.assertEqual(cycles[0]["continuationDecision"]["reason"], "budget_paused")
                        self.assertFalse((root / ".auto-loop-paused").exists(), output.read_text())
                        self.assertTrue(resume_budget(root / ".auto-loop-budget-paused"))
                    deadline = time.monotonic() + 60
                    while not (root / ".auto-loop-paused").exists() and process.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.1)
                    self.assertTrue((root / ".auto-loop-paused").exists(), output.read_text() +
                        ((root / "logs/auto-loop.log").read_text()[-5000:] if (root / "logs/auto-loop.log").exists() else ""))
                    snapshot = HarnessStore(root).snapshot()
                    self.assertEqual(len(snapshot["cycles"]), 2, output.read_text())
                    self.assertEqual([len(c["attempts"]) for c in snapshot["cycles"]], [1, 1] if budget_resume else [2, 1])
                    self.assertEqual([c["sequenceNumber"] for c in snapshot["cycles"]], [1, 2])
                    self.assertEqual(snapshot["cycles"][0]["outcome"], "partial" if recovery else "completed")
                    if not budget_resume:
                        self.assertEqual(bool(snapshot["cycles"][0]["attempts"][1]["recoveryId"]), recovery)
                    else:
                        self.assertTrue(snapshot["cycles"][0]["continuationDecision"]["allowed"])
                        self.assertFalse(snapshot["cycles"][0]["closeReceipt"]["input"]["continuationDecision"]["allowed"])
                    if recovery:
                        self.assertEqual(snapshot["cycles"][0]["qualityApplicability"], [])
                        handoff = snapshot["cycles"][0]["submissions"][-1]["payload"]["handoffRef"]
                        self.assertTrue(handoff["path"].startswith(".company-harness-protocol/"))
                        self.assertIn('"nextContract"', HarnessStore(root).read_evidence(handoff["evidenceId"])["content"])
                    self.assertTrue(all(c["protocolState"] == "closed" for c in snapshot["cycles"]))
                    records, errors = read_usage_records(root / "logs/usage.jsonl")
                    self.assertEqual(errors, [])
                    self.assertEqual(len(records), 2 if budget_resume else 3)
                    self.assertEqual(sum(r["usage"]["total_tokens"] for r in records), 28 if budget_resume else 42)
                    self.assertTrue(all(r["record_role"] == "harness_attempt" for r in records))
                    self.assertEqual(sum(c["usage"]["totalTokens"] for c in snapshot["cycles"]), 28 if budget_resume else 42)
                    self.assertTrue(all(not c["usage"]["totalTokensComplete"] for c in snapshot["cycles"]))
                finally:
                    (root / ".auto-loop-stop").touch()
                    if process.poll() is None:
                        process.send_signal(signal.SIGTERM)
                    process.wait(timeout=15)


if __name__ == "__main__":
    unittest.main()
