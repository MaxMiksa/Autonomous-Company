"""Read-only journal contracts; fixtures never run the company or host services."""

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


DASHBOARD = Path(__file__).resolve().parents[1] / "dashboard"
sys.path.insert(0, str(DASHBOARD))
import journal_data as data_module


def record(identity="cycle-0001-run-a", number=1, **changes):
    value = {"schema_version": 1, "kind": "cycle_usage", "cycle_id": identity, "cycle_number": number,
             "started_at": "2026-09-18T12:00:00+08:00", "ended_at": "2026-09-18T12:01:00+08:00",
             "status": "completed", "engine": "codex", "model": "example-model",
             "usage": {"input_tokens": 90, "output_tokens": 10, "total_tokens": 100, "status": "reported"}}
    value.update(changes)
    return value


class JournalFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "logs").mkdir()
        (self.root / "memories").mkdir()
        self.source = data_module.JournalSource(self.root, "zh-CN")

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def ledger(self, *records):
        self.write("logs/usage.jsonl", "\n".join(json.dumps(value) for value in records))

    def live_status(self):
        pid = self.write(".auto-loop.pid", "4321\n")
        os.utime(pid, (1700000000, 1700000000))
        self.write(".auto-loop-state", "STATUS=running\nLOOP_COUNT=2\nENGINE=codex\nMODEL=example-model\n")
        self.write(".autonomous-company.local", "ACTIVE_PROJECT=projects/probe\n")
        self.write("logs/usage.jsonl.pending", json.dumps(record("cycle-0002-live", number=2, status="interrupted")))
        self.write("logs/cycle-0002-live.context.json", json.dumps({
            "version": 1, "cycleId": "cycle-0002-live", "project": "projects/probe",
            "recordedAt": "2026-09-18T12:00:00+08:00", "source": "runtime_context"}))
        return {"ok": True, "raw": "Loop is running", "stateFile": self.source.pairs(".auto-loop-state"),
                "parsed": {"loop": {"state": "running", "processState": "running", "pid": 4321},
                           "daemon": {"state": "active"}}}


