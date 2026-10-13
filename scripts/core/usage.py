#!/usr/bin/env python3
"""CLI for the structured cycle usage ledger."""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path
from typing import Any

from localization import message

from usage_lib import (
    UsageError,
    append_cycle_record,
    begin_cycle,
    build_cycle_record,
    check_budget,
    load_budget_config,
    read_pause_state,
    recover_pending_cycle,
    resume_budget,
    summarize_usage,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = REPO_ROOT / "logs" / "usage.jsonl"
DEFAULT_PAUSE_FILE = REPO_ROOT / ".auto-loop-budget-paused"


def _add_common_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--pause-file", type=Path, default=DEFAULT_PAUSE_FILE)


def _add_budget_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--budget-period", choices=("day", "week"))
    parser.add_argument("--warning-usd")
    parser.add_argument("--hard-usd")
    parser.add_argument("--warning-tokens")
    parser.add_argument("--hard-tokens")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Autonomous Company structured usage ledger")
    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record", help="append one completed Cycle record")
    _add_common_paths(record)
    _add_budget_args(record)
    record.add_argument("--cycle-id", required=True)
    record.add_argument("--cycle-number", required=True, type=int)
    record.add_argument("--started-at", required=True)
    record.add_argument("--ended-at", required=True)
    record.add_argument("--status", required=True)
    record.add_argument("--exit-code", required=True, type=int)
    record.add_argument("--engine", required=True)
    record.add_argument("--model", default="config-default")
    record.add_argument("--metadata-file", required=True, type=Path)
    record.add_argument("--result-format", choices=("json", "state"), default="json")

    check = subparsers.add_parser("check", help="validate budget configuration and gate startup against persisted usage")
    _add_common_paths(check)
    _add_budget_args(check)
    check.add_argument("--date", default=date.today().isoformat())
    check.add_argument("--result-format", choices=("json", "state"), default="json")

    begin = subparsers.add_parser("begin", help="persist a cycle identity before starting a provider")
    _add_common_paths(begin)
    begin.add_argument("--cycle-id", required=True)
    begin.add_argument("--cycle-number", required=True, type=int)
    begin.add_argument("--started-at", required=True)
    begin.add_argument("--engine", required=True)
    begin.add_argument("--model", default="config-default")

    recover = subparsers.add_parser("recover", help="record an unfinished cycle as interrupted with unknown usage")
    _add_common_paths(recover)
    _add_budget_args(recover)

    summary = subparsers.add_parser("summary", help="summarize a day or ISO week")
    summary.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    summary.add_argument("--period", choices=("day", "week"), default="day")
    summary.add_argument("--date", default=date.today().isoformat())
    summary.add_argument("--format", choices=("json", "text"), default="text")

    status = subparsers.add_parser("status", help="show persistent budget pause state")
    status.add_argument("--pause-file", type=Path, default=DEFAULT_PAUSE_FILE)
    status.add_argument("--format", choices=("json", "text"), default="text")

    resume = subparsers.add_parser("resume", help="manually clear a budget pause")
    resume.add_argument("--pause-file", type=Path, default=DEFAULT_PAUSE_FILE)
    return parser


def _budget_config(args: argparse.Namespace) -> dict[str, Any]:
    overrides = {
        "period": args.budget_period,
        "warning_usd": args.warning_usd,
        "hard_usd": args.hard_usd,
        "warning_tokens": args.warning_tokens,
        "hard_tokens": args.hard_tokens,
    }
    return load_budget_config(os.environ, **{k: v for k, v in overrides.items() if v is not None})


def _format_metric(label: str, metric: dict[str, Any], prefix: str = "") -> str:
    value = "unknown" if metric["value"] is None else f"{prefix}{metric['value']:,}"
    coverage = f"{metric['known_cycles']} known / {metric['unknown_cycles']} unknown"
    return f"{label:<14} {value:<18} {metric['status']} ({coverage})"


def _summary_text(summary: dict[str, Any]) -> str:
    rows = [
        f"Usage summary: {summary['period']} {summary['start_date']}..{summary['end_date']}",
        f"Cycles: {summary['cycles']} | Invalid records: {summary['invalid_records']}",
        _format_metric("Cost USD", summary["cost_usd"], prefix="$"),
        _format_metric("Input tokens", summary["usage"]["input_tokens"]),
        _format_metric("Output tokens", summary["usage"]["output_tokens"]),
        _format_metric("Total tokens", summary["usage"]["total_tokens"]),
    ]
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "begin":
            begin_cycle(args.ledger, build_cycle_record(
                cycle_id=args.cycle_id, cycle_number=args.cycle_number,
                started_at=args.started_at, ended_at=args.started_at,
                status="interrupted", exit_code=130, engine=args.engine, model=args.model, metadata_raw="{}",
            ))
            return 0

        if args.command == "recover":
            recover_pending_cycle(args.ledger, budget_config=_budget_config(args), pause_path=args.pause_file)
            return 0

        if args.command == "check":
            budget = check_budget(args.ledger, budget_config=_budget_config(args), pause_path=args.pause_file, target_date=args.date)
            print(budget["state"] if args.result_format == "state" else json.dumps(budget, ensure_ascii=False, indent=2))
            return 0

        if args.command == "record":
            metadata = args.metadata_file.read_text(encoding="utf-8", errors="replace")
            record = build_cycle_record(
                cycle_id=args.cycle_id,
                cycle_number=args.cycle_number,
                started_at=args.started_at,
                ended_at=args.ended_at,
                status=args.status,
                exit_code=args.exit_code,
                engine=args.engine,
                model=args.model,
                metadata_raw=metadata,
            )
            record = append_cycle_record(
                args.ledger,
                record,
                budget_config=_budget_config(args),
                pause_path=args.pause_file,
            )
            if args.result_format == "state":
                print(record["budget"]["state"])
            else:
                print(json.dumps(record, ensure_ascii=False, indent=2))
            return 0

        if args.command == "summary":
            summary = summarize_usage(args.ledger, period=args.period, target_date=args.date)
            print(
                json.dumps(summary, ensure_ascii=False, indent=2)
                if args.format == "json"
                else _summary_text(summary)
            )
            return 0

        if args.command == "status":
            state = read_pause_state(args.pause_file)
            payload = {"paused": state is not None, "details": state}
            if args.format == "json":
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            elif state is None:
                print(message(REPO_ROOT, "budget.inactive"))
            else:
                print(message(REPO_ROOT, "budget.active"))
                print(json.dumps(state, ensure_ascii=False, indent=2))
                print(message(REPO_ROOT, "budget.paused", state.get("reason", "usage_budget")))
            return 0

        if args.command == "resume":
            removed = resume_budget(args.pause_file)
            print(message(REPO_ROOT, "budget.resumed" if removed else "budget.not_paused"))
            return 0
    except (OSError, UsageError) as exc:
        print(f"usage error: {exc}", file=os.sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    if hasattr(os.sys.stdout, "reconfigure"):
        os.sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
