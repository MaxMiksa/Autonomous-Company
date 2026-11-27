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

    def test_acceptance_baseline_and_receipt_rollback_together_on_database_write_failure(self):
        import company_harness
        payload = {"result": "failed", "unfinishedItems": []}
        original = company_harness._Transaction.put
        def fail_receipt(tx, kind, identity, value):
            if kind == 'message' and value['receipt']['action'] == 'submit':
                raise OSError('injected receipt persistence failure')
            return original(tx, kind, identity, value)
        with patch.object(company_harness._Transaction, 'put', fail_receipt):
            with self.assertRaisesRegex(OSError, 'receipt persistence'):
                self.store.submit_with_versions(self.context, 'atomic', payload, lambda _: {'projects': 'first'})
        restarted = HarnessStore(self.root, create=True)
        cycle = restarted.snapshot()['cycles'][0]
        self.assertEqual(cycle['submissions'], [])
        self.assertIsNone(cycle['attempts'][0]['acceptedSubmissionId'])
        receipt = restarted.submit_with_versions(self.context, 'atomic', payload, lambda _: {'projects': 'retried'})
        self.assertEqual(receipt['status'], 'accepted')
        self.assertEqual(restarted.snapshot()['cycles'][0]['submissions'][0]['acceptanceVersions'], {'projects': 'retried'})

    def test_unsupported_evidence_path_is_rejected_before_ack_and_can_be_corrected_in_place(self):
        content = b'reproducible review script'
        ref = {'evidenceId': 'review-script', 'sha256': hashlib.sha256(content).hexdigest(),
               'path': 'logs/recompute_pdf_review.py'}
        payload = {'result': 'completed', 'unfinishedItems': [], 'evidenceRefs': [ref],
                   'primaryEvidenceId': ref['evidenceId']}
        with running_bridge(self.socket, self.store, self.context, 'bound-token'):
            refused = self.call('submit', 'correct-path', payload)
            self.assertEqual(refused['status'], 'rejected')
            self.assertEqual(refused['errorCode'], 'EVIDENCE_SCOPE')
            self.assertIn(ref['path'], json.dumps(refused))
            self.assertEqual(self.call('submit', 'correct-path', payload), refused)
            cycle = self.store.snapshot()['cycles'][0]
            self.assertEqual(cycle['submissions'], [])
            self.assertIsNone(cycle['attempts'][0]['acceptedSubmissionId'])
            corrected = {**payload, 'evidenceRefs': [{**ref, 'path': 'docs/qa/recompute_pdf_review.py'}]}
            accepted = self.call('submit', 'corrected-path', corrected)
            self.assertEqual(accepted['status'], 'accepted')
            self.assertEqual(self.call('submit', 'corrected-path', corrected), accepted)

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

    def test_submit_rechecks_budget_before_accepting(self):
        tick = [100.0]
        bstore = HarnessStore(self.root / "budget-submit", create=True, clock=lambda: tick[0], boot_id="test-boot")
        bstore.create_cycle({"cycleId": "budget-cycle", "productId": "product", "sequenceNumber": 1,
                             "objective": "Check deadline", "workKind": "research"})
        ctx = bstore.begin_attempt("budget-cycle", "budget-att-1", {"dispatchId": "owned"})["context"]
        def expire_during_capture(_attempt):
            tick[0] += 500.0
            return {"projects": "expired"}
        res = bstore.submit_with_versions(ctx, "late-sub", {"result": "failed", "unfinishedItems": []}, expire_during_capture)
        self.assertEqual(res["status"], "rejected")
        self.assertEqual(res["errorCode"], "BUDGET_EXHAUSTED")
        cycle = bstore.snapshot()["cycles"][0]
        self.assertEqual(cycle["submissions"], [])
        self.assertIsNone(cycle["attempts"][0]["acceptedSubmissionId"])

    def test_material_identical_bytes_different_paths_and_conflicting_evidence_id(self):
        from company_harness_client import material
        (self.root / "docs").mkdir(exist_ok=True)
        (self.root / "docs/a.md").write_text("shared bytes", encoding="utf-8")
        (self.root / "docs/b.md").write_text("shared bytes", encoding="utf-8")
        with patch.dict(os.environ, {"AUTONOMOUS_COMPANY_ROOT": str(self.root), "AUTONOMOUS_COMPANY_ATTEMPT_ID": "attempt-one"}):
            ref_a, _ = material("docs/a.md")
            ref_b, _ = material("docs/b.md")
        self.assertNotEqual(ref_a["evidenceId"], ref_b["evidenceId"])
        dup_a = {"evidenceId": "dup-id", "sha256": hashlib.sha256(b"one").hexdigest(), "path": "docs/one.md"}
        dup_b = {"evidenceId": "dup-id", "sha256": hashlib.sha256(b"two").hexdigest(), "path": "docs/two.md"}
        res = self.store.submit(self.context, "dup-submit", {"result": "completed", "unfinishedItems": [], "evidenceRefs": [dup_a, dup_b]})
        self.assertEqual(res["status"], "rejected")
        self.assertEqual(res["errorCode"], "ID_CONFLICT")
        bound = self.store.bind_evidence("formal-cycle", "bound-id-1", "original bytes",
                                         source={"attemptId": "attempt-one", "path": "docs/orig.md"})
        res_path_conflict = self.store.submit(self.context, "bound-path-conflict", {
            "result": "completed", "unfinishedItems": [],
            "evidenceRefs": [{"evidenceId": bound["evidenceId"], "sha256": bound["sha256"], "path": "docs/other.md"}],
        })
        self.assertEqual(res_path_conflict["status"], "rejected")
        self.assertEqual(res_path_conflict["errorCode"], "ID_CONFLICT")

    def test_inputs_is_completed_head_scoped_to_consuming_lineage(self):
        from company_harness_inputs import load_inputs
        store2 = HarnessStore(self.root / "lineage-store", create=True)
        store2.create_cycle({
            "cycleId": "exp-res", "explorationId": "exp-scope", "sequenceNumber": 1,
            "objective": "Exploration research", "workKind": "research", "artifactKind": "research",
            "scope": ["bounded"], "completionOrHandoff": "note",
        })
        att = store2.begin_attempt("exp-res", "exp-att-1", {"dispatchId": "owned"})
        ref = store2.bind_evidence("exp-res", "exp-doc", "exploration result", source={"attemptId": "exp-att-1"})
        ev = {"evidenceId": ref["evidenceId"], "sha256": ref["sha256"]}
        store2.submit(att["context"], "sub-exp", {"result": "completed", "unfinishedItems": [], "evidenceRefs": [ev], "primaryEvidenceId": ev["evidenceId"]})
        store2.finish_attempt(att["context"], {"outcome": "completed", "exitCode": 0}, writers_stopped=True, observation="ok")
        store2.close_cycle("exp-res", "close-exp", outcome="completed",
            verification={"writersStopped": True, "submittedVersionUnchanged": True, "attemptResults": ["exp-att-1"], "evidenceRefs": [ev], "checkedAt": runner.now()},
            continuation_decision={"allowed": True, "reason": "handoff_validated", "basis": {"governance": "verified"}, "checkedAt": runner.now()}, submission_id="sub-exp")
        # Under product scope, an exploration-only completed head is NOT a completed head for productId='product-1'.
        prod_loaded = load_inputs(store2, {"productId": "product-1", "inputRefs": [ev], "prerequisiteRefs": []})
        self.assertFalse(prod_loaded[0]["isCompletedHead"])
        # Under its own exploration scope, it IS a completed head.
        exp_loaded = load_inputs(store2, {"explorationId": "exp-scope", "inputRefs": [ev], "prerequisiteRefs": []})
        self.assertTrue(exp_loaded[0]["isCompletedHead"])

    def test_cross_attempt_reused_evidence_id_with_path_rejected_at_submit(self):
        first = self.store.bind_evidence(
            "formal-cycle",
            "shared-ev",
            "attempt-one-doc",
            source={"attemptId": "attempt-one"},
            media_type="text/markdown",
        )
        self.store.finish_attempt(self.context, {"outcome": "failed", "exitCode": 1}, writers_stopped=True, observation="done")
        self.store.begin_recovery("formal-cycle", "rec-cross", budget_seconds=60, reason="retry")
        attempt2 = self.store.begin_attempt("formal-cycle", "attempt-two", {"dispatchId": "owned-2"}, recovery_id="rec-cross")
        ws2 = self.root / "ws-cross-attempt"
        (ws2 / "docs").mkdir(parents=True, exist_ok=True)
        (ws2 / "docs/reused.md").write_text("attempt-two-content", encoding="utf-8")
        sock2 = self.root / "bridge-cross.sock"
        with running_bridge(sock2, self.store, attempt2["context"], "bound-token-2") as server:
            with patch.object(server, "live_workspace", return_value=ws2):
                rejected = request("submit", "sub-cross", {
                    "result": "completed",
                    "unfinishedItems": [],
                    "evidenceRefs": [{"evidenceId": "shared-ev", "sha256": first["sha256"], "path": "docs/reused.md"}],
                    "primaryEvidenceId": "shared-ev",
                }, socket_path=sock2, token="bound-token-2")
        self.assertEqual(rejected["status"], "rejected")
        self.assertEqual(rejected["errorCode"], "ID_CONFLICT")


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

    def input_contract(self, count, size=1):
        refs = []
        for number in range(count):
            ref = self.store.bind_evidence(self.cycle_id, 'input-' + str(size) + '-' + str(number), bytes([number]) * size,
                                          media_type='application/octet-stream')
            refs.append({key: ref[key] for key in ('evidenceId', 'sha256')})
        with self.store._transaction() as tx:
            cycle = self.store._cycle(tx, self.cycle_id)
            cycle['contract'].update(inputRefs=refs, prerequisiteRefs=refs)
            self.store._save_cycle(tx, cycle)
        return refs

    def test_invalid_input_packages_do_not_create_dispatch_intent_or_consume_budget_ack(self):
        from usage_lib import append_cycle_record, build_cycle_record, load_budget_config, resume_budget
        with patch.dict(os.environ, {'USAGE_HARD_LIMIT_TOKENS': '10'}):
            pause = self.root / '.auto-loop-budget-paused'
            record = build_cycle_record(cycle_id='prior-usage', cycle_number=1, started_at=runner.now(), ended_at=runner.now(),
                status='completed', exit_code=0, engine='codex', model='fixture', metadata_raw='{"input_tokens":10,"output_tokens":4}')
            append_cycle_record(self.root / 'logs/usage.jsonl', record, budget_config=load_budget_config(os.environ), pause_path=pause)
            self.assertTrue(resume_budget(pause))
            acknowledgement = pause.with_name(pause.name + '.resume')
            original_ack = acknowledgement.read_bytes()
            for count, size in ((17, 1), (9, 1024 * 1024)):
                with self.subTest(count=count, size=size):
                    self.input_contract(count, size)
                    before = self.store.snapshot()
                    with patch.object(runner.tempfile, 'mkdtemp', side_effect=AssertionError('validation must precede temp creation')):
                        with self.assertRaisesRegex(HarnessError, 'INPUT_PACKAGE_INVALID'):
                            runner.begin_attempt(self.store, self.root, self.cycle_id)
                    after = self.store.snapshot()
                    self.assertEqual(after['snapshotRevision'], before['snapshotRevision'])
                    self.assertEqual(after['cycles'][0]['attempts'], [])
                    self.assertIsNone(after['cycles'][0]['activeAttemptId'])
                    self.assertIsNone(after['cycles'][0]['startedAt'])
                    self.assertFalse((self.root / 'logs/usage.jsonl.pending').exists())
                    self.assertEqual(acknowledgement.read_bytes(), original_ack)
                    self.assertEqual(list((self.root / '.autonomous-company').glob('harness/attempt-*.json')), [])

    def test_input_materialization_failure_cleans_temp_before_dispatch_intent(self):
        self.input_contract(1)
        created, original = [], runner.tempfile.mkdtemp
        def owned_directory(**kwargs):
            path = original(**kwargs)
            created.append(Path(path))
            return path
        def fail_materialization(materials, directory):
            directory.mkdir()
            (directory / 'partial').write_bytes(b'partial package')
            raise OSError('injected package write failure')
        before = self.store.snapshot()['snapshotRevision']
        with patch.object(runner.tempfile, 'mkdtemp', side_effect=owned_directory), patch.object(runner, 'write_inputs', side_effect=fail_materialization):
            with self.assertRaisesRegex(OSError, 'package write failure'):
                runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.assertEqual(len(created), 1)
        self.assertFalse(created[0].exists())
        self.assertEqual(self.store.snapshot()['snapshotRevision'], before)
        self.assertIsNone(self.store.snapshot()['cycles'][0]['activeAttemptId'])
        self.assertFalse((self.root / 'logs/usage.jsonl.pending').exists())

    def test_boundary_input_package_repeated_refs_materialize_once_before_attempt(self):
        self.input_contract(16)
        manifest = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, manifest['temporary'], ignore_errors=True)
        inputs = Path(manifest['inputsDirectory'])
        index = json.loads((inputs / 'index.json').read_text())
        self.assertEqual(len(index), 16)
        self.assertEqual(len(list(inputs.iterdir())), 17)
        self.assertEqual(self.store.snapshot()['cycles'][0]['activeAttemptId'], manifest['context']['attemptId'])

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

    def test_fractional_normal_remainder_enters_recovery_without_resetting_its_budget(self):
        from usage_lib import recover_pending_cycle, load_budget_config
        tick = [100.0]
        self.store = HarnessStore(self.root, create=True, clock=lambda: tick[0], boot_id='test-boot')
        def stopped(manifest):
            self.store.finish_attempt(manifest['context'], {'outcome': 'failed', 'exitCode': 17},
                writers_stopped=True, observation='owned supervisor')
            recover_pending_cycle(self.root / 'logs/usage.jsonl', budget_config=load_budget_config({}),
                                  pause_path=self.root / '.auto-loop-budget-paused')
        first = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, first['temporary'], ignore_errors=True)
        deadline = self.store.snapshot()['cycles'][0]['deadline']
        tick[0] += 479.5
        stopped(first)
        with patch.dict(os.environ, {'COMPANY_HARNESS_RECOVERY_SECONDS': '60'}):
            recovery = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, recovery['temporary'], ignore_errors=True)
        self.assertTrue(recovery['recovery'])
        self.assertEqual(recovery['timeoutSeconds'], 60)
        self.assertEqual(self.store.snapshot()['cycles'][0]['deadline'], deadline)
        tick[0] += 59.5
        stopped(recovery)
        before = self.store.snapshot()
        with patch.dict(os.environ, {'COMPANY_HARNESS_RECOVERY_SECONDS': '60'}):
            with self.assertRaisesRegex(HarnessError, 'BUDGET_EXHAUSTED'):
                runner.begin_attempt(self.store, self.root, self.cycle_id)
        after = self.store.snapshot()
        self.assertEqual(after['snapshotRevision'], before['snapshotRevision'])
        self.assertEqual(len(after['cycles'][0]['recoveries']), 1)
        self.assertEqual(len(after['cycles'][0]['attempts']), 2)

    def test_trusted_actual_execution_failure_retries_and_keeps_failed_charge(self):
        manifest, metadata = self.stopped_material()
        failed = runner.finish_attempt(self.store, self.root, manifest['context']['attemptId'],
            {**metadata, 'exit_code': 17, 'status': 'error'}, {'cleanupFailed': False, 'supervisorOwner': 'owned-tree'})
        self.assertTrue(failed['validSubmission'])
        self.assertFalse(failed['actualSuccess'])
        self.assertEqual(failed['action'], 'retry')
        self.assertEqual(failed['error'], 'EXECUTION_FAILED')
        deadline = self.store.snapshot()['cycles'][0]['deadline']
        correction = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, correction['temporary'], ignore_errors=True)
        self.assertFalse(correction['recovery'])
        self.assertEqual(self.store.snapshot()['cycles'][0]['deadline'], deadline)
        records = read_usage_records(self.root / 'logs/usage.jsonl')[0]
        self.assertEqual(records[0]['status'], 'failed')
        self.assertEqual(records[0]['usage']['total_tokens'], 14)

    def test_voluntary_failed_result_with_normal_exit_is_a_legal_close(self):
        self.assert_voluntary_result_closes('failed')

    def test_voluntary_blocked_result_with_normal_exit_is_a_legal_close(self):
        self.assert_voluntary_result_closes('blocked')

    def assert_voluntary_result_closes(self, outcome):
        manifest, metadata = self.stopped_material(result=outcome)
        result = runner.finish_attempt(self.store, self.root, manifest['context']['attemptId'], metadata,
            {'cleanupFailed': False, 'supervisorOwner': 'owned-tree'})
        self.assertTrue(result['validSubmission'])
        self.assertTrue(result['actualSuccess'])
        self.assertEqual(result['action'], 'close')
        self.assertEqual(result['outcome'], outcome)
        self.assertEqual(runner.close_cycle(self.store, self.root, self.cycle_id, True)['outcome'], outcome)

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

    def stopped_material(self, result="completed", with_handoff=False, handoff_inputs=None):
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
                "scope": ["the unfinished research question"], "inputRefs": handoff_inputs if handoff_inputs is not None else [ref], "prerequisiteRefs": [],
                "completionOrHandoff": "research note", "timeClass": "regular"}})
            (docs / "handoff.json").write_text(plan)
            handoff = {"evidenceId": "handoff-v1", "sha256": hashlib.sha256(plan.encode()).hexdigest(), "path": "docs/handoff.json"}
            payload.update(handoffRef=handoff, primaryEvidenceId=ref["evidenceId"])
            payload["evidenceRefs"].append(handoff)
        versions = {"projects": "p", "docs": "d", "memories": "m"}
        self.store.submit_with_versions(manifest["context"], "accepted", payload, lambda _: versions)
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

    def test_oversized_next_contract_returns_same_cycle_correction_before_close(self):
        refs = []
        for number in range(17):
            evidence = self.store.bind_evidence(self.cycle_id, 'next-input-' + str(number), 'Closed input ' + str(number))
            refs.append({key: evidence[key] for key in ('evidenceId', 'sha256')})
        manifest, metadata = self.stopped_material(with_handoff=True, handoff_inputs=refs)
        result = runner.finish_attempt(self.store, self.root, manifest['context']['attemptId'], metadata,
            {'cleanupFailed': False, 'supervisorOwner': 'verified-tree'})
        self.assertEqual(result['action'], 'retry')
        self.assertFalse(result['validSubmission'])
        self.assertIn('INPUT_PACKAGE_INVALID', result['error'])
        cycle = self.store.snapshot()['cycles'][0]
        self.assertNotEqual(cycle['protocolState'], 'closed')
        self.assertIsNone(cycle['activeAttemptId'])
        self.assertTrue(cycle['attempts'][0]['writersStopped'])

    def test_lost_ack_retry_keeps_first_atomic_baseline_and_detects_unlisted_business_write(self):
        from isolation_workspace import fingerprint
        manifest = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, manifest['temporary'], ignore_errors=True)
        attempt_id = manifest['context']['attemptId']
        workspace = self.root / 'live-view'
        for name in ('projects', 'docs', 'memories'):
            (workspace / name).mkdir(parents=True)
        artifact = workspace / 'docs/result.txt'
        artifact.write_text('The declared primary evidence')
        extra = workspace / 'projects/unlisted-business.txt'
        extra.write_text('Before durable submit')
        payload = {'result': 'completed', 'unfinishedItems': [], 'evidenceRefs': [{
            'evidenceId': 'primary-version', 'path': 'docs/result.txt', 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()}]}
        with running_bridge(manifest['socket'], self.store, manifest['context'], manifest['token']) as server:
            original = server.dispatch
            def lose_ack(value):
                original(value)
                raise OSError('injected post-commit acknowledgement write failure')
            with patch.object(server, 'live_workspace', return_value=workspace), patch.object(server, 'dispatch', side_effect=lose_ack):
                first = request('submit', 'stable', payload, socket_path=manifest['socket'], token=manifest['token'])
            self.assertEqual(first['errorCode'], 'INVALID_REQUEST')
            accepted = self.store.snapshot()['cycles'][0]['submissions'][0]
            baseline = accepted['acceptanceVersions']
            self.assertEqual(baseline['projects'], fingerprint(workspace / 'projects'))
            extra.write_text('After durable submit, outside declared evidence')
            with patch.object(server, 'capture_versions', side_effect=AssertionError('replay must never resample')):
                retry = request('submit', 'stable', payload, socket_path=manifest['socket'], token=manifest['token'])
                conflict = request('submit', 'stable', {**payload, 'result': 'partial'}, socket_path=manifest['socket'], token=manifest['token'])
            self.assertEqual(retry['status'], 'accepted')
            self.assertEqual(conflict['errorCode'], 'ID_CONFLICT')
        restarted = HarnessStore(self.root, create=True)
        self.assertEqual(restarted.snapshot()['cycles'][0]['submissions'][0]['acceptanceVersions'], baseline)
        versions = {name: fingerprint(workspace / name) for name in ('projects', 'docs', 'memories')}
        # An obsolete or forged sidecar cannot replace the transaction's first baseline.
        runner.write_fact(runner.host_path(self.root, attempt_id + '.acceptance.json'), {'submissionId': 'stable', 'versions': versions})
        runner.write_fact(runner.host_path(self.root, attempt_id + '.collect.json'), {
            **{key: manifest['context'][key] for key in ('cycleId', 'attemptId', 'generation')},
            'collected': True, 'docsRoot': str(workspace / 'docs'), 'versions': versions})
        result = runner.finish_attempt(restarted, self.root, attempt_id, {'exit_code': 0, 'status': 'success'},
            {'cleanupFailed': False, 'supervisorOwner': 'owned-tree'})
        self.assertTrue(result['actualSuccess'])
        self.assertFalse(result['validSubmission'])
        self.assertIn('POST_SUBMISSION_CHANGE', result['error'])
        closed = runner.close_cycle(restarted, self.root, self.cycle_id, True)
        self.assertEqual(closed['outcome'], 'failed')

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

    def test_partial_head_feedback_and_completion_path_unblocks_downstream(self):
        from company_harness_quality import artifact_state, prepare_contract
        from company_harness_inputs import load_inputs, write_inputs
        # Seed a completed definition + passed review so prototype reaches visual_direction check.
        with self.store._transaction() as tx:
            c0 = self.store._cycle(tx, self.cycle_id)
            c0["contract"].update(workKind="definition", artifactKind="definition")
            c0["workKind"] = "definition"
            self.store._save_cycle(tx, c0)
        a0 = self.store.begin_attempt(self.cycle_id, "def-1", {"dispatchId": "owned"})
        def_ref = self.store.bind_evidence(self.cycle_id, "def-doc", "complete definition", source={"attemptId": "def-1"})
        def_ev = {"evidenceId": def_ref["evidenceId"], "sha256": def_ref["sha256"]}
        self.store.submit(a0["context"], "sub-def", {
            "result": "completed", "unfinishedItems": [], "evidenceRefs": [def_ev], "primaryEvidenceId": def_ev["evidenceId"],
        })
        self.store.finish_attempt(a0["context"], {"outcome": "completed", "exitCode": 0}, writers_stopped=True, observation="ok")
        self.store.close_cycle(self.cycle_id, "close-def", outcome="completed",
            verification={"writersStopped": True, "submittedVersionUnchanged": True, "attemptResults": ["def-1"], "evidenceRefs": [def_ev], "checkedAt": runner.now()},
            continuation_decision={"allowed": True, "reason": "handoff_validated", "basis": {"governance": "verified"}, "checkedAt": runner.now()}, submission_id="sub-def")
        runner.sync_identity(self.root, runner.row(self.store, self.cycle_id))
        rev_id = reserve_cycle(self.root, "", "rev-def", 2)["cycleId"]
        self.store.create_cycle({
            "cycleId": rev_id, "explorationId": self.identity["explorationId"], "sequenceNumber": 2,
            "objective": "Review definition", "workKind": "review", "artifactKind": "review",
            "scope": ["review def"], "completionOrHandoff": "done", "inputRefs": [def_ev], "prerequisiteRefs": [],
        })
        ar = self.store.begin_attempt(rev_id, "rev-def-1", {"dispatchId": "owned"})
        rev_ref = self.store.bind_evidence(rev_id, "rev-def-doc", "passed review", source={"attemptId": "rev-def-1"})
        rev_ev = {"evidenceId": rev_ref["evidenceId"], "sha256": rev_ref["sha256"]}
        self.store.submit(ar["context"], "sub-rev-def", {
            "result": "completed", "unfinishedItems": [], "evidenceRefs": [rev_ev], "primaryEvidenceId": rev_ev["evidenceId"],
            "review": {"targetRefs": [def_ev], "verdict": "passed", "issues": [], "qualityApplicability": ["visual_exploration", "prototype"]},
        })
        self.store.finish_attempt(ar["context"], {"outcome": "completed", "exitCode": 0}, writers_stopped=True, observation="ok")
        self.store.close_cycle(rev_id, "close-rev-def", outcome="completed",
            verification={"writersStopped": True, "submittedVersionUnchanged": True, "attemptResults": ["rev-def-1"], "evidenceRefs": [rev_ev], "checkedAt": runner.now()},
            quality_applicability=[{"artifactKind": "definition", "targetRef": def_ev, "verdict": "passed",
                                    "workKinds": ["visual_exploration", "prototype"], "reviewEvidenceRefs": [rev_ev]}],
            continuation_decision={"allowed": True, "reason": "handoff_validated", "basis": {"governance": "verified"}, "checkedAt": runner.now()},
            submission_id="sub-rev-def")
        runner.sync_identity(self.root, runner.row(self.store, rev_id))
        # Now run visual_exploration closing partial.
        vis_id = reserve_cycle(self.root, "", "partial-vis", 3)["cycleId"]
        self.store.create_cycle({
            "cycleId": vis_id, "explorationId": self.identity["explorationId"], "sequenceNumber": 3,
            "objective": "Visual exploration", "workKind": "visual_exploration", "artifactKind": "visual_direction",
            "scope": ["visuals"], "completionOrHandoff": "done", "inputRefs": [def_ev], "prerequisiteRefs": [rev_ev],
        })
        attempt = self.store.begin_attempt(vis_id, "partial-vis-1", {"dispatchId": "owned"})
        ref = self.store.bind_evidence(vis_id, "vis-partial-doc", "partial mockups", source={"attemptId": "partial-vis-1"})
        ev = {"evidenceId": ref["evidenceId"], "sha256": ref["sha256"]}
        self.store.submit(attempt["context"], "sub-partial", {
            "result": "partial", "unfinishedItems": ["mobile layout"], "evidenceRefs": [ev], "primaryEvidenceId": ev["evidenceId"],
        })
        self.store.finish_attempt(attempt["context"], {"outcome": "completed", "exitCode": 0}, writers_stopped=True, observation="ok")
        self.store.close_cycle(vis_id, "close-partial-vis", outcome="partial",
            verification={"writersStopped": True, "submittedVersionUnchanged": True, "attemptResults": ["partial-vis-1"], "evidenceRefs": [ev], "checkedAt": runner.now()},
            continuation_decision={"allowed": True, "reason": "handoff_validated", "basis": {"governance": "verified"}, "checkedAt": runner.now()}, submission_id="sub-partial")
        runner.sync_identity(self.root, runner.row(self.store, vis_id))
        scope = {"productId": None, "explorationId": self.identity["explorationId"]}
        state = artifact_state(self.store, scope)
        self.assertNotIn("visual_direction", state["heads"])
        self.assertEqual(state["incomplete"][0]["artifactKind"], "visual_direction")
        self.assertEqual(state["incomplete"][0]["requiredProductionWorkKind"], "visual_exploration")
        with self.assertRaisesRegex(HarnessError, "visual_exploration"):
            prepare_contract(self.store, {
                "objective": "Try prototype", "workKind": "prototype", "scope": ["proto"],
                "completionOrHandoff": "done", "inputRefs": [def_ev, ev], "prerequisiteRefs": [rev_ev],
            }, scope)
        with self.assertRaisesRegex(HarnessError, "visual_exploration"):
            prepare_contract(self.store, {
                "objective": "Try revision", "workKind": "revision", "revisesKind": "visual_direction",
                "scope": ["rev"], "completionOrHandoff": "done", "inputRefs": [ev], "prerequisiteRefs": [],
            }, scope)
        loaded = load_inputs(self.store, {"inputRefs": [ev], "prerequisiteRefs": []})
        self.assertEqual(loaded[0]["sourceOutcome"], "partial")
        self.assertFalse(loaded[0]["isCompletedHead"])
        inputs_dir = self.root / "probe-inputs"
        write_inputs(loaded, inputs_dir)
        idx = json.loads((inputs_dir / "index.json").read_text())
        self.assertFalse(idx[0]["isCompletedHead"])
        self.assertEqual(idx[0]["sourceOutcome"], "partial")
        # Completing via original production workKind establishes the completed head.
        c2_id = reserve_cycle(self.root, "", "complete-vis", 4)["cycleId"]
        c2 = self.store.create_cycle({
            "cycleId": c2_id, "explorationId": self.identity["explorationId"], "sequenceNumber": 4,
            "objective": "Finish visual exploration", "workKind": "visual_exploration", "artifactKind": "visual_direction",
            "scope": ["complete"], "completionOrHandoff": "done", "inputRefs": [def_ev, ev], "prerequisiteRefs": [rev_ev],
        })
        a2 = self.store.begin_attempt(c2_id, "complete-vis-1", {"dispatchId": "owned"})
        ref2 = self.store.bind_evidence(c2_id, "vis-complete-doc", "complete mockups", source={"attemptId": "complete-vis-1"})
        ev2 = {"evidenceId": ref2["evidenceId"], "sha256": ref2["sha256"]}
        self.store.submit(a2["context"], "sub-complete", {
            "result": "completed", "unfinishedItems": [], "evidenceRefs": [ev2], "primaryEvidenceId": ev2["evidenceId"],
        })
        self.store.finish_attempt(a2["context"], {"outcome": "completed", "exitCode": 0}, writers_stopped=True, observation="ok")
        self.store.close_cycle(c2_id, "close-complete-vis", outcome="completed",
            verification={"writersStopped": True, "submittedVersionUnchanged": True, "attemptResults": ["complete-vis-1"], "evidenceRefs": [ev2], "checkedAt": runner.now()},
            continuation_decision={"allowed": True, "reason": "handoff_validated", "basis": {"governance": "verified"}, "checkedAt": runner.now()}, submission_id="sub-complete")
        state2 = artifact_state(self.store, scope)
        self.assertEqual(state2["heads"]["visual_direction"]["evidenceId"], ev2["evidenceId"])
        self.assertEqual(state2["incomplete"], [])
        self.assertTrue(load_inputs(self.store, {"inputRefs": [ev2], "prerequisiteRefs": []})[0]["isCompletedHead"])

    def test_bridge_submit_synchronously_rejects_missing_review_prereq_and_allows_retry(self):
        # Seed completed definition head + passed independent review covering prototype.
        with self.store._transaction() as tx:
            c0 = self.store._cycle(tx, self.cycle_id)
            c0["contract"].update(workKind="definition", artifactKind="definition")
            c0["workKind"] = "definition"
            self.store._save_cycle(tx, c0)
        a0 = self.store.begin_attempt(self.cycle_id, "def-live-1", {"dispatchId": "owned"})
        def_ref = self.store.bind_evidence(self.cycle_id, "def-live-doc", "complete definition", source={"attemptId": "def-live-1"})
        def_ev = {"evidenceId": def_ref["evidenceId"], "sha256": def_ref["sha256"]}
        self.store.submit(a0["context"], "sub-def-live", {
            "result": "completed", "unfinishedItems": [], "evidenceRefs": [def_ev], "primaryEvidenceId": def_ev["evidenceId"],
        })
        self.store.finish_attempt(a0["context"], {"outcome": "completed", "exitCode": 0}, writers_stopped=True, observation="ok")
        self.store.close_cycle(self.cycle_id, "close-def-live", outcome="completed",
            verification={"writersStopped": True, "submittedVersionUnchanged": True, "attemptResults": ["def-live-1"], "evidenceRefs": [def_ev], "checkedAt": runner.now()},
            continuation_decision={"allowed": True, "reason": "handoff_validated", "basis": {"governance": "verified"}, "checkedAt": runner.now()}, submission_id="sub-def-live")
        runner.sync_identity(self.root, runner.row(self.store, self.cycle_id))

        rev_id = reserve_cycle(self.root, "", "rev-def-live", 2)["cycleId"]
        self.store.create_cycle({
            "cycleId": rev_id, "explorationId": self.identity["explorationId"], "sequenceNumber": 2,
            "objective": "Review definition", "workKind": "review", "artifactKind": "review",
            "scope": ["review def"], "completionOrHandoff": "passed",
            "inputRefs": [def_ev], "reviewRequirement": {"independent": True, "targetRefs": [def_ev]},
        })
        arev = self.store.begin_attempt(rev_id, "rev-live-1", {"dispatchId": "owned"})
        rev_ref = self.store.bind_evidence(rev_id, "rev-def-live-doc", "passed review", source={"attemptId": "rev-live-1"})
        rev_ev = {"evidenceId": rev_ref["evidenceId"], "sha256": rev_ref["sha256"]}
        self.store.submit(arev["context"], "sub-rev-live", {
            "result": "completed", "unfinishedItems": [], "evidenceRefs": [rev_ev], "primaryEvidenceId": rev_ev["evidenceId"],
            "review": {"verdict": "passed", "targetRefs": [def_ev], "issues": [], "qualityApplicability": ["visual_exploration", "prototype"]},
        })
        self.store.finish_attempt(arev["context"], {"outcome": "completed", "exitCode": 0}, writers_stopped=True, observation="ok")
        self.store.close_cycle(rev_id, "close-rev-live", outcome="completed",
            verification={"writersStopped": True, "submittedVersionUnchanged": True, "attemptResults": ["rev-live-1"], "evidenceRefs": [rev_ev], "checkedAt": runner.now()},
            continuation_decision={"allowed": True, "reason": "handoff_validated", "basis": {"governance": "verified"}, "checkedAt": runner.now()}, submission_id="sub-rev-live",
            quality_applicability=[{"artifactKind": "definition", "targetRef": def_ev, "verdict": "passed",
                "workKinds": ["visual_exploration", "prototype"], "issues": [], "source": "independent_review",
                "reviewerAttemptId": "rev-live-1", "reviewCycleId": rev_id, "reviewEvidenceRefs": [rev_ev]}])
        runner.sync_identity(self.root, runner.row(self.store, rev_id))

        vis_id = reserve_cycle(self.root, "", "vis-live", 3)["cycleId"]
        self.store.create_cycle({
            "cycleId": vis_id, "explorationId": self.identity["explorationId"], "sequenceNumber": 3,
            "objective": "Explore visual direction", "workKind": "visual_exploration", "artifactKind": "visual_direction",
            "scope": ["visual"], "completionOrHandoff": "done", "inputRefs": [def_ev], "prerequisiteRefs": [rev_ev],
        })
        vis_attempt = self.store.begin_attempt(vis_id, "vis-live-1", {"dispatchId": "owned"})
        ctx = vis_attempt["context"]
        ws = self.root / "live-vis-ws"
        for folder in ("docs/harness", "projects", "memories"):
            (ws / folder).mkdir(parents=True, exist_ok=True)
        vis_file = ws / "docs/vis.md"
        vis_file.write_text("visual direction A", encoding="utf-8")
        vis_ev_ref = {"evidenceId": "vis-doc-live", "path": "docs/vis.md", "sha256": hashlib.sha256(vis_file.read_bytes()).hexdigest()}
        handoff_file = ws / "docs/harness/handoff.json"
        handoff_payload = {
            "nextContract": {
                "objective": "Build prototype", "workKind": "prototype", "scope": ["proto"],
                "completionOrHandoff": "proto done", "inputRefs": [def_ev, vis_ev_ref], "prerequisiteRefs": [],
            }
        }
        handoff_file.write_text(json.dumps(handoff_payload), encoding="utf-8")
        hoff_ref = {"evidenceId": "vis-hoff-live", "path": "docs/harness/handoff.json", "sha256": hashlib.sha256(handoff_file.read_bytes()).hexdigest()}
        sock = self.root / "vis-live.sock"
        with running_bridge(sock, self.store, ctx, "vis-token") as server:
            with patch.object(server, "live_workspace", return_value=ws):
                bad_payload = {"result": "completed", "unfinishedItems": [], "evidenceRefs": [vis_ev_ref, hoff_ref],
                               "primaryEvidenceId": "vis-doc-live", "handoffRef": hoff_ref}
                rejected = request("submit", "bad-sub", bad_payload, socket_path=sock, token="vis-token")
                self.assertEqual(rejected["status"], "rejected")
                self.assertEqual(rejected["errorCode"], "REVIEW_REQUIRED")
                self.assertEqual(rejected["field"], "definition")
                self.assertIn(rev_ev["evidenceId"], rejected.get("detail", ""))
                self.assertEqual(self.store.snapshot()["cycles"][-1]["submissions"], [])

                handoff_payload["nextContract"]["prerequisiteRefs"] = [rev_ev]
                handoff_file.write_text(json.dumps(handoff_payload), encoding="utf-8")
                fixed_hoff = {"evidenceId": "vis-hoff-live", "path": "docs/harness/handoff.json",
                              "sha256": hashlib.sha256(handoff_file.read_bytes()).hexdigest()}
                missing_vis_rev = request("submit", "missing-vis-rev", {
                    **bad_payload, "evidenceRefs": [vis_ev_ref, fixed_hoff], "handoffRef": fixed_hoff,
                }, socket_path=sock, token="vis-token")
                self.assertEqual(missing_vis_rev["status"], "rejected")
                self.assertEqual(missing_vis_rev["errorCode"], "REVIEW_REQUIRED")
                self.assertEqual(missing_vis_rev["field"], "visual_direction")
                self.assertIn("workKind=review", missing_vis_rev.get("detail", ""))

                review_payload = {
                    "nextContract": {
                        "objective": "Independent review of visual direction", "workKind": "review",
                        "scope": ["review visual"], "completionOrHandoff": "review passed",
                        "inputRefs": [vis_ev_ref], "prerequisiteRefs": [],
                    }
                }
                handoff_file.write_text(json.dumps(review_payload), encoding="utf-8")
                review_hoff = {"evidenceId": "vis-hoff-live", "path": "docs/harness/handoff.json",
                               "sha256": hashlib.sha256(handoff_file.read_bytes()).hexdigest()}
                accepted = request("submit", "fixed-sub", {
                    **bad_payload, "evidenceRefs": [vis_ev_ref, review_hoff], "handoffRef": review_hoff,
                }, socket_path=sock, token="vis-token")
                self.assertEqual(accepted["status"], "accepted")

    def test_bridge_recovery_submit_reports_offending_protocol_file_detail(self):
        a0 = self.store.begin_attempt(self.cycle_id, "rec-first-1", {"dispatchId": "owned"})
        self.store.finish_attempt(a0["context"], {"outcome": "failed", "exitCode": 1}, writers_stopped=True, observation="fail")
        self.store.begin_recovery(self.cycle_id, "rec-1", budget_seconds=300, reason="recover")
        rec_attempt = self.store.begin_attempt(self.cycle_id, "rec-att-1", {"dispatchId": "owned"}, recovery_id="rec-1")
        ws = self.root / "live-rec-ws"
        proto_dir = ws / ".company-harness-protocol" / "rec-att-1"
        for folder in (proto_dir, ws / "docs", ws / "projects", ws / "memories"):
            folder.mkdir(parents=True, exist_ok=True)
        existing = ws / "docs/existing.md"
        existing.write_text("existing partial artifact", encoding="utf-8")
        hoff = proto_dir / "handoff.json"
        hoff.write_text(json.dumps({"nextContract": {"objective": "Continue", "workKind": "research", "scope": ["s"], "completionOrHandoff": "d", "inputRefs": [], "prerequisiteRefs": []}}), encoding="utf-8")
        (proto_dir / "progress.json").write_text('{"transient": true}', encoding="utf-8")
        refs = [
            {"evidenceId": "existing-doc", "path": "docs/existing.md", "sha256": hashlib.sha256(existing.read_bytes()).hexdigest()},
            {"evidenceId": "rec-hoff", "path": ".company-harness-protocol/rec-att-1/handoff.json", "sha256": hashlib.sha256(hoff.read_bytes()).hexdigest()},
        ]
        sock = self.root / "rec-live.sock"
        with running_bridge(sock, self.store, rec_attempt["context"], "rec-token") as server:
            with patch.object(server, "live_workspace", return_value=ws):
                res = request("submit", "rec-bad", {
                    "result": "partial", "unfinishedItems": ["pending"], "evidenceRefs": refs,
                    "primaryEvidenceId": "existing-doc", "handoffRef": refs[1],
                }, socket_path=sock, token="rec-token")
                self.assertEqual(res["status"], "rejected")
                self.assertEqual(res["errorCode"], "PROTOCOL_SCOPE")
                self.assertIn("progress.json", res.get("detail", ""))

    def test_repeated_identical_rejection_escalates_to_human(self):
        with patch.dict(os.environ, {"COMPANY_HARNESS_CORRECTIONS": "1", "COMPANY_HARNESS_MAX_SAME_ERROR": "2",
                                     "AUTONOMOUS_COMPANY_LOCK_PID": str(os.getpid())}):
            m1 = runner.begin_attempt(self.store, self.root, self.cycle_id)
            self.addCleanup(shutil.rmtree, m1["temporary"], ignore_errors=True)
            a1 = m1["context"]["attemptId"]
            runner.write_fact(self.root / m1["collectRelative"], {**m1["context"], "collected": True, "versions": {}})
            r1 = runner.finish_attempt(self.store, self.root, a1, {"status": "success", "exit_code": 0, "input_tokens": 5, "output_tokens": 2},
                {"cleanupFailed": False, "supervisorOwner": "owned"})
            self.assertEqual(r1["action"], "retry")
            m2 = runner.begin_attempt(self.store, self.root, self.cycle_id)
            self.addCleanup(shutil.rmtree, m2["temporary"], ignore_errors=True)
            a2 = m2["context"]["attemptId"]
            runner.write_fact(self.root / m2["collectRelative"], {**m2["context"], "collected": True, "versions": {}})
            r2 = runner.finish_attempt(self.store, self.root, a2, {"status": "success", "exit_code": 0, "input_tokens": 5, "output_tokens": 2},
                {"cleanupFailed": False, "supervisorOwner": "owned"})
            self.assertEqual(r2["action"], "human")
            self.assertEqual(r2["repeatedErrorCount"], 2)
            self.assertIn("Repeated identical rejection", r2["guidance"])

        # Also when CORRECTIONS=3 and MAX_SAME_ERROR=2, the 2nd identical error escalates to 'human' immediately.
        with tempfile.TemporaryDirectory(prefix="harness-same-err-") as tmp:
            troot = Path(tmp)
            (troot / "memories").mkdir()
            shutil.copy2(ROOT / "memories/consensus.template.md", troot / "memories/consensus.md")
            tstore = HarnessStore(troot, create=True)
            cid2 = reserve_cycle(troot, "", "same-err-early", 1)["cycleId"]
            runner.prepare(tstore, troot, cid2)
            with patch.dict(os.environ, {"COMPANY_HARNESS_CORRECTIONS": "3", "COMPANY_HARNESS_MAX_SAME_ERROR": "2",
                                         "AUTONOMOUS_COMPANY_LOCK_PID": str(os.getpid())}):
                for idx in range(2):
                    m = runner.begin_attempt(tstore, troot, cid2)
                    self.addCleanup(shutil.rmtree, m["temporary"], ignore_errors=True)
                    runner.write_fact(troot / m["collectRelative"], {**m["context"], "collected": True, "versions": {}})
                    res = runner.finish_attempt(tstore, troot, m["context"]["attemptId"],
                        {"status": "success", "exit_code": 0, "input_tokens": 5, "output_tokens": 2},
                        {"cleanupFailed": False, "supervisorOwner": "owned"})
                    self.assertEqual(res["action"], "retry" if idx == 0 else "human")
                self.assertEqual(len(tstore.snapshot()["cycles"][-1]["attempts"]), 2)

    def test_usage_mirror_reports_self_coverage_when_tokens_measured(self):
        manifest, metadata = self.stopped_material(with_handoff=True)
        runner.finish_attempt(self.store, self.root, manifest["context"]["attemptId"], metadata,
            {"cleanupFailed": False, "supervisorOwner": "verified-tree"})
        attempt = self.store.snapshot()["cycles"][0]["attempts"][0]
        self.assertEqual(attempt["calls"][0]["coverage"], "self")
        self.assertTrue(attempt["usage"]["observedFieldsComplete"]["totalTokens"])
        self.assertFalse(attempt["usage"]["totalTokensComplete"])

    def test_reconcile_crash_closes_orphaned_cycle_after_writers_stopped(self):
        with patch.dict(os.environ, {"AUTONOMOUS_COMPANY_LOCK_PID": str(os.getpid())}):
            manifest = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, manifest["temporary"], ignore_errors=True)
        with self.assertRaisesRegex(HarnessError, "UNFINISHED_HARNESS"):
            runner.recover_stopped_cycles(self.store, self.root)
        # Active process blocks crash reconciliation.
        live_proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
        self.addCleanup(lambda: (live_proc.terminate(), live_proc.wait(timeout=5)) if live_proc.poll() is None else None)
        live_start = runner.process_start(live_proc.pid)
        runner.write_fact(Path(manifest["ready"]), {"pid": live_proc.pid, "processStart": live_start})
        with self.assertRaisesRegex(HarnessError, "WRITERS_UNCONFIRMED"):
            runner.reconcile_crash(self.store, self.root)
        live_proc.terminate()
        live_proc.wait(timeout=5)
        cli = subprocess.run([sys.executable, str(ROOT / "scripts/core/company_harness_runner.py"),
                              "--root", str(self.root), "reconcile-crash", "--reason", "test_power_loss"],
                             capture_output=True, text=True)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        payload = json.loads(cli.stdout)
        self.assertEqual(payload["reconciledCycles"], [self.cycle_id])
        cycle = self.store.snapshot()["cycles"][0]
        self.assertEqual(cycle["protocolState"], "closed")
        self.assertEqual(cycle["outcome"], "interrupted")
        self.assertFalse(cycle["continuationDecision"]["allowed"])
        self.assertEqual(cycle["continuationDecision"]["reason"], "crash_reconciled_human_review")
        startup = subprocess.run([sys.executable, str(ROOT / "scripts/core/company_harness_runner.py"),
                                  "--root", str(self.root), "startup"], capture_output=True, text=True)
        self.assertEqual(startup.returncode, 0, startup.stderr)

    def test_abort_unstarted_and_approve_recovery_resume_without_replaying_crash(self):
        aborted = runner.abort_unstarted_cycle(self.store, self.root, self.cycle_id, "governance_admission_blocked")
        self.assertEqual(aborted["outcome"], "failed")
        self.assertEqual(runner.close_cycle(self.store, self.root, self.cycle_id, True)["outcome"], "failed")

        # Seed prior completed cycle with validated nextContract handoff, then simulate crash on cycle 2 -> reconcile-crash -> approve-recovery.
        with tempfile.TemporaryDirectory(prefix="harness-rec-approve-") as tmp:
            troot = Path(tmp)
            (troot / "memories").mkdir()
            (troot / "scripts/core").mkdir(parents=True)
            shutil.copy2(ROOT / "memories/consensus.template.md", troot / "memories/consensus.md")
            shutil.copy2(ROOT / "scripts/core/consensus-guard.sh", troot / "scripts/core/consensus-guard.sh")
            shutil.copy2(ROOT / "scripts/core/consensus-format.py", troot / "scripts/core/consensus-format.py")
            shutil.copy2(ROOT / "scripts/core/project-context.py", troot / "scripts/core/project-context.py")
            tstore = HarnessStore(troot, create=True)
            id1 = reserve_cycle(troot, "", "good-cycle", 1)["cycleId"]
            runner.prepare(tstore, troot, id1)
            a1 = tstore.begin_attempt(id1, "good-att-1", {"dispatchId": "owned"})
            doc1 = tstore.bind_evidence(id1, "ev-good", "good research note", source={"attemptId": "good-att-1"})
            ev_good = {"evidenceId": doc1["evidenceId"], "sha256": doc1["sha256"]}
            hoff_data = {"nextContract": {"objective": "Follow-up direction", "workKind": "direction", "scope": ["bounded"], "inputRefs": [ev_good], "prerequisiteRefs": [], "completionOrHandoff": "direction doc"}}
            hoff1 = tstore.bind_evidence(id1, "hoff-good", json.dumps(hoff_data), source={"attemptId": "good-att-1"}, media_type="application/json")
            ev_hoff = {"evidenceId": hoff1["evidenceId"], "sha256": hoff1["sha256"], "path": "docs/harness/hoff.json"}
            tstore.submit(a1["context"], "sub-good", {"result": "completed", "unfinishedItems": [], "evidenceRefs": [ev_good, ev_hoff], "primaryEvidenceId": ev_good["evidenceId"], "handoffRef": ev_hoff})
            tstore.finish_attempt(a1["context"], {"outcome": "completed", "exitCode": 0}, writers_stopped=True, observation="ok")
            tstore.close_cycle(id1, "close-good", outcome="completed",
                verification={"writersStopped": True, "submittedVersionUnchanged": True, "attemptResults": ["good-att-1"], "evidenceRefs": [ev_good, ev_hoff], "checkedAt": runner.now()},
                continuation_decision={"allowed": True, "reason": "handoff_validated", "basis": {"governance": "verified"}, "checkedAt": runner.now()}, submission_id="sub-good")
            runner.sync_identity(troot, runner.row(tstore, id1))
            exp_scope = {"productId": None, "explorationId": tstore.snapshot()["cycles"][0]["explorationId"]}
            id2 = reserve_cycle(troot, "", "crashed-cycle", 2)["cycleId"]
            tstore.create_cycle({
                "cycleId": id2, "explorationId": exp_scope["explorationId"], "sequenceNumber": 2, "runCycleNumber": 2,
                "objective": "Crashed step", "workKind": "direction", "artifactKind": "direction", "scope": ["dir"],
                "inputRefs": [ev_good], "prerequisiteRefs": [], "completionOrHandoff": "dir doc",
            })
            tstore.begin_attempt(id2, "crashed-att-1", {"dispatchId": "owned"})
            runner.reconcile_crash(tstore, troot)
            with self.assertRaisesRegex(HarnessError, "CONTINUATION_BLOCKED"):
                runner.reassess_continuation(tstore, troot, exp_scope)
            runner.approve_recovery(tstore, troot, "rev-tok-123")
            runner.reassess_continuation(tstore, troot, exp_scope)
            planned = runner.next_contract(tstore, exp_scope, root=troot)
            self.assertEqual(planned["workKind"], "direction")
            self.assertEqual(planned["objective"], "Follow-up direction")

    def test_begin_prepared_attempt_failure_rolls_back_active_attempt_and_manifests(self):
        env = dict(os.environ, AUTONOMOUS_COMPANY_LOCK_PID=str(os.getpid()))
        with patch.dict(os.environ, env), \
             patch.object(runner, "begin_cycle", side_effect=OSError("ledger write failed")):
            with self.assertRaisesRegex(OSError, "ledger write failed"):
                runner.begin_attempt(self.store, self.root, self.cycle_id)
        cycle = runner.row(self.store, self.cycle_id)
        self.assertIsNone(cycle["activeAttemptId"])
        self.assertEqual(len(cycle["attempts"]), 1)
        self.assertEqual(cycle["attempts"][0]["actualResult"]["outcome"], "not_started")
        self.assertEqual(cycle["attempts"][0]["actualResult"]["providerInvoked"], False)
        self.assertFalse(any(runner.host_path(self.root, "").glob("*.launch.json")))

        # Failure while writing .prompt.json also rolls back activeAttemptId and cleans host files.
        orig_write = runner.write_fact
        def fail_prompt(path, value):
            if str(path).endswith(".prompt.json"):
                raise OSError("prompt write failed")
            return orig_write(path, value)
        self.store.begin_recovery(self.cycle_id, "rec-prompt-fail", budget_seconds=60, reason="retry")
        with patch.dict(os.environ, env), patch.object(runner, "write_fact", side_effect=fail_prompt):
            with self.assertRaisesRegex(OSError, "prompt write failed"):
                runner.begin_attempt(self.store, self.root, self.cycle_id)
        cycle2 = runner.row(self.store, self.cycle_id)
        self.assertIsNone(cycle2["activeAttemptId"])
        self.assertEqual(len(cycle2["attempts"]), 2)
        self.assertEqual(cycle2["attempts"][1]["actualResult"]["outcome"], "not_started")
        self.assertFalse(any(runner.host_path(self.root, "").glob("*.prompt.json")))

    def test_recover_stopped_cycles_closes_zero_attempt_unstarted_result(self):
        runner.write_fact(
            runner.host_path(self.root, self.cycle_id + ".result.json"),
            {"cycleId": self.cycle_id, "outcome": "not_started", "providerInvoked": False,
             "submissionId": None, "validSubmission": False, "evidenceRefs": []},
        )
        runner.recover_stopped_cycles(self.store, self.root)
        cycle = runner.row(self.store, self.cycle_id)
        self.assertEqual(cycle["protocolState"], "closed")
        self.assertEqual(cycle["outcome"], "failed")

        # Also recovers a cycle that has a rolled-back not_started attempt + providerInvoked=False .result.json.
        id_rb = reserve_cycle(self.root, "", "rolledback-cycle", 2)["cycleId"]
        self.store.create_cycle({
            "cycleId": id_rb, "explorationId": self.store.snapshot()["cycles"][0]["explorationId"],
            "sequenceNumber": 2, "runCycleNumber": 2, "objective": "Rolled back cycle",
            "workKind": "research", "artifactKind": "research", "scope": ["s"],
            "inputRefs": [], "prerequisiteRefs": [], "completionOrHandoff": "note",
        })
        att_rb = self.store.begin_attempt(id_rb, "att-rb-1", {"dispatchId": "owned"})
        self.store.finish_attempt(
            att_rb["context"], {"outcome": "not_started", "exitCode": None, "providerInvoked": False},
            writers_stopped=True, observation={"type": "prepare_rollback", "checkedAt": runner.now()},
        )
        runner.write_fact(
            runner.host_path(self.root, id_rb + ".result.json"),
            {"cycleId": id_rb, "outcome": "not_started", "providerInvoked": False,
             "submissionId": None, "validSubmission": False, "evidenceRefs": []},
        )
        runner.recover_stopped_cycles(self.store, self.root)
        closed_rb = runner.row(self.store, id_rb)
        self.assertEqual(closed_rb["protocolState"], "closed")
        self.assertEqual(closed_rb["outcome"], "failed")

    def test_approve_recovery_atomic_failure_and_next_contract_uses_bound_contract(self):
        with tempfile.TemporaryDirectory(prefix="harness-bound-rec-") as tmp:
            troot = Path(tmp)
            (troot / "memories").mkdir()
            (troot / "scripts/core").mkdir(parents=True)
            shutil.copy2(ROOT / "memories/consensus.template.md", troot / "memories/consensus.md")
            tstore = HarnessStore(troot, create=True)
            id1 = reserve_cycle(troot, "", "crashed-initial", 1)["cycleId"]
            tstore.create_cycle({
                "cycleId": id1, "explorationId": "exp-bound-rec", "sequenceNumber": 1, "runCycleNumber": 1,
                "objective": "Initial objective", "workKind": "objective_selection", "artifactKind": "objective",
                "scope": ["topic"], "inputRefs": [], "prerequisiteRefs": [], "completionOrHandoff": "topic note",
            })
            tstore.begin_attempt(id1, "crashed-att-1", {"dispatchId": "owned"})
            reconciled = runner.reconcile_crash(tstore, troot)
            self.assertEqual(reconciled["nextContract"]["workKind"], "objective_selection")

            # If planning raises inside approve_recovery, continuationDecision stays disallowed.
            with patch.object(runner, "_plan_recovery_contract", side_effect=HarnessError("HANDOFF_MISSING")):
                with self.assertRaisesRegex(HarnessError, "HANDOFF_MISSING"):
                    runner.approve_recovery(tstore, troot, "rev-tok-fail")
            self.assertFalse(runner.row(tstore, id1)["continuationDecision"]["allowed"])

            # Once approved, boundNextContract is preserved even if consensus/env change afterward.
            approved = runner.approve_recovery(tstore, troot, "rev-tok-ok")
            self.assertEqual(approved["nextContract"]["workKind"], "objective_selection")
            consensus = troot / "memories/consensus.md"
            consensus.write_text(consensus.read_text().replace("- (none)", "- Mutated later objective"), encoding="utf-8")
            with patch.dict(os.environ, {"COMPANY_HARNESS_INITIAL_WORK_KIND": "research"}):
                planned = runner.next_contract(tstore, {"productId": None, "explorationId": "exp-bound-rec"}, root=troot)
            self.assertEqual(planned["workKind"], "objective_selection")

    def test_retry_error_signature_normalizes_attempt_hex_and_trips_max_same_error(self):
        import company_harness_quality as hquality
        attempts = []
        docs = self.root / "collected-sig/docs"
        docs.mkdir(parents=True, exist_ok=True)
        content = "body"
        (docs / "res.md").write_text(content, encoding="utf-8")
        ev_ref = {"evidenceId": "ev-sig", "sha256": hashlib.sha256(content.encode()).hexdigest(), "path": "docs/res.md"}
        hoff_text = json.dumps({"nextContract": {"objective": "Next", "workKind": "research", "scope": ["s"], "inputRefs": [ev_ref], "prerequisiteRefs": [], "completionOrHandoff": "note"}})
        (docs / "hoff.json").write_text(hoff_text, encoding="utf-8")
        hoff_ref = {"evidenceId": "hoff-sig", "sha256": hashlib.sha256(hoff_text.encode()).hexdigest(), "path": "docs/hoff.json"}
        versions = {"projects": "p", "docs": "d", "memories": "m"}
        runner.prepare(self.store, self.root, self.cycle_id)
        for idx, suffix in enumerate(("0123abcd", "deadbeef"), start=1):
            att_id = f"attempt-{suffix}"
            rec_id = None if idx == 1 else f"rec-{idx}"
            if idx > 1:
                self.store.begin_recovery(self.cycle_id, rec_id, budget_seconds=60, reason="retry")
            att = self.store.begin_attempt(self.cycle_id, att_id, {"dispatchId": "owned"}, recovery_id=rec_id)
            ev_i = {"evidenceId": f"ev-sig-{idx}", "sha256": ev_ref["sha256"], "path": "docs/res.md"}
            hoff_i = {"evidenceId": f"hoff-sig-{idx}", "sha256": hoff_ref["sha256"], "path": "docs/hoff.json"}
            sub = self.store.submit_with_versions(att["context"], f"sub-{idx}", {
                "result": "completed" if idx == 1 else "partial", "unfinishedItems": [], "evidenceRefs": [ev_i, hoff_i],
                "primaryEvidenceId": ev_i["evidenceId"], "handoffRef": hoff_i,
            }, lambda _: versions)
            self.assertEqual(sub["status"], "accepted", sub)
            collect_rel = f".autonomous-company/harness/{att_id}.collect.json"
            runner.write_fact(runner.host_path(self.root, att_id + ".json"), {
                "root": str(self.root), "context": att["context"], "collectRelative": collect_rel,
                "temporary": str(self.root / f"tmp-{att_id}"),
            })
            runner.write_fact(self.root / collect_rel, {
                **{k: att["context"][k] for k in ("cycleId", "attemptId", "generation")},
                "collected": True, "docsRoot": str(docs), "versions": versions,
            })
            with patch.object(
                hquality, "prepare_contract",
                side_effect=HarnessError("EVIDENCE_VERSION_MISMATCH", f"evidence-{att_id}-" + (chr(ord("a") + idx - 1) * 64) + "-1234567890ab"),
            ):
                res = runner.finish_attempt(
                    self.store,
                    self.root,
                    att_id,
                    {"status": "success", "exit_code": 0, "providerInvoked": True},
                    {"cleanupFailed": False, "supervisorOwner": "verified-tree"},
                )
            attempts.append(res)
        self.assertEqual(attempts[1].get("repeatedErrorCount"), 2)
        self.assertEqual(attempts[1].get("action"), "human")
        self.assertIn("Repeated identical rejection", attempts[1].get("guidance", ""))