class JournalTests(JournalFixture):
    def test_persistent_numbers_replace_only_their_exact_program_bound_cycles(self):
        from product_identity import reserve_cycle, update_cycle
        self.write("projects/probe/index.html", "<p>Real file</p>")
        self.write(".autonomous-company.local", "ACTIVE_PROJECT=projects/probe\n")
        first = reserve_cycle(self.root, "projects/probe", "attempt-a", 1)
        update_cycle(self.root, first["cycleId"], "completed")
        second = reserve_cycle(self.root, "projects/probe", "attempt-b", 1)
        update_cycle(self.root, second["cycleId"], "completed")
        self.ledger(record(first["cycleId"], project="projects/probe"),
                    record(second["cycleId"], project="projects/probe"), record())
        before = (self.root / "logs/usage.jsonl").read_bytes()
        data = self.source.snapshot()
        rows = {cycle["id"]: cycle for cycle in data["cycles"]}
        self.assertEqual([rows[row["cycleId"]]["number"] for row in (first, second)], [1, 2])
        self.assertEqual(rows[second["cycleId"]]["runCycleNumber"], 1)
        self.assertEqual(rows["cycle-0001-run-a"]["numbering"], "legacy")
        self.assertEqual(data["project"]["stableId"], second["productId"])
        self.assertEqual((self.root / "logs/usage.jsonl").read_bytes(), before)

    def test_unconfirmed_reservation_is_visible_without_invented_usage_or_live_status(self):
        from product_identity import reserve_cycle, update_cycle, recover_cycles
        self.write("projects/probe/index.html", "<p>Real file</p>")
        self.write(".autonomous-company.local", "ACTIVE_PROJECT=projects/probe\n")
        cycle = reserve_cycle(self.root, "projects/probe", "uncertain", 1)
        update_cycle(self.root, cycle["cycleId"], "dispatching")
        recover_cycles(self.root)
        row = self.source.snapshot()["cycles"][0]
        self.assertEqual(row["status"], "startup_unconfirmed")
        self.assertFalse(row["active"])
        self.assertIsNone(row["usage"]["totalTokens"])
        self.assertFalse(row["durationReliable"])

    def test_creation_links_exploration_explicitly_without_relabeling_its_number(self):
        from product_identity import reserve_cycle, register_project, update_cycle
        cycle = reserve_cycle(self.root, "", "exploration", 1)
        self.write("projects/probe/index.html", "<p>Real file</p>")
        register_project(self.root, "projects/probe", cycle["cycleId"])
        update_cycle(self.root, cycle["cycleId"], "completed")
        import hashlib
        text = "# Real delivery file\n"
        self.write("projects/probe/DELIVERY.md", text)
        self.write("logs/artifacts/" + "a" * 32 + ".json", json.dumps({
            "version": 1, "id": "a" * 32, "kind": "document", "project": "projects/probe",
            "cycleId": cycle["cycleId"], "recordedAt": "2026-09-19T01:00:00+00:00", "source": "runner",
            "path": "projects/probe/DELIVERY.md", "sha256": hashlib.sha256(text.encode()).hexdigest()}))
        data = self.source.snapshot()
        self.assertEqual(data["project"]["id"], "projects/probe")
        row = data["cycles"][0]
        self.assertEqual(row["identityKind"], "exploration")
        self.assertIsNone(row["stableProductId"])
        self.assertEqual(row["linkedProductId"], data["project"]["stableId"])
        self.assertEqual(row["projectStatus"], "current")
        self.assertEqual(data["artifactCollection"]["selectedProject"], "projects/probe")
        self.assertEqual(row["artifacts"][0]["path"], "projects/probe/DELIVERY.md")
        self.assertEqual(data["artifacts"][0]["path"], "projects/probe/DELIVERY.md")

    def test_unique_id_preserves_restarted_numbers_and_ignores_prose_cycle_count(self):
        first = record()
        second = record("cycle-0001-run-b", started_at="2026-09-18T13:00:00+08:00")
        self.ledger(first, first, second)
        self.write(".auto-loop-state", "LOOP_COUNT=99\nSTATUS=running\n")
        self.write("memories/consensus.md", "## Current Phase\nLaunching\n## What We Did This Cycle\n- Cycle 15 is a narrative stage\n")
        snapshot = self.source.snapshot()
        self.assertEqual([item["id"] for item in snapshot["cycles"]], [second["cycle_id"], first["cycle_id"]])
        self.assertEqual([item["number"] for item in snapshot["cycles"]], [1, 1])
        self.assertEqual(snapshot["runtime"]["state"], "stopped")
        self.assertEqual(snapshot["consensus"]["phase"], "Launching")
        self.assertEqual(snapshot["runtime"]["reasoning"], "unknown")

    def test_malformed_conflicting_and_traversal_id_records_warn_without_duplicate_count(self):
        first = record()
        self.ledger(first, record(status="failed"), record("../secret"), ["wrong"], record(number=True))
        with (self.root / "logs/usage.jsonl").open("a", encoding="utf-8") as ledger:
            ledger.write("\n{broken\n")
        snapshot = self.source.snapshot()
        self.assertEqual(len(snapshot["cycles"]), 1)
        self.assertIn("ledger_invalid_records:4", snapshot["warnings"])
        self.assertIn("ledger_conflicting_ids:1", snapshot["warnings"])

    def test_unknown_tokens_and_timestamps_remain_unknown(self):
        self.ledger(record(started_at="bad", ended_at="2026-09-18T12:00:00", status=[],
                           usage={"input_tokens": 0, "output_tokens": -1, "total_tokens": None}))
        cycle = self.source.snapshot()["cycles"][0]
        self.assertIsNone(cycle["startedAt"])
        self.assertIsNone(cycle["endedAt"])
        self.assertEqual(cycle["status"], "unknown")
        self.assertEqual(cycle["usage"], {"inputTokens": 0, "outputTokens": None, "totalTokens": None, "status": "partial"})
        for value in (True, "10", 1.5, -1, 2**60):
            self.assertIsNone(data_module.token_count(value))

    def test_consensus_reads_sections_after_long_intro_and_reports_file_mtime(self):
        text = "# Report\n" + ("intro\n" * 800) + "\n## 最后更新\n2020-01-01T00:00:00+08:00\n## 当前阶段\n交付\n## 本轮做了什么\n- 完成测试\n## 下一步行动\n等待人工试用\n"
        path = self.write("memories/consensus.md", text)
        os.utime(path, (1800000000, 1800000000))
        consensus = self.source.snapshot()["consensus"]
        self.assertEqual(consensus["phase"], "交付")
        self.assertEqual(consensus["progress"], ["完成测试"])
        self.assertNotIn("nextAction", consensus)
        self.assertEqual(consensus["reportedUpdatedAt"], "2020-01-01T00:00:00+08:00")
        self.assertEqual(consensus["updatedAt"], "2027-01-15T08:00:00+00:00")
        self.assertEqual(consensus["raw"], path.read_bytes().decode("utf-8"))

    def test_sidecar_is_summary_source_not_fabricated_history(self):
        self.ledger(record())
        self.write("logs/cycle-0001-run-a.json", json.dumps({"result": "**Shipped MVP.**\n\nDetailed evidence."}))
        cycle = self.source.snapshot()["cycles"][0]
        self.assertEqual(cycle["summary"], "Shipped MVP.")
        self.assertIn("Detailed evidence.", cycle["report"])
        self.assertFalse(cycle["logAvailable"])

    def test_recovery_and_clock_rollback_do_not_claim_precise_duration(self):
        self.ledger(record("recovered", status="interrupted", source={"type": "cycle_recovery"}),
                    record("clock-rollback", ended_at="2026-09-18T11:59:00+08:00"),
                    record("timeout-complete", status="completed_with_timeout"))
        cycles = {cycle["id"]: cycle for cycle in self.source.snapshot()["cycles"]}
        self.assertFalse(cycles["recovered"]["durationReliable"])
        self.assertEqual(cycles["recovered"]["endedAtKind"], "recovered")
        self.assertFalse(cycles["clock-rollback"]["durationReliable"])
        self.assertEqual(cycles["timeout-complete"]["status"], "completed_with_timeout")

    def test_markdown_delimiters_remain_bounded_and_nonregular_files_rejected(self):
        text = "[" * data_module.MAX_TEXT_BYTES
        self.assertEqual(data_module.plain_text(text), text)
        with self.assertRaises(ValueError):
            self.source.read("logs")

    def test_log_requires_ledger_identity_and_bounds_tail(self):
        self.ledger(record())
        self.write("logs/cycle-0001-run-a.log", "old-" + "a" * data_module.MAX_LOG_BYTES + "\n-latest")
        result = self.source.log("cycle-0001-run-a")
        self.assertTrue(result["available"])
        self.assertTrue(result["truncated"])
        self.assertTrue(result["text"].endswith("-latest"))
        self.assertLessEqual(len(result["text"]), data_module.MAX_LOG_BYTES)
        for identity in ("../secret", "cycle-0001-unknown", "cycle-0001-run-a/../../secret"):
            with self.assertRaises(ValueError):
                self.source.log(identity)

    def test_execution_domain_configuration_requires_matching_scoped_identity(self):
        from product_identity import reserve_cycle
        self.write('projects/probe/index.html', '<p>Fixture</p>')
        self.write('.autonomous-company.local', 'ACTIVE_PROJECT=projects/probe\n')
        cycle = reserve_cycle(self.root, 'projects/probe', 'live-fixture', 1)
        self.write('.auto-loop-state', 'STATUS=idle\nPRODUCT_ID=' + cycle['productId'] + '\nENGINE=codex\nMODEL=actual-model\n')
        status = {'ok': True, 'stateFile': self.source.pairs('.auto-loop-state'),
                  'parsed': {'loop': {'state': 'idle', 'processState': 'running', 'pid': 4321}}}
        source = data_module.JournalSource(self.root, 'en', scope=data_module.ProductScope('product', product_id=cycle['productId'], project='projects/probe'))
        config = {'effort': 'high', 'productLanguage': 'zh-CN'}
        result = source.snapshot(status=status, runtime_config=config)
        self.assertEqual(result['runtime']['reasoning'], 'high')
        self.assertEqual(result['runtime']['language'], 'zh-CN')
        self.assertEqual(result['runtime']['configSource'], 'execution_domain')
        self.assertEqual(result['runtime']['state'], 'idle')
        changed = {**status, 'stateFile': {**status['stateFile'], 'PRODUCT_ID': 'f' * 32}}
        result = source.snapshot(status=changed, runtime_config=config)
        self.assertEqual(result['runtime']['reasoning'], 'unknown')
        self.assertEqual(result['runtime']['state'], 'unknown')
        self.assertNotIn('configSource', result['runtime'])


    def test_usage_pending_does_not_promote_reserved_attempt_before_real_dispatch(self):
        from product_identity import reserve_cycle, update_cycle
        status = self.live_status()
        self.write("projects/probe/index.html", "<p>Real file</p>")
        reservation = reserve_cycle(self.root, "projects/probe", "staged-attempt", 2)
        identity = reservation["cycleId"]
        pending = record(identity, number=2)
        self.write("logs/usage.jsonl.pending", json.dumps(pending))
        self.write(f"logs/{identity}.context.json", json.dumps({
            "version": 1, "cycleId": identity, "project": "projects/probe",
            "recordedAt": pending["started_at"], "source": "runtime_context"}))
        identity_path = self.root / ".autonomous-company/product-state.json"
        reserved_bytes = identity_path.read_bytes()
        reserved = self.source.snapshot(status=status)
        self.assertEqual(reserved["cycles"][0]["status"], "not_started")
        self.assertFalse(reserved["cycles"][0]["active"])
        self.assertIsNone(reserved["cycles"][0]["startedAt"])
        self.assertIsNone(reserved["runtime"]["currentCycleId"])
        self.assertIsNone(reserved["cycles"][0]["usage"]["totalTokens"])
        self.assertEqual(identity_path.read_bytes(), reserved_bytes)
        with self.assertRaises(ValueError):
            self.source.log(identity, status)
        update_cycle(self.root, identity, "dispatching")
        dispatched_bytes = identity_path.read_bytes()
        dispatched = self.source.snapshot(status=status)
        self.assertTrue(dispatched["cycles"][0]["active"])
        self.assertEqual(dispatched["cycles"][0]["status"], "running")
        actual_dispatch = self.source.identity_state()["cycles"][identity]["dispatchAt"]
        self.assertEqual(dispatched["cycles"][0]["startedAt"], actual_dispatch)
        self.assertNotEqual(dispatched["cycles"][0]["startedAt"], pending["started_at"])
        self.assertEqual(identity_path.read_bytes(), dispatched_bytes)
        update_cycle(self.root, identity, "completed")
        completed = self.source.snapshot(status=status)
        self.assertFalse(completed["cycles"][0]["active"])
        self.assertEqual(completed["cycles"][0]["status"], "completed")
        self.assertIsNone(completed["runtime"]["currentCycleId"])


    def test_documents_only_advertise_delivery_and_one_explicit_project_readme(self):
        self.write("DELIVERY.md", "# Sample — Local MVP\n[Guide](projects/sample/README.md)\n")
        self.write("projects/sample/README.md", "# Sample guide")
        self.write(".env", "private")
        self.assertEqual([item["path"] for item in self.source.documents()], ["DELIVERY.md", "projects/sample/README.md"])
        self.assertEqual(self.source.snapshot()["project"]["name"], "Autonomous Company",
                         "delivery prose is not project identity")
        self.assertEqual(self.source.document("projects/sample/README.md")[0], "# Sample guide")
        for path in (".env", "../.env", "projects/sample/../../.env", "C:/secret", "projects\\sample\\README.md"):
            with self.assertRaises(ValueError):
                self.source.document(path)

    def test_project_metadata_is_identity_bound_and_never_reuses_consensus(self):
        self.write("DELIVERY.md", "# Old Product\n[Guide](projects/old/README.md)\n")
        self.write("projects/old/README.md", "stale deliverable")
        self.write(".autonomous-company.local", "ACTIVE_PROJECT=projects/probe\n")
        self.write("projects/probe/.autonomous-company-project.json", json.dumps({
            "version": 1, "project": "projects/probe", "displayName": "Probe",
            "description": "Bound description", "recordedAt": "2026-09-19T01:00:00+00:00",
            "source": "project_metadata"}))
        self.write("memories/consensus.md", "## Company State\n- Product: stale other product\n")
        project = self.source.snapshot()["project"]
        self.assertEqual(project, {"id": "projects/probe", "name": "Probe", "displayName": "Probe",
                                  "description": "Bound description", "source": "project_metadata",
                                  "status": "recorded", "recordedAt": "2026-09-19T01:00:00+00:00", "stableId": None,
                                  "createdAt": None})
        self.assertEqual(self.source.documents(), [], "legacy root delivery cannot cross product selection")
        self.write(".autonomous-company.local", "ACTIVE_PROJECT=projects/other\n")
        self.write("projects/other/README.md", "new selection")
        project = self.source.snapshot()["project"]
        self.assertEqual((project["id"], project["name"], project["description"], project["status"]),
                         ("projects/other", "other", "", "missing"))
        self.write("projects/other/.autonomous-company-project.json", json.dumps({
            "version": 1, "project": "projects/probe", "displayName": "Wrong",
            "description": "wrong identity", "recordedAt": "2026-09-19T01:00:00+00:00",
            "source": "project_metadata"}))
        self.assertEqual(self.source.snapshot()["project"]["status"], "invalid")

    def test_project_switch_does_not_borrow_unknown_or_other_cycle(self):
        self.write(".autonomous-company.local", "ACTIVE_PROJECT=projects/probe\n")
        self.write("projects/probe/README.md", "selected")
        current = record("cycle-current", started_at="2026-09-19T12:00:00+00:00")
        other = record("cycle-other", number=2, started_at="2026-09-19T13:00:00+00:00")
        unknown = record("cycle-unknown", number=3, started_at="2026-09-19T14:00:00+00:00")
        self.ledger(current, other, unknown)
        for identity, project in (("cycle-current", "projects/probe"), ("cycle-other", "projects/other")):
            self.write(f"logs/{identity}.context.json", json.dumps({
                "version": 1, "cycleId": identity, "project": project,
                "recordedAt": "2026-09-19T01:00:00+00:00", "source": "runtime_context"}))
        for identity, project in (("cycle-current", "projects/probe"), ("cycle-other", "projects/other"),
                                  ("cycle-unknown", "projects/probe")):
            self.write(f"logs/{identity}.work.json", json.dumps({
                "version": 2, "cycle_id": identity, "project": project,
                "recorded_at": "2026-09-19T01:00:00+00:00", "source": "model_report",
                "final": True, "phase": "review", "title": identity,
                "summary": "Valid historical report", "blocker": ""}))
        snapshot = self.source.snapshot()
        cycles = {cycle["id"]: cycle for cycle in snapshot["cycles"]}
        self.assertEqual(cycles["cycle-current"]["projectStatus"], "current")
        self.assertEqual(cycles["cycle-other"]["projectStatus"], "other")
        self.assertEqual(cycles["cycle-unknown"]["projectStatus"], "unknown")
        self.assertEqual(cycles["cycle-other"]["workReportStatus"], "valid")
        self.assertEqual(cycles["cycle-unknown"]["workReportStatus"], "valid")
        self.assertEqual(snapshot["latestProjectCycleId"], "cycle-current")

    def test_large_history_marks_unloaded_cycle_details_explicitly(self):
        records = [record(f"cycle-{number:04d}", number=number + 1,
                          started_at=f"2026-09-{(number % 18) + 1:02d}T12:00:00+00:00")
                   for number in range(31)]
        self.ledger(*records)
        snapshot = self.source.snapshot()
        self.assertEqual(len(snapshot["cycles"]), 31)
        self.assertIn("cycle_details_truncated", snapshot["warnings"])
        self.assertEqual(snapshot["cycles"][-1]["detailStatus"], "limited")
        self.assertEqual(snapshot["cycles"][-1]["projectStatus"], "unknown")

    def test_cycle_check_projection_and_live_elapsed_have_verified_identity(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/core"))
        from runtime_artifacts import base_record, save
        self.write(".autonomous-company.local", "ACTIVE_PROJECT=projects/probe\n")
        self.write("projects/probe/README.md", "project")
        self.ledger(record())
        check = base_record("projects/probe", "check")
        check.update(cycleId="cycle-0001-run-a", state="running",
                     startedAt="2026-09-18T12:00:30+08:00", endedAt=None,
                     adapter="exit-code", command=["python", "-m", "unittest"],
                     exitCode=None, reportStatus="unavailable")
        save(self.root, check)
        cycle = self.source.snapshot()["cycles"][0]
        self.assertEqual((cycle["projectId"], cycle["checkStatus"]), ("projects/probe", "running"))
        self.assertEqual(cycle["latestCheck"]["cycleId"], cycle["id"])
        self.assertEqual(cycle["latestCheck"]["project"], "projects/probe")
        live = self.source.snapshot(status=self.live_status())
        self.assertTrue(live["runtime"]["active"])
        self.assertTrue(live["runtime"]["elapsedReliable"])
        self.assertGreaterEqual(live["runtime"]["elapsedSeconds"], 0)
        self.assertEqual(live["runtime"]["startedAt"], live["cycles"][0]["startedAt"])

    def test_symlinked_source_files_and_ancestor_directories_are_not_exposed(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        secret = Path(outside.name) / "secret.txt"
        secret.write_text("private", encoding="utf-8")
        try:
            (self.root / "DELIVERY.md").symlink_to(secret)
            (self.root / "external").symlink_to(Path(outside.name), target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Creating test symlinks unavailable: {exc}")
        self.assertEqual(self.source.documents(), [])
        for path in ("DELIVERY.md", "external/secret.txt"):
            with self.assertRaises(ValueError):
                self.source.read(path)

    def test_ledger_and_document_size_boundaries_are_explicit(self):
        line = json.dumps(record()) + "\n"
        self.write("logs/usage.jsonl", line + json.dumps(record("cycle-0002")))
        with mock.patch.object(data_module, "MAX_LEDGER_BYTES", len(line.encode("utf-8")) + 5):
            records, warnings = self.source.ledger()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["cycle_id"], "cycle-0002")
        self.assertIn("ledger_truncated", warnings)
        self.write("DELIVERY.md", "# Delivery\n" + "x" * data_module.MAX_TEXT_BYTES)
        text, truncated = self.source.document("DELIVERY.md")
        self.assertTrue(truncated)
        self.assertLessEqual(len(text), data_module.MAX_TEXT_BYTES)

    def test_saved_language_and_locked_product_are_read_without_writes(self):
        path = self.write(".autonomous-company.local", "AUTONOMOUS_COMPANY_LANGUAGE=en\nAUTONOMOUS_COMPANY_PRODUCT_LANGUAGE=zh-CN\nAUTONOMOUS_COMPANY_PRODUCT_STATUS=active\n")
        before = path.read_bytes()
        language = data_module.JournalSource(self.root).language()
        self.assertEqual(language["language"], "zh-CN")
        self.assertEqual(language["nextLanguage"], "en")
        self.assertTrue(language["pending"])
        self.assertEqual(path.read_bytes(), before)

    def test_live_cycle_uses_reserved_identity_and_reports_unknown_usage(self):
        self.ledger(record())
        status = self.live_status()
        self.write("logs/cycle-0002-live.log", "provider is working")
        snapshot = self.source.snapshot(status=status)
        self.assertFalse(snapshot["readOnly"])
        self.assertEqual(snapshot["runtime"]["state"], "running")
        self.assertEqual(snapshot["runtime"]["currentCycleId"], "cycle-0002-live")
        self.assertEqual(snapshot["runtime"]["currentCycleNumber"], 2)
        active = snapshot["cycles"][0]
        self.assertTrue(active["active"])
        self.assertEqual(active["status"], "running")
        self.assertIsNone(active["endedAt"])
        self.assertIsNone(active["usage"]["totalTokens"])
        self.assertEqual(self.source.log(active["id"], status)["text"], "provider is working")
        self.assertIs(snapshot["status"], status)
        self.assertEqual(len(self.source.snapshot()["cycles"]), 1)

    def test_stale_mismatched_or_unverified_pending_never_becomes_live_cycle(self):
        self.ledger(record())
        for failure in ("status", "pid", "count", "previous_launch", "path"):
            with self.subTest(failure=failure):
                status = self.live_status()
                if failure == "status":
                    status["ok"] = False
                elif failure == "pid":
                    self.write(".auto-loop.pid", "9999\n")
                elif failure == "count":
                    self.write(".auto-loop-state", "STATUS=running\nLOOP_COUNT=1\nENGINE=codex\nMODEL=example-model\n")
                    status["stateFile"] = self.source.pairs(".auto-loop-state")
                elif failure == "previous_launch":
                    os.utime(self.root / "logs/usage.jsonl.pending", (1600000000, 1600000000))
                else:
                    self.write("logs/usage.jsonl.pending", json.dumps(record("../private", number=2)))
                snapshot = self.source.snapshot(status=status)
                self.assertEqual(len(snapshot["cycles"]), 1)
                self.assertIsNone(snapshot["runtime"]["currentCycleId"])
                self.assertIsNone(snapshot["runtime"]["currentCycleNumber"])
                with self.assertRaises(ValueError):
                    self.source.log("cycle-0002-live", status)

    def test_completed_reservation_is_not_duplicated_while_loop_finishes(self):
        status = self.live_status()
        self.ledger(record("cycle-0002-live", number=2))
        cycles = self.source.snapshot(status=status)["cycles"]
        self.assertEqual(len(cycles), 1)
        self.assertEqual(cycles[0]["status"], "completed")
        self.assertFalse(cycles[0]["active"])

    def test_runtime_failures_do_not_claim_stopped_and_phases_remain_distinct(self):
        status = self.live_status()
        status["ok"] = False
        status["raw"] = "Status command timed out"
        snapshot = self.source.snapshot(status=status)
        self.assertEqual(snapshot["runtime"]["state"], "unavailable")
        self.assertFalse(snapshot["runtime"]["available"])
        self.assertEqual(snapshot["runtime"]["error"], status["raw"])
        self.assertIn("runtime_unavailable", snapshot["warnings"])
        status["ok"] = True
        for phase in ("idle", "paused", "waiting_limit", "circuit_break", "failed", "unknown"):
            with self.subTest(phase=phase):
                status["parsed"]["loop"]["state"] = phase
                status["stateFile"]["STATUS"] = phase
                self.write(".auto-loop-state", "\n".join(f"{key}={value}" for key, value in status["stateFile"].items()))
                runtime = self.source.snapshot(status=status)["runtime"]
                self.assertEqual(runtime["state"], "unavailable" if phase == "unknown" else phase)
                self.assertIsNone(runtime["currentCycleId"])
        status["parsed"]["loop"].update(state="stopped", processState="stopped", pid=None)
        status["parsed"]["daemon"]["state"] = "failed"
        self.assertEqual(self.source.snapshot(status=status)["runtime"]["state"], "failed")

    def test_recorded_cost_and_budget_are_preserved_without_estimation(self):
        budget = {"state": "warning", "period": "day"}
        self.ledger(record(cost_usd=0.125, cost_usd_status="reported", budget=budget),
                    record("cycle-unknown", number=2, cost_usd=None, started_at="2026-09-18T13:00:00+08:00"))
        snapshot = self.source.snapshot()
        self.assertIsNone(snapshot["cycles"][0]["costUsd"])
        self.assertEqual(snapshot["cycles"][1]["costUsd"], 0.125)
        self.assertEqual(snapshot["cycles"][1]["budget"], budget)
        self.assertEqual(snapshot["recordedBudget"], budget)


if __name__ == "__main__":
    unittest.main()
