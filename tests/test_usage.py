import json
import sys
import subprocess
import tempfile
import unittest
from datetime import datetime
from unittest import mock
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from usage_lib import (  # noqa: E402
    UsageError,
    append_cycle_record,
    begin_cycle,
    build_cycle_record,
    check_budget,
    load_budget_config,
    normalize_engine_metadata,
    read_pause_state,
    recover_pending_cycle,
    read_usage_records,
    resume_budget,
    summarize_usage,
)


def make_record(
    cycle_number: int,
    ended_at: str,
    *,
    engine: str = "claude",
    metadata: dict | str | None = None,
) -> dict:
    raw = metadata if isinstance(metadata, str) else json.dumps(metadata or {})
    return build_cycle_record(
        cycle_id=f"cycle-{cycle_number}",
        cycle_number=cycle_number,
        started_at=ended_at,
        ended_at=ended_at,
        status="completed",
        exit_code=0,
        engine=engine,
        model="test-model",
        metadata_raw=raw,
    )


class UsageLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.ledger = root / "logs" / "usage.jsonl"
        self.pause = root / ".auto-loop-budget-paused"
        self.no_budget = load_budget_config({})

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def append(self, record: dict, config: dict | None = None) -> dict:
        return append_cycle_record(
            self.ledger,
            record,
            budget_config=config or self.no_budget,
            pause_path=self.pause,
        )

    def test_cross_day_and_historical_date_summary(self) -> None:
        self.append(
            make_record(
                1,
                "2026-08-31T23:59:00+08:00",
                metadata={
                    "usage": {"input_tokens": 10, "output_tokens": 5},
                    "total_cost_usd": 0.2,
                },
            )
        )
        self.append(
            make_record(
                2,
                "2026-09-01T00:01:00+08:00",
                metadata={
                    "usage": {"input_tokens": 20, "output_tokens": 7},
                    "total_cost_usd": 0.3,
                },
            )
        )

        august = summarize_usage(
            self.ledger, period="day", target_date="2026-08-31"
        )
        september = summarize_usage(
            self.ledger, period="day", target_date="2026-09-01"
        )
        self.assertEqual(august["cycles"], 1)
        self.assertEqual(august["usage"]["total_tokens"]["value"], 15)
        self.assertEqual(september["cycles"], 1)
        self.assertEqual(september["cost_usd"]["value"], 0.3)

    def test_clock_rollback_preserves_usage_and_observed_calendar_dates(self) -> None:
        record = build_cycle_record(
            cycle_id="clock-rollback", cycle_number=1,
            started_at="2026-09-02T00:00:02+08:00", ended_at="2026-09-01T23:59:58+08:00",
            status="completed", exit_code=0, engine="claude", model="test-model",
            metadata_raw='{"total_tokens":100,"cost_usd":1.25}',
        )
        with self.assertLogs("usage_lib", level="WARNING") as warning:
            self.append(record, load_budget_config({"USAGE_HARD_LIMIT_USD": "1"}))
        self.assertIn("wall-clock rollback", warning.output[0])
        self.assertEqual(record["clock_anomaly"]["wall_clock_delta_seconds"], -4)
        self.assertEqual(record["started_at"], "2026-09-02T00:00:02+08:00")
        self.assertEqual(record["ended_at"], "2026-09-01T23:59:58+08:00")
        self.assertEqual(record["budget"]["state"], "hard_limit")
        self.assertEqual(summarize_usage(self.ledger, period="day", target_date="2026-09-01")["usage"]["total_tokens"]["value"], 100)
        self.assertEqual(summarize_usage(self.ledger, period="day", target_date="2026-09-02")["cycles"], 0)

    def test_pending_recovery_after_clock_rollback_keeps_unknown_usage(self) -> None:
        record = make_record(1, "2026-09-10T00:00:02+08:00")
        begin_cycle(self.ledger, record)
        config = load_budget_config({"USAGE_HARD_LIMIT_TOKENS": "100"})
        earlier = datetime.fromisoformat("2026-09-09T23:59:57+08:00")
        with mock.patch("usage_lib.datetime") as clock:
            clock.fromisoformat.side_effect = datetime.fromisoformat
            clock.now.return_value = earlier
            with self.assertLogs("usage_lib", level="WARNING"):
                budget = check_budget(self.ledger, budget_config=config, pause_path=self.pause, target_date="2026-09-09")
        records, errors = read_usage_records(self.ledger)
        self.assertFalse(errors)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "interrupted")
        self.assertEqual(records[0]["clock_anomaly"]["wall_clock_delta_seconds"], -5)
        self.assertEqual(budget["state"], "unverifiable")
        self.assertEqual(budget["start_date"], "2026-09-09")
        self.assertEqual(summarize_usage(self.ledger, period="day", target_date="2026-09-10")["cycles"], 0)
        self.assertIsNone(records[0]["usage"]["total_tokens"])
        self.assertIsNone(records[0]["cost_usd"])
        self.assertEqual(read_pause_state(self.pause)["reason"], "budget_unverifiable")
        self.assertFalse(self.ledger.with_name(self.ledger.name + ".pending").exists())

    def test_week_summary_uses_monday_through_sunday(self) -> None:
        for cycle, timestamp, tokens in (
            (1, "2026-08-31T12:00:00+08:00", 10),
            (2, "2026-09-06T12:00:00+08:00", 20),
            (3, "2026-09-07T12:00:00+08:00", 40),
        ):
            self.append(
                make_record(
                    cycle,
                    timestamp,
                    metadata={"usage": {"input_tokens": tokens, "output_tokens": 1}},
                )
            )
        summary = summarize_usage(
            self.ledger, period="week", target_date="2026-09-02"
        )
        self.assertEqual(summary["start_date"], "2026-08-31")
        self.assertEqual(summary["end_date"], "2026-09-06")
        self.assertEqual(summary["cycles"], 2)
        self.assertEqual(summary["usage"]["input_tokens"]["value"], 30)

    def test_missing_price_remains_unknown_not_zero(self) -> None:
        config = load_budget_config({"USAGE_WARNING_USD": "1"})
        record = self.append(
            make_record(
                1,
                "2026-09-02T10:00:00+08:00",
                metadata={"usage": {"input_tokens": 100, "output_tokens": 25}},
            ),
            config,
        )
        self.assertIsNone(record["cost_usd"])
        self.assertEqual(record["cost_usd_status"], "unavailable")
        summary = summarize_usage(
            self.ledger, period="day", target_date="2026-09-02"
        )
        self.assertIsNone(summary["cost_usd"]["value"])
        self.assertEqual(summary["cost_usd"]["status"], "unavailable")
        self.assertEqual(record["budget"]["state"], "indeterminate")
        self.assertFalse(self.pause.exists())

    def test_codex_na_metadata_remains_unknown(self) -> None:
        normalized = normalize_engine_metadata("codex", "N/A")
        self.assertEqual(normalized["usage"]["status"], "unavailable")
        self.assertIsNone(normalized["usage"]["input_tokens"])
        self.assertIsNone(normalized["usage"]["output_tokens"])
        self.assertIsNone(normalized["usage"]["total_tokens"])
        self.assertIsNone(normalized["cost_usd"])

    def test_codex_jsonl_usage_is_read_without_log_regex(self) -> None:
        metadata = "\n".join(
            (
                json.dumps({"type": "turn.started"}),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {"input_tokens": 80, "output_tokens": 20},
                    }
                ),
            )
        )
        normalized = normalize_engine_metadata("codex", metadata)
        self.assertEqual(normalized["usage"]["total_tokens"], 100)
        self.assertIsNone(normalized["cost_usd"])
        self.assertEqual(normalized["source"]["adapter"], "codex_jsonl")

    def test_local_model_standard_metadata_keeps_tokens_without_price(self) -> None:
        record = make_record(
            1,
            "2026-09-02T10:00:00+08:00",
            engine="local",
            metadata={
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 8,
                    "total_tokens": 20,
                }
            },
        )
        self.assertEqual(record["engine"], "local")
        self.assertEqual(record["usage"]["total_tokens"], 20)
        self.assertIsNone(record["cost_usd"])
        self.assertEqual(record["source"]["adapter"], "standard_json")

    def test_engine_adapter_sidecar_is_the_usage_boundary(self) -> None:
        sidecar = {
            "schema_version": 1,
            "engine": "cursor",
            "status": "success",
            "cycle_outcome": "success",
            "failure_reason": "",
            "result": "done",
            "cost_usd": 0.25,
            "input_tokens": 21,
            "output_tokens": 9,
            "total_tokens": 30,
            "subtype": "success",
            "type": "cursor_exec",
            "exit_code": 0,
            "timed_out": False,
        }
        record = make_record(
            1,
            "2026-09-02T10:00:00+08:00",
            engine="cursor",
            metadata=sidecar,
        )
        self.assertEqual(record["usage"]["input_tokens"], 21)
        self.assertEqual(record["usage"]["output_tokens"], 9)
        self.assertEqual(record["usage"]["total_tokens"], 30)
        self.assertEqual(record["cost_usd"], 0.25)
        self.assertEqual(record["source"]["adapter"], "cycle_sidecar_v1")

    def test_warning_threshold_alerts_without_pause(self) -> None:
        config = load_budget_config(
            {"USAGE_WARNING_TOKENS": "100", "USAGE_HARD_LIMIT_TOKENS": "200"}
        )
        record = self.append(
            make_record(
                1,
                "2026-09-02T10:00:00+08:00",
                metadata={"usage": {"input_tokens": 80, "output_tokens": 30}},
            ),
            config,
        )
        self.assertEqual(record["budget"]["state"], "warning")
        self.assertFalse(self.pause.exists())

    def test_hard_metric_unknown_pauses_but_unconfigured_cost_does_not(self) -> None:
        record = make_record(1, "2026-09-02T10:00:00+08:00", metadata={"total_tokens": 10})
        recorded = self.append(record, load_budget_config({"USAGE_HARD_LIMIT_TOKENS": "100"}))
        self.assertEqual(recorded["budget"]["state"], "ok")
        self.assertFalse(self.pause.exists())
        second = make_record(2, "2026-09-02T10:01:00+08:00", metadata={"total_tokens": 10})
        recorded = self.append(second, load_budget_config({"USAGE_HARD_LIMIT_USD": "100"}))
        self.assertEqual(recorded["budget"]["state"], "unverifiable")
        self.assertEqual(read_pause_state(self.pause)["reason"], "budget_unverifiable")

    def test_replaying_same_cycle_is_idempotent_and_conflicts_are_rejected(self) -> None:
        record = make_record(1, "2026-09-02T10:00:00+08:00", metadata={"total_tokens": 10})
        self.append(record)
        self.append(record)
        self.assertEqual(len(self.ledger.read_text().splitlines()), 1)
        conflict = make_record(1, "2026-09-02T10:00:00+08:00", metadata={"total_tokens": 20})
        with self.assertRaises(UsageError):
            self.append(conflict)

    def test_corrupt_ledger_is_not_silently_ignored_when_appending(self) -> None:
        self.ledger.parent.mkdir()
        self.ledger.write_text('{"kind":"cycle_usage","usage":null}\n')
        record = make_record(1, "2026-09-02T10:00:00+08:00")
        with self.assertRaises(UsageError):
            self.append(record)

    def test_startup_reconstructs_pause_and_resume_is_consumed_once(self) -> None:
        record = make_record(1, "2026-09-02T10:00:00+08:00", metadata={"total_tokens": 110})
        self.append(record)
        config = load_budget_config({"USAGE_HARD_LIMIT_TOKENS": "100"})
        def check() -> dict:
            return check_budget(self.ledger, budget_config=config, pause_path=self.pause, target_date="2026-09-02")
        self.assertEqual(check()["state"], "hard_limit")
        self.assertTrue(self.pause.exists())
        self.assertTrue(resume_budget(self.pause))
        check()
        self.assertFalse(self.pause.exists())
        check()
        self.assertTrue(self.pause.exists())
        resume_budget(self.pause)
        self.append(make_record(2, "2026-09-02T10:01:00+08:00", metadata={"total_tokens": 1}))
        check()
        self.assertTrue(self.pause.exists(), "resume may not acknowledge a changed ledger")

    def test_empty_ledger_does_not_count_as_missing_reported_usage(self) -> None:
        budget = check_budget(self.ledger, budget_config=load_budget_config({"USAGE_HARD_LIMIT_USD": "10"}), pause_path=self.pause, target_date="2026-09-02")
        self.assertEqual(budget["state"], "ok")
        self.assertFalse(self.pause.exists())

    def test_pre_dispatch_checks_preserve_one_use_budget_resume(self) -> None:
        self.append(make_record(1, "2026-09-02T10:00:00+08:00", metadata={"total_tokens": 110}))
        config = load_budget_config({"USAGE_HARD_LIMIT_TOKENS": "100"})
        args = {"budget_config": config, "pause_path": self.pause, "target_date": "2026-09-02"}
        check_budget(self.ledger, **args)
        self.assertTrue(resume_budget(self.pause))
        acknowledgement = self.pause.with_name(self.pause.name + ".resume")
        for _ in range(2):
            check_budget(self.ledger, **args, consume_resume=False)
            self.assertTrue(acknowledgement.exists())
            self.assertFalse(self.pause.exists())
        check_budget(self.ledger, **args)
        self.assertFalse(acknowledgement.exists())
        self.assertFalse(self.pause.exists())
        check_budget(self.ledger, **args)
        self.assertTrue(self.pause.exists())

    def test_budget_configuration_rejects_invalid_numbers_and_inverted_thresholds(self) -> None:
        for values in ({"USAGE_HARD_LIMIT_USD": "NaN"}, {"USAGE_HARD_LIMIT_USD": "-1"},
                       {"USAGE_HARD_LIMIT_TOKENS": "1.5"}, {"USAGE_WARNING_USD": "20", "USAGE_HARD_LIMIT_USD": "10"}):
            with self.subTest(values=values), self.assertRaises(UsageError):
                load_budget_config(values)

    def test_reports_deduplicate_replayed_rows_and_reject_conflicting_rows(self) -> None:
        recorded = self.append(make_record(1, "2026-09-02T10:00:00+08:00", metadata={"total_tokens": 10}))
        with self.ledger.open("a") as handle:
            handle.write(json.dumps(recorded) + "\n")
            conflict = dict(recorded, usage={"total_tokens": 999})
            handle.write(json.dumps(conflict) + "\n")
        summary = summarize_usage(self.ledger, period="day", target_date="2026-09-02")
        self.assertEqual(summary["cycles"], 1)
        self.assertEqual(summary["usage"]["total_tokens"]["value"], 10)
        self.assertEqual(summary["invalid_records"], 1)

    def test_unfinished_cycle_recovers_once_with_unknown_usage(self) -> None:
        record = make_record(1, "2026-09-02T10:00:00+08:00")
        record.update(status="interrupted", exit_code=130)
        begin_cycle(self.ledger, record)
        config = load_budget_config({"USAGE_HARD_LIMIT_TOKENS": "100"})
        recover_pending_cycle(self.ledger, budget_config=config, pause_path=self.pause)
        recover_pending_cycle(self.ledger, budget_config=config, pause_path=self.pause)
        records, errors = read_usage_records(self.ledger)
        self.assertFalse(errors)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "interrupted")
        self.assertIsNone(records[0]["usage"]["total_tokens"])
        self.assertEqual(read_pause_state(self.pause)["reason"], "budget_unverifiable")

    def test_recovery_does_not_duplicate_cycle_committed_before_crash(self) -> None:
        record = make_record(1, "2026-09-02T10:00:00+08:00", metadata={"total_tokens": 10})
        self.append(record)
        pending = dict(record, status="interrupted", usage={field: None for field in ("input_tokens", "output_tokens", "total_tokens")})
        begin_cycle(self.ledger, pending)
        recover_pending_cycle(self.ledger, budget_config=self.no_budget, pause_path=self.pause)
        records, errors = read_usage_records(self.ledger)
        self.assertFalse(errors)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["usage"]["total_tokens"], 10)

    def test_parallel_replays_append_only_one_complete_row(self) -> None:
        metadata = Path(self.tempdir.name) / "metadata.json"
        metadata.write_text('{"total_tokens":10}', encoding="utf-8")
        command = [
            sys.executable, str(CORE_DIR / "usage.py"), "record",
            "--ledger", str(self.ledger), "--pause-file", str(self.pause),
            "--metadata-file", str(metadata), "--cycle-id", "parallel-cycle", "--cycle-number", "1",
            "--started-at", "2026-09-02T10:00:00+08:00", "--ended-at", "2026-09-02T10:01:00+08:00",
            "--status", "completed", "--exit-code", "0", "--engine", "codex",
        ]
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(4)]
        for process in processes:
            output = process.communicate(timeout=15)
            self.assertEqual(process.returncode, 0, output)
        records, errors = read_usage_records(self.ledger)
        self.assertFalse(errors)
        self.assertEqual(len(records), 1)
        self.assertEqual(len(self.ledger.read_text().splitlines()), 1)

    def test_hard_limit_records_cycle_then_persists_pause_until_manual_resume(self) -> None:
        config = load_budget_config({"USAGE_HARD_LIMIT_USD": "1.00"})
        record = self.append(
            make_record(
                1,
                "2026-09-02T10:00:00+08:00",
                metadata={
                    "usage": {"input_tokens": 100, "output_tokens": 20},
                    "total_cost_usd": 1.25,
                },
            ),
            config,
        )
        records, errors = read_usage_records(self.ledger)
        self.assertFalse(errors)
        self.assertEqual(records[-1]["cycle_id"], record["cycle_id"])
        self.assertEqual(record["budget"]["state"], "hard_limit")
        self.assertEqual(read_pause_state(self.pause)["reason"], "usage_hard_limit")
        self.assertTrue(resume_budget(self.pause))
        self.assertIsNone(read_pause_state(self.pause))


if __name__ == "__main__":
    unittest.main()