@unittest.skipUnless(sys.platform == 'linux', 'Live pre-dispatch ownership uses real Linux processes')
class PreDispatchTests(unittest.TestCase):
    setUp = RunnerTests.setUp

    def prepared(self, recovery=False):
        if recovery:
            self.store.begin_recovery(self.cycle_id, 'fixture-recovery', budget_seconds=60, reason='Owned fixture recovery')
        self.environment = dict(os.environ, AUTONOMOUS_COMPANY_LOCK_PID=str(os.getpid()))
        with patch.dict(os.environ, self.environment):
            manifest = runner.begin_attempt(self.store, self.root, self.cycle_id)
        self.addCleanup(shutil.rmtree, manifest['temporary'], ignore_errors=True)
        self.bridge = subprocess.Popen([sys.executable, str(ROOT / 'scripts/core/company_harness_bridge.py'),
            '--root', str(self.root), '--manifest', str(runner.host_path(self.root, manifest['context']['attemptId'] + '.json'))],
            env=self.environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(self.stop_bridge)
        deadline = time.monotonic() + 5
        while not Path(manifest['ready']).exists() and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue(Path(manifest['ready']).exists())
        return manifest

    def stop_bridge(self):
        if self.bridge.poll() is None:
            self.bridge.terminate()
        self.bridge.wait(timeout=5)
        for stream in (self.bridge.stdout, self.bridge.stderr):
            if stream and not stream.closed:
                stream.close()

    def expired(self):
        with self.store._transaction() as tx:
            cycle = self.store._cycle(tx, self.cycle_id)
            timer = cycle['recoveries'][0]['timer'] if cycle['recoveries'] else cycle['budgetTimer']
            timer['consumedSeconds'] = timer['limitSeconds']
            self.store._save_cycle(tx, cycle)

    def control(self, action, manifest, *, injected_crash=False):
        args = ['--root', str(self.root), action, '--attempt', manifest['context']['attemptId'], '--bridge-pid', str(self.bridge.pid)]
        if injected_crash:
            code = "import sys;sys.path.insert(0,sys.argv[1]);sys.argv=sys.argv[1:];import company_harness_runner as r;r.complete_unstarted=lambda *a:(_ for _ in ()).throw(OSError('crash after proof'));r.main()"
            command = [sys.executable, '-c', code, str(ROOT / 'scripts/core'), *args]
        else:
            command = [sys.executable, str(ROOT / 'scripts/core/company_harness_runner.py'), *args]
        return subprocess.run(command, env=self.environment, capture_output=True, text=True)

    def test_live_unstarted_settlement_has_real_log_known_empty_calls_and_idempotent_receipt(self):
        manifest = self.prepared()
        self.expired()
        self.stop_bridge()
        result = self.control('unstarted', manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'retry')
        snapshot = self.store.snapshot()
        attempt = snapshot['cycles'][0]['attempts'][0]
        self.assertTrue(attempt['writersStopped'])
        self.assertEqual(attempt['actualResult']['outcome'], 'not_started')
        self.assertEqual(attempt['calls'], [])
        self.assertEqual(attempt['usage']['totalTokens'], 0)
        self.assertTrue(attempt['usage']['totalTokensComplete'])
        self.assertTrue(attempt['usage']['costComplete'])
        self.assertFalse((self.root / 'logs/usage.jsonl.pending').exists())
        records = read_usage_records(self.root / 'logs/usage.jsonl')[0]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['cost_usd'], 0)
        self.assertFalse(records[0]['provider_invoked'])
        log = self.root / 'logs' / (attempt['attemptId'] + '.log')
        self.assertIn('providerInvoked=false', log.read_text())
        self.assertEqual(self.control('unstarted', manifest).returncode, 0)
        self.assertEqual(self.store.snapshot()['snapshotRevision'], snapshot['snapshotRevision'])
        self.assertEqual(len(read_usage_records(self.root / 'logs/usage.jsonl')[0]), 1)

    def test_old_prepared_or_dispatch_intent_does_not_infer_no_writer_or_zero_usage(self):
        manifest = self.prepared()
        marked = self.control('dispatch', manifest)
        self.assertEqual(marked.returncode, 0, marked.stderr)
        self.expired()
        self.stop_bridge()
        refused = self.control('unstarted', manifest)
        self.assertIn('DISPATCH_UNCONFIRMED', refused.stderr)
        with self.assertRaisesRegex(HarnessError, 'UNFINISHED_HARNESS'):
            runner.recover_stopped_cycles(self.store, self.root)
        attempt = self.store.snapshot()['cycles'][0]['attempts'][0]
        self.assertFalse(attempt['writersStopped'])
        self.assertIsNone(attempt['usage']['totalTokens'])
        self.assertFalse(attempt['usage']['totalTokensComplete'])
        self.assertTrue((self.root / 'logs/usage.jsonl.pending').exists())
        self.assertEqual(read_usage_records(self.root / 'logs/usage.jsonl')[0], [])

    def test_dispatch_gate_returns_current_seconds_and_persists_that_timeout(self):
        manifest = self.prepared()
        with self.store._transaction() as tx:
            cycle = self.store._cycle(tx, self.cycle_id)
            cycle['budgetTimer'].update(consumedSeconds=120, anchor=time.monotonic())
            self.store._save_cycle(tx, cycle)
        marked = self.control('dispatch', manifest)
        self.assertEqual(marked.returncode, 0, marked.stderr)
        seconds = int(marked.stdout.strip())
        self.assertTrue(355 <= seconds <= 360, seconds)
        self.assertLess(seconds, manifest['timeoutSeconds'])
        launch = runner.read_fact(runner.host_path(self.root, manifest['context']['attemptId'] + '.launch.json'))
        self.assertEqual(launch['phase'], 'provider_dispatch_intent')
        self.assertEqual(launch['timeoutSeconds'], seconds)

    def test_dispatch_gate_fractional_exhaustion_leaves_prepared_for_live_settlement(self):
        manifest = self.prepared()
        with self.store._transaction() as tx:
            cycle = self.store._cycle(tx, self.cycle_id)
            cycle['budgetTimer'].update(consumedSeconds=479.5, anchor=time.monotonic())
            self.store._save_cycle(tx, cycle)
        refused = self.control('dispatch', manifest)
        self.assertIn('BUDGET_EXHAUSTED', refused.stderr)
        launch = runner.read_fact(runner.host_path(self.root, manifest['context']['attemptId'] + '.launch.json'))
        self.assertEqual(launch['phase'], 'prepared')
        self.stop_bridge()
        settled = self.control('unstarted', manifest)
        self.assertEqual(settled.returncode, 0, settled.stderr)
        self.assertEqual(self.store.snapshot()['cycles'][0]['attempts'][0]['actualResult']['outcome'], 'not_started')

    def test_current_bridge_and_matching_worker_and_stale_generation_refuse_zero_settlement(self):
        manifest = self.prepared()
        self.expired()
        self.assertIn('WRITERS_UNCONFIRMED', self.control('unstarted', manifest).stderr)
        self.stop_bridge()
        path = self.root / '.autonomous-company/isolation' / self.identity['identityId'] / 'active-run.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'pid': os.getpid(), 'processStart': runner.process_start(os.getpid()),
            'cycle': self.cycle_id, 'attemptId': manifest['context']['attemptId']}))
        self.assertIn('WRITERS_UNCONFIRMED', self.control('unstarted', manifest).stderr)
        path.unlink()
        self.store.claim_controller('replacement-controller')
        self.assertIn('STALE_GENERATION', self.control('unstarted', manifest).stderr)
        self.assertTrue((self.root / 'logs/usage.jsonl.pending').exists())
        self.assertEqual(read_usage_records(self.root / 'logs/usage.jsonl')[0], [])

    def test_only_durable_live_cancellation_proof_replays_after_crash_without_dispatch(self):
        manifest = self.prepared()
        self.expired()
        self.stop_bridge()
        self.assertNotEqual(self.control('unstarted', manifest, injected_crash=True).returncode, 0)
        launch = runner.read_fact(runner.host_path(self.root, manifest['context']['attemptId'] + '.launch.json'))
        self.assertEqual(launch['phase'], 'cancelled')
        self.assertFalse(self.store.snapshot()['cycles'][0]['attempts'][0]['writersStopped'])
        with self.assertRaisesRegex(HarnessError, 'UNFINISHED_HARNESS'):
            runner.recover_stopped_cycles(HarnessStore(self.root, create=True), self.root)
        snapshot = self.store.snapshot()
        self.assertTrue(snapshot['cycles'][0]['attempts'][0]['writersStopped'])
        self.assertEqual(snapshot['cycles'][0]['attempts'][0]['usage']['totalTokens'], 0)
        self.assertEqual(len(snapshot['cycles'][0]['attempts']), 1)
        with self.assertRaisesRegex(HarnessError, 'UNFINISHED_HARNESS'):
            runner.recover_stopped_cycles(HarnessStore(self.root, create=True), self.root)
        self.assertEqual(self.store.snapshot()['snapshotRevision'], snapshot['snapshotRevision'])
        self.assertEqual(len(read_usage_records(self.root / 'logs/usage.jsonl')[0]), 1)

    def test_expired_recovery_preparation_does_not_allocate_another_recovery_budget(self):
        manifest = self.prepared(recovery=True)
        self.expired()
        self.stop_bridge()
        result = self.control('unstarted', manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        with patch.dict(os.environ, self.environment), self.assertRaisesRegex(HarnessError, 'BUDGET_EXHAUSTED'):
            runner.begin_attempt(self.store, self.root, self.cycle_id)
        cycle = self.store.snapshot()['cycles'][0]
        self.assertEqual(len(cycle['recoveries']), 1)
        self.assertEqual(len(cycle['attempts']), 1)
        self.assertEqual(cycle['recoveries'][0]['budgetSeconds'], 60)
        closed = runner.close_cycle(self.store, self.root, self.cycle_id, True)
        self.assertEqual(closed['outcome'], 'failed')
        self.assertFalse(closed['continuationAllowed'])


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

    def test_voluntary_failed_submission_with_new_p1_triggers_governance_blocked(self):
        from isolation_workspace import TEMPLATES
        with tempfile.TemporaryDirectory(prefix="harness-p1-vol-fail-") as temporary:
            root = Path(temporary)
            for name in TEMPLATES:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
            shutil.copytree(ROOT / "scripts/core", root / "scripts/core", dirs_exist_ok=True)
            shutil.copytree(ROOT / "memories", root / "memories")
            source, binary = root / "fake.c", root / "fake-codex"
            program = '''import json,pathlib,sys
consensus=pathlib.Path('/workspace/memories/consensus.md')
body=consensus.read_text()
if '## Next Action' not in body:
    body += chr(10)+'## Next Action'+chr(10)+'Bounded synthetic task'+chr(10)
if '## Company State' not in body:
    body += chr(10)+'## Company State'+chr(10)+'Governance boundary fixture'+chr(10)
body=body.replace('## Priority Issues','## Priority Issues'+chr(10)+'- [ ] P1: voluntary failed blocker',1)
consensus.write_text(body)
sys.path.insert(0,'/workspace/scripts/core')
from company_harness_client import request
assert request('submit','voluntary-failed-p1',{'result':'failed','unfinishedItems':['blocker']})['status']=='accepted'
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':2,'output_tokens':3}}),flush=True)
'''
            source.write_text('#include <unistd.h>\n#include <string.h>\n#include <stdio.h>\nint main(int argc,char**argv){if(argc>1&&!strcmp(argv[1],"--version")){puts("p1-fixture");return 0;}char *args[]={"/usr/bin/python3","-c",' + json.dumps(program) + ',0};execv(args[0],args);return 1;}\n')
            subprocess.run(["cc", str(source), "-o", str(binary)], check=True, capture_output=True)
            env = dict(os.environ, COMPANY_HARNESS_ENABLED="1", COMPANY_HARNESS_CORRECTIONS="0",
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
                    self.assertEqual((root / ".auto-loop-paused").read_text(), "PAUSE_REASON=unresolved_p1\n")
                    self.assertIn("- [ ] P1: voluntary failed blocker", (root / "memories/consensus.md").read_text())
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

    def test_accepted_nonzero_exit_uses_correction_and_keeps_actual_failed_charge(self):
        self.run_owned_loop(False, accepted_failure=True)

    def test_accepted_nonzero_exit_uses_bounded_recovery_and_keeps_actual_failed_charge(self):
        self.run_owned_loop(True, accepted_failure=True)

    def test_live_bridge_preparation_expiry_settles_unstarted_then_uses_readonly_recovery(self):
        self.run_owned_loop(True, pre_dispatch_expiry='before_prompt')

    def test_live_dispatch_gate_expiry_settles_unstarted_then_uses_readonly_recovery(self):
        self.run_owned_loop(True, pre_dispatch_expiry='before_dispatch')

    def run_owned_loop(self, recovery, budget_resume=False, accepted_failure=False, pre_dispatch_expiry=False):
        from isolation_workspace import TEMPLATES
        with tempfile.TemporaryDirectory(prefix="harness-kernel-") as temporary:
            root = Path(temporary)
            for name in TEMPLATES:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
            shutil.copytree(ROOT / "scripts/core", root / "scripts/core", dirs_exist_ok=True)
            shutil.copytree(ROOT / "memories", root / "memories")
            if pre_dispatch_expiry:
                loop = root / 'scripts/core/company_harness_loop.sh'
                injection = '''        if [ "$recovery" = 0 ] && [ ! -f "$PROJECT_DIR/.predispatch-injected" ]; then
            python3 - "$PROJECT_DIR" "$CURRENT_PRODUCT_CYCLE_ID" <<'PY'
import pathlib,sys,time
sys.path.insert(0,str(pathlib.Path(sys.argv[1])/'scripts/core'))
from company_harness import HarnessStore
from product_identity import read_state
s=HarnessStore(sys.argv[1],create=True)
root=pathlib.Path(sys.argv[1]);owner=read_state(root)['cycles'][sys.argv[2]]['identityId']
scoped=root/'.autonomous-company/isolation'/owner
(scoped/'docs').mkdir(parents=True,exist_ok=True)
(scoped/'docs/correction-marker').write_text('pre-dispatch fixture artifact')
body=(root/'memories/consensus.md').read_text()
if '## Next Action' not in body:body+=chr(10)+'## Next Action'+chr(10)+'Continue the one bounded task'+chr(10)
if '## Company State' not in body:body+=chr(10)+'## Company State'+chr(10)+'Deterministic isolation fixture only'+chr(10)
(scoped/'consensus.md').write_text(body)
with s._transaction() as tx:
    c=s._cycle(tx,sys.argv[2]);c['budgetTimer']['consumedSeconds']=478.5;c['budgetTimer']['anchor']=time.monotonic();s._save_cycle(tx,c)
PY
            touch "$PROJECT_DIR/.predispatch-injected"
            sleep 2
        fi
'''
                needle = '        harness_prompt=' if pre_dispatch_expiry == 'before_prompt' else '        if ! CYCLE_TIMEOUT_SECONDS='
                self.assertEqual(loop.read_text().count(needle), 1)
                loop.write_text(loop.read_text().replace(needle, injection + needle))
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
    plan=pathlib.Path('/workspace/logs/recovery-plan.json')
    plan.write_text(json.dumps({'contract':{'objective':'Research one concrete customer problem','workKind':'research','scope':['one customer problem'],'completionOrHandoff':'research note'},'inputs':[],'prerequisites':[]}))
    import subprocess
    generated=json.loads(subprocess.check_output(['python3','/workspace/scripts/core/company_harness_handoff.py','--plan','logs/recovery-plan.json','--primary',marker.relative_to('/workspace').as_posix()]))
    assert target==pathlib.Path('/workspace')/generated['handoffPath']
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
    plan=pathlib.Path('/workspace/logs/normal-plan.json')
    plan.write_text(json.dumps({'contract':{'objective':'Research one concrete customer problem','workKind':'research','scope':['one customer problem'],'timeClass':'regular','completionOrHandoff':'research note'},'inputs':[{'evidence':'docs/synthetic-binary.bin'}],'prerequisites':[]}))
    import subprocess
    generated=json.loads(subprocess.check_output(['python3','/workspace/scripts/core/company_harness_handoff.py','--plan','logs/normal-plan.json','--primary','docs/selection.txt','--evidence','docs/synthetic-binary.bin']))
    target=pathlib.Path('/workspace')/generated['handoffPath']
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
            if accepted_failure:
                program = program.replace("marker.write_text('first attempt had no submission')", """marker.write_text('first accepted attempt later failed')
    primary,_=material(marker)
    assert request('submit','accepted-before-failure',{'result':'completed','unfinishedItems':[],'evidenceRefs':[primary]})['status']=='accepted'
    print(json.dumps({'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':4}}),flush=True)
    raise SystemExit(17)""")
                program = program.replace("('Selected bounded research question','first attempt had no submission')",
                    "('Selected bounded research question','first attempt had no submission','first accepted attempt later failed')")
            if pre_dispatch_expiry:
                program = program.replace("('Selected bounded research question','first attempt had no submission')",
                    "('Selected bounded research question','first attempt had no submission','pre-dispatch fixture artifact')")
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
                    self.assertEqual(len(snapshot["cycles"]), 2, output.read_text() + (root / 'logs/auto-loop.log').read_text()[-5000:] +
                        str([runner.read_fact(path) for path in (root / '.autonomous-company/harness').glob('*.finish.json')]) +
                        '\n'.join(path.read_text(errors='replace')[-3000:] for path in (root / 'logs').glob('attempt-*.log')))
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
                    self.assertEqual(sum(r["usage"]["total_tokens"] for r in records), 28 if budget_resume or pre_dispatch_expiry else 42)
                    self.assertTrue(all(r["record_role"] == "harness_attempt" for r in records))
                    self.assertEqual(sum(c["usage"]["totalTokens"] for c in snapshot["cycles"]), 28 if budget_resume or pre_dispatch_expiry else 42)
                    self.assertTrue(all(not c["usage"]["totalTokensComplete"] for c in snapshot["cycles"]))
                    if accepted_failure:
                        first = snapshot['cycles'][0]['attempts'][0]
                        self.assertEqual(first['actualResult']['exitCode'], 17)
                        self.assertEqual(first['actualResult']['outcome'], 'failed')
                        self.assertEqual(records[0]['cycle_id'], first['attemptId'])
                        self.assertEqual(records[0]['status'], 'failed')
                        self.assertEqual(records[0]['usage']['total_tokens'], 14)
                        result = runner.read_fact(runner.host_path(root, first['attemptId'] + '.finish.json'))
                        self.assertTrue(result['validSubmission'])
                        self.assertFalse(result['actualSuccess'])
                        self.assertEqual(result['action'], 'retry')
                        self.assertIn('EXECUTION_FAILED', result['error'])
                    if pre_dispatch_expiry:
                        first = snapshot['cycles'][0]['attempts'][0]
                        self.assertEqual(first['actualResult']['outcome'], 'not_started')
                        self.assertFalse(first['actualResult']['providerInvoked'])
                        self.assertEqual(first['calls'], [])
                        self.assertEqual(first['usage']['totalTokens'], 0)
                        self.assertTrue(first['usage']['totalTokensComplete'])
                        self.assertIn('providerInvoked=false', (root / 'logs' / (first['attemptId'] + '.log')).read_text())
                        self.assertEqual(records[0]['source']['type'], 'host_pre_dispatch_cancel')
                finally:
                    (root / ".auto-loop-stop").touch()
                    if process.poll() is None:
                        process.send_signal(signal.SIGTERM)
                    process.wait(timeout=15)


@unittest.skipUnless(sys.platform == "linux", "Linux host bridge and shell checks")
class AntiSpinAndTopicTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="harness-a2-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "memories").mkdir()
        shutil.copy2(ROOT / "memories/consensus.template.md", self.root / "memories/consensus.md")
        self.store = HarnessStore(self.root, create=True)

    def test_initial_contract_smart_entry_for_human_override_active_project_and_env(self):
        scope = {"productId": None, "explorationId": "exp-a2"}
        self.assertEqual(runner.next_contract(self.store, scope, root=self.root)["workKind"], "objective_selection")
        self.assertEqual(runner.next_contract(self.store, scope, root=self.root, project="projects/demo")["workKind"], "research")

        consensus = self.root / "memories/consensus.md"
        consensus.write_text(
            consensus.read_text().replace("- (none)", "- Build an offline Markdown diagram studio"),
            encoding="utf-8",
        )
        self.assertEqual(runner.next_contract(self.store, scope, root=self.root)["workKind"], "direction")

        with patch.dict(os.environ, {"COMPANY_HARNESS_INITIAL_WORK_KIND": "research"}):
            self.assertEqual(runner.next_contract(self.store, scope, root=self.root)["workKind"], "research")
        with patch.dict(os.environ, {"COMPANY_HARNESS_INITIAL_WORK_KIND": "invalid_kind"}):
            with self.assertRaisesRegex(HarnessError, "INVALID_CONFIG"):
                runner.next_contract(self.store, scope, root=self.root)

    def test_bridge_status_exposes_progression_state_and_submit_enforces_anti_spin(self):
        identity = reserve_cycle(self.root, "", "a2-bridge", 1)
        cid = identity["cycleId"]
        runner.prepare(self.store, self.root, cid)
        with self.store._transaction() as tx:
            c0 = self.store._cycle(tx, cid)
            c0["contract"].update(workKind="objective_selection", artifactKind="objective")
            c0["workKind"] = "objective_selection"
            self.store._save_cycle(tx, c0)
        attempt = self.store.begin_attempt(cid, "a2-att-1", {"dispatchId": "owned"})
        ws = self.root / "ws"
        for folder in ("docs/harness", "projects", "memories"):
            (ws / folder).mkdir(parents=True, exist_ok=True)
        res_file = ws / "docs/sel.md"
        res_file.write_text("selected research topic", encoding="utf-8")
        res_ref = {"evidenceId": "sel-doc", "path": "docs/sel.md", "sha256": hashlib.sha256(res_file.read_bytes()).hexdigest()}
        hoff_file = ws / "docs/harness/handoff.json"
        hoff_file.write_text(json.dumps({
            "nextContract": {
                "objective": "Chain another selection", "workKind": "objective_selection",
                "scope": ["still picking"], "completionOrHandoff": "picked",
                "inputRefs": [], "prerequisiteRefs": [],
            }
        }), encoding="utf-8")
        hoff_ref = {"evidenceId": "hoff-doc", "path": "docs/harness/handoff.json", "sha256": hashlib.sha256(hoff_file.read_bytes()).hexdigest()}
        sock = self.root / "a2-bridge.sock"
        with running_bridge(sock, self.store, attempt["context"], "a2-token") as server:
            with patch.object(server, "live_workspace", return_value=ws):
                st = request("status", socket_path=sock, token="a2-token")
                self.assertIn("progressionState", st)
                self.assertEqual(st["progressionState"]["stagnationLevel"], "none")
                self.assertEqual(st["progressionState"]["nextMilestone"], "direction")

                rejected = request("submit", "bad-spin", {
                    "result": "completed", "unfinishedItems": [], "evidenceRefs": [res_ref, hoff_ref],
                    "primaryEvidenceId": "sel-doc", "handoffRef": hoff_ref,
                }, socket_path=sock, token="a2-token")
                self.assertEqual(rejected["status"], "rejected")
                self.assertEqual(rejected["errorCode"], "SPIN_GUARD")
                self.assertIn("objective_selection", rejected.get("detail", ""))

    def test_attempt_prompt_includes_cli_quick_ref_and_progression_advisory(self):
        exp = "exp-prompt"
        for seq in range(1, 4):
            cid = f"res-cycle-{seq}"
            self.store.create_cycle({
                "cycleId": cid, "explorationId": exp, "sequenceNumber": seq,
                "objective": f"Research {seq}", "workKind": "research", "artifactKind": "research",
                "scope": ["bounded"], "completionOrHandoff": "note",
            })
            att = self.store.begin_attempt(cid, f"att-{seq}", {"dispatchId": "owned"})
            ref = self.store.bind_evidence(cid, f"ev-{seq}", f"content {seq}", source={"attemptId": f"att-{seq}"})
            ev = {"evidenceId": ref["evidenceId"], "sha256": ref["sha256"]}
            self.store.submit(att["context"], f"sub-{seq}", {"result": "completed", "unfinishedItems": [], "evidenceRefs": [ev], "primaryEvidenceId": ev["evidenceId"]})
            self.store.finish_attempt(att["context"], {"outcome": "completed", "exitCode": 0}, writers_stopped=True, observation="ok")
            self.store.close_cycle(cid, f"close-{seq}", outcome="completed",
                verification={"writersStopped": True, "submittedVersionUnchanged": True, "attemptResults": [f"att-{seq}"], "evidenceRefs": [ev], "checkedAt": runner.now()},
                continuation_decision={"allowed": True, "reason": "handoff_validated", "basis": {"governance": "verified"}, "checkedAt": runner.now()}, submission_id=f"sub-{seq}")

        target_cid = "cycle-warn"
        self.store.create_cycle({
            "cycleId": target_cid, "explorationId": exp, "sequenceNumber": 4, "runCycleNumber": 4,
            "objective": "Converge topic", "workKind": "research", "artifactKind": "research",
            "scope": ["converge"], "completionOrHandoff": "direction",
        })
        manifest = runner.begin_attempt(self.store, self.root, target_cid)
        self.addCleanup(shutil.rmtree, manifest["temporary"], ignore_errors=True)
        prompt = runner.read_fact(runner.host_path(self.root, manifest["context"]["attemptId"] + ".prompt.json"))["prompt"]
        self.assertIn("CLI Quick Reference", prompt)
        self.assertIn("Current progression & anti-spin state:", prompt)
        self.assertIn("ANTI-SPIN ADVISORY: STAGNATION (warning)", prompt)
        self.assertIn("Compare 2-3 bounded feasible candidates", prompt)

    def test_auto_loop_harness_default_interval_is_5_and_honors_override(self):
        script = (ROOT / "scripts/core/auto-loop.sh").read_text(encoding="utf-8")
        marker = 'if [ -z "${LOOP_INTERVAL:-}" ]; then'
        start = script.index(marker)
        snippet = script[start:script.index("\nfi\n", start) + 4]
        for extra_env, expected in (
            ({"COMPANY_HARNESS_ENABLED": "1"}, "5"),
            ({"COMPANY_HARNESS_ENABLED": "1", "LOOP_INTERVAL": ""}, "5"),
            ({"COMPANY_HARNESS_ENABLED": "0", "LOOP_INTERVAL": ""}, "30"),
            ({"COMPANY_HARNESS_ENABLED": "0"}, "30"),
            ({"COMPANY_HARNESS_ENABLED": "1", "LOOP_INTERVAL": "0"}, "0"),
            ({"COMPANY_HARNESS_ENABLED": "1", "LOOP_INTERVAL": "17"}, "17"),
        ):
            env = {k: v for k, v in os.environ.items() if k != "LOOP_INTERVAL"}
            env.update(extra_env)
            out = subprocess.check_output(["bash", "-c", snippet + '\nprintf "%s" "$LOOP_INTERVAL"'], env=env, text=True)
            self.assertEqual(out, expected)
        # Legacy soft-timeout remains enabled only when COMPANY_HARNESS_ENABLED != 1.
        timeout_marker = 'elif [ "$CYCLE_TIMED_OUT" -eq 1 ]; then'
        tstart = script.index(timeout_marker)
        tsnippet = script[tstart:script.index("\n    elif [", tstart)]
        self.assertIn('if [ "$COMPANY_HARNESS_ENABLED" != 1 ] && consensus_changed_since_backup && validate_consensus; then', tsnippet)


if __name__ == "__main__":
    unittest.main()
