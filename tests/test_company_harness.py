"""Isolated protocol facts and crash/retry boundaries; no services or models."""
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/core"))
from company_harness import HarnessError, HarnessStore


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.tick = 100.0
        self.store = self.open()
        self.contract = {"cycleId": "cycle-existing-1", "productId": "stable-product",
            "sequenceNumber": 17, "objective": "Draft the product definition", "workKind": "draft"}
        self.store.create_cycle(self.contract)

    def open(self, boot="boot-one"):
        return HarnessStore(self.root, create=True, clock=lambda: self.tick, boot_id=boot,
                            utc_now=lambda: "2026-10-22T12:00:00+00:00")

    def start(self, attempt="attempt-1", **kwargs):
        return self.store.begin_attempt(self.contract["cycleId"], attempt,
            {"runtimeId": "r1", "dispatchId": "dispatch-1", "requestId": "q1"}, **kwargs)["context"]

    def finish(self, context, outcome="completed"):
        return self.store.finish_attempt(context, {"outcome": outcome, "exitCode": 0 if outcome == "completed" else 1},
            writers_stopped=True, observation={"executionTree": "verified-terminated", "dispatchId": "dispatch-1"})

    def evidence(self, evidence_id="definition-v1", content="Actual draft"):
        row = self.store.bind_evidence(self.contract["cycleId"], evidence_id, content)
        return {"evidenceId": row["evidenceId"], "sha256": row["sha256"]}

    def submit(self, context, submission="submission-1", refs=None, result="completed"):
        return self.store.submit(context, submission, {"result": result, "evidenceRefs": refs or [], "unfinishedItems": []})

    def verification(self, refs=None):
        cycle = self.store.snapshot()["cycles"][0]
        return {"writersStopped": True, "attemptResults": [a["attemptId"] for a in cycle["attempts"]],
            "evidenceRefs": refs or [], "submittedVersionUnchanged": True, "checkedAt": "2026-10-22T12:00:00+00:00"}

    def report(self, revision=1, title="Progress"):
        return {"reportRevision": revision, "title": title, "summary": "Recorded real progress", "reportedPhase": "planning"}

    def close(self, outcome="completed", refs=None, submission="submission-1", **kwargs):
        return self.store.close_cycle(self.contract["cycleId"], "close-1", outcome=outcome,
            verification=self.verification(refs), submission_id=submission, **kwargs)

    def test_missing_read_does_not_create_and_existing_reader_cannot_write(self):
        other = self.root / "missing"
        self.assertEqual(HarnessStore(other).snapshot()["cycles"], [])
        self.assertFalse(other.exists())
        reader = HarnessStore(self.root)
        self.assertEqual(reader.snapshot()["cycles"][0]["sequenceNumber"], 17)
        with self.assertRaisesRegex(HarnessError, "READ_ONLY"):
            reader.claim_controller("new")

    def test_late_old_cycle_usage_preserves_creation_order_and_current_cycle(self):
        context = self.start()
        self.finish(context, outcome="failed")
        self.close(outcome="failed", submission=None)
        self.store.create_cycle({**self.contract, "cycleId": "cycle-2", "sequenceNumber": 18})
        self.store.record_usage(self.contract["cycleId"], context["attemptId"], {
            "callId": "late-provider", "coverage": "unknown", "cost": None,
            "inputTokens": 5, "outputTokens": 2, "source": {"type": "late-provider"}})
        snapshot = self.store.snapshot()
        self.assertEqual([c["cycleId"] for c in snapshot["cycles"]], [self.contract["cycleId"], "cycle-2"])
        self.assertEqual(snapshot["currentCycleId"], "cycle-2")

    def test_compact_and_catalog_reads_preserve_metadata_without_event_or_call_history(self):
        context = self.start()
        self.store.publish_progress(context, 'report', self.report())
        self.store.record_event(context, 1, {'kind': 'report', 'text': 'x' * 3000})
        self.store.record_usage(self.contract['cycleId'], context['attemptId'], {
            'callId': 'known', 'coverage': 'unknown', 'cost': 1, 'inputTokens': 3, 'outputTokens': 2})
        original = self.store.snapshot()
        compact = self.store.snapshot(compact=True)
        catalog = self.store.snapshot(catalog=True)
        attempt = compact['cycles'][0]['attempts'][0]
        self.assertNotIn('events', attempt)
        self.assertNotIn('calls', attempt)
        self.assertEqual(compact['cycles'][0]['report'], original['cycles'][0]['report'])
        self.assertEqual(compact['cycles'][0]['usage']['totalTokens'], 5)
        self.assertNotIn('usage', catalog['cycles'][0])
        self.assertNotIn('report', catalog['cycles'][0]['attempts'][0])
        self.assertEqual(self.store.snapshot(cycle_ids=[])['cycles'], [])
        self.assertEqual(original['snapshotRevision'], self.store.snapshot()['snapshotRevision'])

    def test_submit_ack_loss_replay_survives_restart_without_revision_change(self):
        context, refs = self.start(), [self.evidence()]
        first = self.submit(context, refs=refs)
        revision = self.store.snapshot()["snapshotRevision"]
        self.store = self.open()
        self.assertEqual(self.submit(context, refs=refs), first)
        self.assertEqual(self.store.snapshot()["snapshotRevision"], revision)
        self.assertEqual(first["status"], "accepted")
        self.assertEqual(self.store.snapshot()["cycles"][0]["protocolState"], "submitted")
        with self.assertRaisesRegex(HarnessError, "ID_CONFLICT"):
            self.submit(context, refs=refs, result="failed")

    def test_rejections_are_persistent_and_different_context_cannot_replay(self):
        context = self.start()
        first = self.submit(context)
        self.assertEqual(first["errorCode"], "EVIDENCE_MISSING")
        self.assertEqual(self.submit(context), first)
        forged = copy.deepcopy(context)
        forged["ownership"]["dispatchId"] = "other"
        with self.assertRaisesRegex(HarnessError, "ID_CONFLICT"):
            self.submit(forged)
        self.assertEqual(self.submit(forged, submission="other")["errorCode"], "OWNER_MISMATCH")

    def test_close_requires_writer_quiescence_actual_results_and_evidence(self):
        context, refs = self.start(), [self.evidence()]
        self.submit(context, refs=refs)
        with self.assertRaisesRegex(HarnessError, "WRITERS_UNCONFIRMED"):
            self.close(refs=refs)
        with self.assertRaisesRegex(HarnessError, "WRITERS_UNCONFIRMED"):
            self.store.finish_attempt(context, {"outcome": "completed"}, writers_stopped=False, observation={})
        self.finish(context)
        with self.assertRaisesRegex(HarnessError, "EVIDENCE_UNCONFIRMED"):
            self.close()
        self.close(refs=refs)
        cycle = self.store.snapshot()["cycles"][0]
        self.assertEqual(cycle["outcome"], "completed")
        self.assertFalse(cycle["continuationDecision"]["allowed"])
        self.assertEqual(cycle["qualityApplicability"], [])

    def test_close_replay_survives_crash_and_late_submission_cannot_overwrite(self):
        context, refs = self.start(), [self.evidence()]
        receipt = self.submit(context, refs=refs)
        self.finish(context)
        closed = self.close(refs=refs)
        self.store = self.open()
        revision = self.store.snapshot()["snapshotRevision"]
        self.assertEqual(self.close(refs=refs), closed)
        self.assertEqual(self.store.snapshot()["snapshotRevision"], revision)
        self.assertEqual(self.submit(context, refs=refs), receipt)
        self.assertEqual(self.submit(context, submission="late", result="failed")["errorCode"], "CYCLE_CLOSED")
        with self.assertRaisesRegex(HarnessError, "CYCLE_CLOSED"):
            self.close(outcome="failed", refs=refs)

    def test_failed_checks_are_legal_result_without_automatic_continuation(self):
        context = self.start()
        self.assertEqual(self.submit(context, result="failed")["status"], "accepted")
        self.finish(context, "failed")
        self.close(outcome="failed")
        cycle = self.store.snapshot()["cycles"][0]
        self.assertEqual(cycle["outcome"], "failed")
        self.assertFalse(cycle["continuationDecision"]["allowed"])

    def test_actual_failure_cannot_be_closed_as_completed(self):
        context, refs = self.start(), [self.evidence()]
        self.submit(context, refs=refs)
        self.finish(context, "failed")
        with self.assertRaisesRegex(HarnessError, "RESULT_MISMATCH"):
            self.close(refs=refs)

    def test_system_termination_without_fabricated_model_submission(self):
        context = self.start()
        self.finish(context, "interrupted")
        receipt = self.close(outcome="interrupted", submission=None)
        self.assertEqual(receipt["source"], "system_termination")
        self.assertEqual(self.store.snapshot()["cycles"][0]["submissions"], [])

    def test_two_attempts_keep_identity_reports_events_and_usage_independent(self):
        first = self.start()
        self.store.publish_progress(first, "p1", self.report(title="First"))
        self.store.record_event(first, 1, {"type": "started"})
        self.finish(first, "failed")
        second = self.start("attempt-2")
        self.assertEqual(self.store.snapshot()["cycles"][0]["report"]["status"], "missing")
        self.store.publish_progress(second, "p1", self.report(title="Second"))
        self.store.record_event(second, 1, {"type": "started"})
        for context, call_id in ((first, "call-1"), (second, "call-2")):
            self.store.record_usage(self.contract["cycleId"], context["attemptId"], {
                "callId": call_id, "coverage": "self", "cost": 1, "inputTokens": 10, "outputTokens": 4})
        self.assertEqual(self.store.publish_progress(first, "late", {"reportRevision": 2, "title": "Late"})["errorCode"], "STALE_ATTEMPT")
        cycles = self.store.snapshot()["cycles"]
        self.assertEqual(len(cycles), 1)
        self.assertEqual(cycles[0]["sequenceNumber"], 17)
        self.assertEqual(cycles[0]["report"]["title"], "Second")
        self.assertEqual([a["usage"]["cost"] for a in cycles[0]["attempts"]], [1, 1])
        self.assertEqual([a["events"][0]["sequence"] for a in cycles[0]["attempts"]], [1, 1])

    def test_report_and_event_revision_conflicts(self):
        context = self.start()
        self.store.publish_progress(context, "p1", self.report(2, "Current"))
        self.assertEqual(self.store.publish_progress(context, "p2", {"reportRevision": 1})["errorCode"], "STALE_REPORT")
        first = self.store.record_event(context, 1, {"type": "start"})
        self.assertEqual(self.store.record_event(context, 1, {"type": "start"}), first)
        with self.assertRaisesRegex(HarnessError, "ID_CONFLICT"):
            self.store.record_event(context, 1, {"type": "finish"})

    def test_new_generation_fences_old_model_but_requires_host_reconciliation(self):
        context = self.start()
        self.store.claim_controller("controller-next")
        self.assertEqual(self.submit(context, result="failed")["errorCode"], "STALE_GENERATION")
        with self.assertRaisesRegex(HarnessError, "WRITERS_UNCONFIRMED"):
            self.start("attempt-2")
        self.finish(context, "interrupted")
        next_context = self.start("attempt-2")
        self.assertEqual(next_context["generation"], "controller-next")

    def test_budget_cannot_reset_by_correction_extension_or_store_restart(self):
        context = self.start()
        original_deadline = self.store.snapshot()["cycles"][0]["deadline"]
        self.tick += 300
        extension = self.store.request_extension(context, "extend", "Need to finish the same draft", 170)
        self.assertEqual(extension["status"], "accepted")
        self.finish(context, "failed")
        self.store = self.open()
        self.start("attempt-2")
        self.tick += 181
        self.assertEqual(self.store.snapshot()["cycles"][0]["time"]["executionSeconds"], 481)
        self.assertEqual(self.store.snapshot()["cycles"][0]["deadline"], original_deadline)
        current = self.store.snapshot()["cycles"][0]["attempts"][-1]["context"]
        self.assertEqual(self.submit(current, result="failed")["errorCode"], "BUDGET_EXHAUSTED")

    def test_cross_boot_preserves_consumed_lower_bound_and_stops_business(self):
        context = self.start()
        self.tick += 50
        self.store.publish_progress(context, "p1", self.report())
        self.store = self.open("different-boot")
        cycle = self.store.snapshot()["cycles"][0]
        self.assertEqual(cycle["time"]["executionSeconds"], 50)
        self.assertEqual(cycle["time"]["reliability"], "unknown")
        self.assertEqual(self.submit(context, result="failed")["errorCode"], "TIME_UNCONFIRMED")

    def test_recovery_has_separate_nonresettable_budget_and_no_new_cycle(self):
        context = self.start()
        self.tick += 480
        self.finish(context, "interrupted")
        recovery = self.store.begin_recovery(self.contract["cycleId"], "recover-1", budget_seconds=60, reason="Safe closure")
        self.start("recovery-attempt", recovery_id=recovery["recoveryId"])
        self.tick += 61
        cycle = self.store.snapshot()["cycles"][0]
        self.assertEqual(cycle["time"]["executionSeconds"], 480)
        self.assertEqual(cycle["time"]["recoverySeconds"], 61)
        self.assertEqual(cycle["time"]["totalSeconds"], 541)
        ctx = cycle["attempts"][-1]["context"]
        self.assertEqual(self.submit(ctx, result="failed")["errorCode"], "BUDGET_EXHAUSTED")
        self.finish(ctx, "failed")
        with self.assertRaisesRegex(HarnessError, "RECOVERY_ALREADY_ALLOCATED"):
            self.store.begin_recovery(self.contract["cycleId"], "recover-new", budget_seconds=60, reason="Reset")

    def test_evidence_is_readable_immutable_and_owner_bound(self):
        context, ref = self.start(), self.evidence()
        self.assertEqual(self.store.read_evidence(ref["evidenceId"])["content"], "Actual draft")
        with self.assertRaisesRegex(HarnessError, "ID_CONFLICT"):
            self.evidence(content="Changed")
        bad = {**ref, "sha256": "wrong"}
        self.assertEqual(self.submit(context, refs=[bad])["errorCode"], "EVIDENCE_VERSION_MISMATCH")
        self.assertEqual(self.store.checkpoint(context, "cp1", {"evidenceRefs": [ref]})["status"], "accepted")

    def test_parent_subtree_usage_never_double_counts_child_and_retries(self):
        context = self.start()
        parent = {"callId": "parent", "coverage": "subtree", "cost": 5, "inputTokens": 100, "outputTokens": 20}
        child = {"callId": "child", "parentCallId": "parent", "coverage": "self", "cost": 2, "inputTokens": 30, "outputTokens": 5}
        for call in (child, parent, parent):
            self.store.record_usage(context["cycleId"], context["attemptId"], call)
        usage = self.store.snapshot()["cycles"][0]["attempts"][0]["usage"]
        self.assertEqual(usage["cost"], 5)
        self.assertEqual(usage["countedCallIds"], ["parent"])
        self.assertFalse(usage["costComplete"])
        self.finish(context)
        self.store.confirm_usage(context["cycleId"], context["attemptId"], ["parent", "child"],
            source="trusted-meter", observation={"settlement": "complete-provider-ledger"})
        self.assertTrue(self.store.snapshot()["cycles"][0]["attempts"][0]["usage"]["costComplete"])
        with self.assertRaisesRegex(HarnessError, "ID_CONFLICT"):
            self.store.record_usage(context["cycleId"], context["attemptId"], {**parent, "cost": 6})

    def test_unknown_usage_is_not_zero_or_complete_and_parent_cycles_rejected(self):
        context = self.start()
        usage = self.store.snapshot()["cycles"][0]["attempts"][0]["usage"]
        self.assertIsNone(usage["cost"])
        parent = {"callId": "p", "parentCallId": "c", "coverage": "unknown", "cost": 5}
        self.store.record_usage(context["cycleId"], context["attemptId"], parent)
        with self.assertRaisesRegex(HarnessError, "CALL_CYCLE"):
            self.store.record_usage(context["cycleId"], context["attemptId"], {"callId": "c", "parentCallId": "p", "coverage": "self"})
        self.assertFalse(self.store.snapshot()["cycles"][0]["attempts"][0]["usage"]["costComplete"])

    def test_submit_pending_worker_version_requires_collection_before_close(self):
        context = self.start()
        content = "Worker's exact submitted draft"
        ref = {"evidenceId": "pending-v1", "sha256": hashlib.sha256(content.encode()).hexdigest()}
        self.assertEqual(self.submit(context, refs=[ref])["status"], "accepted")
        self.finish(context)
        with self.assertRaisesRegex(HarnessError, "EVIDENCE_MISSING"):
            self.close(refs=[ref])
        self.store.bind_evidence(context["cycleId"], "pending-v1", content)
        self.close(refs=[ref])

    def test_execution_recovery_and_shutdown_time_are_separate(self):
        context = self.start()
        self.tick += 30
        self.finish(context, "interrupted")
        self.tick += 10
        self.store.begin_recovery(context["cycleId"], "recovery", budget_seconds=60, reason="Close safely")
        recovery_context = self.start("recovery-attempt", recovery_id="recovery")
        self.tick += 15
        self.store.publish_progress(recovery_context, "p1", self.report())
        self.finish(recovery_context, "failed")
        self.tick += 5
        self.close(outcome="failed", submission=None)
        timing = self.store.snapshot()["cycles"][0]["time"]
        self.assertEqual(timing["executionSeconds"], 30)
        self.assertEqual(timing["recoverySeconds"], 20)
        self.assertEqual(timing["totalSeconds"], 60)

    def test_correction_wait_consumes_original_deadline_but_not_execution_clock(self):
        context = self.start()
        self.tick += 30
        self.finish(context, "failed")
        self.tick += 451
        with self.assertRaisesRegex(HarnessError, "BUDGET_EXHAUSTED"):
            self.start("correction")
        self.assertEqual(self.store.snapshot()["cycles"][0]["time"]["executionSeconds"], 30)

    def test_reports_reuse_existing_plain_text_limits_and_phase_semantics(self):
        context = self.start()
        for index, bad in enumerate(({"title": "a" * 61}, {"summary": "a" * 501},
                                     {"blocker": "a" * 301}, {"reportedPhase": "passed"},
                                     {"title": "line\nbreak"})):
            receipt = self.store.publish_progress(context, "bad-" + str(index), {**self.report(), **bad})
            self.assertEqual(receipt["status"], "rejected")
        self.assertEqual(self.store.publish_progress(context, "review", {**self.report(), "reportedPhase": "review"})["status"], "accepted")
        self.assertEqual(self.store.snapshot()["cycles"][0]["qualityApplicability"], [])

    def test_failed_submission_cannot_be_promoted_to_completed_or_partial(self):
        context = self.start()
        self.assertEqual(self.submit(context, result="failed")["status"], "accepted")
        self.finish(context, "completed")
        for outcome in ("completed", "partial"):
            with self.assertRaisesRegex(HarnessError, "RESULT_MISMATCH"):
                self.close(outcome=outcome)
        self.assertNotEqual(self.store.snapshot()["cycles"][0]["protocolState"], "closed")

    def test_partial_submission_cannot_be_promoted_to_completed(self):
        context, refs = self.start(), [self.evidence()]
        self.assertEqual(self.submit(context, refs=refs, result="partial")["status"], "accepted")
        self.finish(context)
        with self.assertRaisesRegex(HarnessError, "RESULT_MISMATCH"):
            self.close(refs=refs)
        self.close(outcome="partial", refs=refs)

    def test_usage_observed_fields_do_not_imply_complete_call_set(self):
        context = self.start()
        call = {"callId": "one", "coverage": "self", "cost": 2, "inputTokens": 10, "outputTokens": 4}
        self.store.record_usage(context["cycleId"], context["attemptId"], call)
        cycle = self.store.snapshot()["cycles"][0]
        usage = cycle["attempts"][0]["usage"]
        self.assertEqual(usage["totalTokens"], 14)
        self.assertEqual(usage["status"], "partial")
        self.assertTrue(usage["observedFieldsComplete"]["cost"])
        self.assertFalse(usage["costComplete"])
        self.assertFalse(cycle["usage"]["totalTokensComplete"])
        with self.assertRaisesRegex(HarnessError, "WRITERS_UNCONFIRMED"):
            self.store.confirm_usage(context["cycleId"], context["attemptId"], ["one"], source="provider-ledger", observation="final")
        self.finish(context, "failed")
        with self.assertRaisesRegex(HarnessError, "USAGE_CALL_SET_MISMATCH"):
            self.store.confirm_usage(context["cycleId"], context["attemptId"], [], source="provider-ledger", observation="final")
        self.store.confirm_usage(context["cycleId"], context["attemptId"], ["one"], source="provider-ledger", observation="final")
        self.assertTrue(self.store.snapshot()["cycles"][0]["attempts"][0]["usage"]["costComplete"])
        self.close(outcome="failed", submission=None)
        self.assertTrue(self.store.snapshot()["cycles"][0]["usage"]["costComplete"])
        self.store.record_usage(context["cycleId"], context["attemptId"], {**call, "callId": "late", "cost": 3})
        late = self.store.snapshot()["cycles"][0]
        self.assertEqual(late["usage"]["cost"], 5)
        self.assertEqual(late["usage"]["totalTokens"], 28)
        self.assertFalse(late["usage"]["costComplete"])
        self.assertFalse(late["attempts"][0]["usage"]["coverage"]["callSetConfirmed"])
        self.assertEqual(late["attempts"][0]["usageConfirmation"]["callIds"], ["one"])

    def test_cycle_usage_includes_both_attempts_and_unknown_coverage(self):
        first = self.start()
        self.store.record_usage(first["cycleId"], first["attemptId"], {
            "callId": "first-call", "coverage": "self", "cost": 2, "inputTokens": 10, "outputTokens": 4})
        self.finish(first, "failed")
        self.store.confirm_usage(first["cycleId"], first["attemptId"], ["first-call"], source="provider", observation="final")
        second = self.start("second")
        self.store.record_usage(second["cycleId"], second["attemptId"], {
            "callId": "second-call", "coverage": "self", "cost": 3, "inputTokens": None, "outputTokens": 5})
        self.finish(second, "failed")
        self.close(outcome="failed", submission=None)
        usage = self.store.snapshot()["cycles"][0]["usage"]
        self.assertEqual(usage["cost"], 5)
        self.assertEqual(usage["outputTokens"], 9)
        self.assertFalse(usage["costComplete"])
        self.assertEqual(usage["coverage"]["completeAttemptIds"], [first["attemptId"]])

    def test_recovery_progress_persists_recovery_and_total_lower_bounds(self):
        context = self.start()
        self.tick += 30
        self.finish(context, "interrupted")
        self.store.begin_recovery(context["cycleId"], "recover", budget_seconds=100, reason="Close safely")
        recovery_context = self.start("recovery-attempt", recovery_id="recover")
        self.tick += 40
        self.assertEqual(self.store.publish_progress(recovery_context, "recovery-progress", self.report())["status"], "accepted")
        self.store = self.open("new-boot")
        timing = self.store.snapshot()["cycles"][0]["time"]
        self.assertEqual(timing["executionSeconds"], 30)
        self.assertEqual(timing["recoverySeconds"], 40)
        self.assertEqual(timing["totalSeconds"], 70)
        self.assertEqual(timing["reliability"], "unknown")
        self.assertEqual(self.store.publish_progress(recovery_context, "late", self.report(2))["errorCode"], "TIME_UNCONFIRMED")

    def test_report_unknown_wrapper_fields_are_rejected_before_projection(self):
        context = self.start()
        for index, extra in enumerate(({"value": {"summary": "x" * 501}}, {"status": "available"},
                                       {"source": "runtime"}, {"reporterAttemptId": "forged"})):
            receipt = self.store.publish_progress(context, "extra-" + str(index), {**self.report(), **extra})
            self.assertEqual(receipt["status"], "rejected")
            self.assertEqual(receipt["errorCode"], "UNKNOWN_FIELD")
        self.assertEqual(self.store.snapshot()["cycles"][0]["report"]["status"], "missing")

    def test_confirmed_nonempty_call_set_keeps_unknown_fields_null(self):
        context = self.start()
        self.store.record_usage(context["cycleId"], context["attemptId"], {
            "callId": "unknown-call", "coverage": "self", "cost": None,
            "inputTokens": None, "outputTokens": None})
        self.finish(context, "failed")
        self.store.confirm_usage(context["cycleId"], context["attemptId"], ["unknown-call"],
            source="provider", observation="complete-call-set-without-field-values")
        self.close(outcome="failed", submission=None)
        cycle = self.store.snapshot()["cycles"][0]
        for usage in (cycle["usage"], cycle["attempts"][0]["usage"]):
            self.assertTrue(usage["coverage"]["callSetConfirmed"])
            self.assertEqual(usage["status"], "partial")
            for field in ("cost", "inputTokens", "outputTokens", "totalTokens"):
                self.assertIsNone(usage[field])
                self.assertFalse(usage[field + "Complete"])

    def test_confirmed_empty_call_set_is_known_zero_after_closure(self):
        context = self.start()
        self.finish(context, "not_started")
        self.store.confirm_usage(context["cycleId"], context["attemptId"], [],
            source="supervisor", observation="verified-no-provider-invocation")
        self.close(outcome="not_started", submission=None)
        cycle = self.store.snapshot()["cycles"][0]
        for usage in (cycle["usage"], cycle["attempts"][0]["usage"]):
            self.assertTrue(usage["coverage"]["callSetConfirmed"])
            self.assertEqual(usage["status"], "available")
            for field in ("cost", "inputTokens", "outputTokens", "totalTokens"):
                self.assertEqual(usage[field], 0)
                self.assertTrue(usage[field + "Complete"])

    def test_parallel_identical_submit_commits_once(self):
        context, refs = self.start(), [self.evidence()]
        with ThreadPoolExecutor(max_workers=4) as pool:
            receipts = list(pool.map(lambda _: self.submit(context, refs=refs), range(8)))
        self.assertTrue(all(receipt == receipts[0] for receipt in receipts))
        self.assertEqual(len(self.store.snapshot()["cycles"][0]["submissions"]), 1)

    def test_read_snapshot_revision_is_stable_and_development_limit_is_720(self):
        self.start()
        snapshot = self.store.snapshot()
        self.tick += 2
        newer = self.store.snapshot()
        self.assertEqual(newer["snapshotRevision"], snapshot["snapshotRevision"])
        self.assertEqual(newer["projectionEpoch"], snapshot["projectionEpoch"])
        self.assertGreater(newer["cycles"][0]["time"]["executionSeconds"], snapshot["cycles"][0]["time"]["executionSeconds"])
        other = HarnessStore(self.root / "development", create=True, clock=lambda: self.tick, boot_id="b")
        other.create_cycle({**self.contract, "timeClass": "development"})
        self.assertEqual(other.snapshot()["cycles"][0]["time"]["hardLimitSeconds"], 720)


if __name__ == "__main__":
    unittest.main()
