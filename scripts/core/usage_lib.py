"""Structured cycle usage ledger, aggregation, and budget policy.

The ledger contract is intentionally engine-neutral. Vendor-specific metadata is
normalized at this boundary; dashboards and budget policy only consume the
standard fields written to ``logs/usage.jsonl``.
"""

from __future__ import annotations

import json
import hashlib
import logging
import math
import os
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = 1
RECORD_KIND = "cycle_usage"
TOKEN_FIELDS = ("input_tokens", "output_tokens", "total_tokens")


class UsageError(ValueError):
    """Raised when a usage command receives an invalid contract value."""


def _non_negative_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return int(parsed) if parsed.is_finite() and parsed >= 0 and parsed == parsed.to_integral_value() else None


def _non_negative_decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return parsed if parsed.is_finite() and parsed >= 0 and math.isfinite(float(parsed)) else None


def _number_for_json(value: Decimal | None) -> float | int | None:
    if value is None:
        return None
    return int(value) if value == value.to_integral_value() else float(value)


def _json_documents(raw: str) -> list[Any]:
    stripped = raw.strip()
    if not stripped:
        return []
    try:
        document = json.loads(stripped)
    except json.JSONDecodeError:
        documents: list[Any] = []
        for line in stripped.splitlines():
            try:
                documents.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return documents
    return document if isinstance(document, list) else [document]


def _walk_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _find_usage(documents: list[Any]) -> dict[str, Any] | None:
    candidate: dict[str, Any] | None = None
    for document in documents:
        for item in _walk_dicts(document):
            usage = item.get("usage")
            if isinstance(usage, dict) and any(
                field in usage for field in TOKEN_FIELDS
            ):
                candidate = usage
            elif any(field in item for field in TOKEN_FIELDS):
                # Engine Adapter cycle sidecars expose normalized token fields
                # at the top level. Usage consumers deliberately accept that
                # stable boundary instead of reparsing provider output.
                candidate = item
    return candidate


def _uses_cycle_sidecar(documents: list[Any]) -> bool:
    return any(
        isinstance(document, dict)
        and document.get("schema_version") == 1
        and "cycle_outcome" in document
        and "engine" in document
        for document in documents
    )


def _find_cost(documents: list[Any]) -> Decimal | None:
    candidate: Decimal | None = None
    for document in documents:
        for item in _walk_dicts(document):
            for field in ("total_cost_usd", "cost_usd"):
                if field in item:
                    parsed = _non_negative_decimal(item[field])
                    if parsed is not None:
                        candidate = parsed
    return candidate


def normalize_engine_metadata(engine: str, raw: str) -> dict[str, Any]:
    """Map current Claude/Codex or adapter-like JSON onto the stable contract.

    No price table is used. Cost is present only when the engine reports a USD
    amount. Unknown values remain ``None`` and are never converted to zero.
    """

    documents = _json_documents(raw)
    usage_source = _find_usage(documents)
    usage = {field: None for field in TOKEN_FIELDS}
    if usage_source is not None:
        usage["input_tokens"] = _non_negative_int(usage_source.get("input_tokens"))
        usage["output_tokens"] = _non_negative_int(usage_source.get("output_tokens"))
        usage["total_tokens"] = _non_negative_int(usage_source.get("total_tokens"))
        if usage["total_tokens"] is None:
            input_tokens = usage["input_tokens"]
            output_tokens = usage["output_tokens"]
            if input_tokens is not None and output_tokens is not None:
                usage["total_tokens"] = input_tokens + output_tokens

    known_usage = sum(usage[field] is not None for field in TOKEN_FIELDS)
    if known_usage == 0:
        usage_status = "unavailable"
    elif known_usage == len(TOKEN_FIELDS):
        usage_status = "reported"
    else:
        usage_status = "partial"
    usage["status"] = usage_status

    cost = _find_cost(documents)
    engine_name = engine.strip().lower() or "unknown"
    if _uses_cycle_sidecar(documents):
        adapter = "cycle_sidecar_v1"
    elif engine_name == "claude":
        adapter = "claude_json"
    elif engine_name == "codex":
        adapter = "codex_jsonl"
    else:
        adapter = "standard_json"

    return {
        "usage": usage,
        "cost_usd": _number_for_json(cost),
        "cost_usd_status": "reported" if cost is not None else "unavailable",
        "source": {"type": "engine_metadata", "adapter": adapter},
    }


def _parse_iso_datetime(value: str, field: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise UsageError(f"{field} must be an ISO-8601 timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise UsageError(f"{field} must include a UTC offset: {value}")
    return parsed


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise UsageError(f"date must use YYYY-MM-DD: {value}") from exc


def build_cycle_record(
    *,
    cycle_id: str,
    cycle_number: int,
    started_at: str,
    ended_at: str,
    status: str,
    exit_code: int,
    engine: str,
    model: str,
    metadata_raw: str,
) -> dict[str, Any]:
    if not cycle_id.strip():
        raise UsageError("cycle_id must not be empty")
    if cycle_number < 1:
        raise UsageError("cycle_number must be positive")
    started = _parse_iso_datetime(started_at, "started_at")
    ended = _parse_iso_datetime(ended_at, "ended_at")
    normalized = normalize_engine_metadata(engine, metadata_raw)
    record = {
        "schema_version": SCHEMA_VERSION,
        "kind": RECORD_KIND,
        "cycle_id": cycle_id,
        "cycle_number": cycle_number,
        "started_at": started_at,
        "ended_at": ended_at,
        "status": status,
        "exit_code": exit_code,
        "engine": engine.strip().lower() or "unknown",
        "model": model or "config-default",
        "usage": normalized["usage"],
        "cost_usd": normalized["cost_usd"],
        "cost_usd_status": normalized["cost_usd_status"],
        "source": normalized["source"],
    }
    if ended < started:
        # Wall clocks can move backwards after host/VM synchronization. Keep
        # observed timestamps and book usage on its actual completion date;
        # timestamps alone cannot establish an elapsed duration.
        record["clock_anomaly"] = {
            "type": "wall_clock_rollback",
            "wall_clock_delta_seconds": (ended - started).total_seconds(),
        }
    return record


def _cycle_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "budget"}


def read_usage_records(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        rows = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return records, errors
    except UnicodeError:
        return records, ["usage ledger is not valid UTF-8"]

    seen: dict[str, dict[str, Any]] = {}
    for line_number, row in enumerate(rows, start=1):
        if not row.strip():
            continue
        try:
            record = json.loads(row)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON ({exc.msg})")
            continue
        if not isinstance(record, dict) or record.get("kind") != RECORD_KIND:
            errors.append(f"line {line_number}: unsupported usage record")
            continue
        try:
            cycle_id = record.get("cycle_id")
            if not isinstance(cycle_id, str) or not cycle_id.strip() or record.get("schema_version") != SCHEMA_VERSION:
                raise UsageError("invalid cycle identity or schema version")
            _parse_iso_datetime(str(record.get("ended_at", "")), "ended_at")
            usage = record.get("usage")
            if not isinstance(usage, dict):
                raise UsageError("usage must be an object")
            for field in TOKEN_FIELDS:
                if usage.get(field) is not None and _non_negative_int(usage[field]) is None:
                    raise UsageError("invalid token amount")
            if record.get("cost_usd") is not None and _non_negative_decimal(record["cost_usd"]) is None:
                raise UsageError("invalid cost amount")
            if cycle_id in seen:
                if _cycle_payload(record) != _cycle_payload(seen[cycle_id]):
                    raise UsageError("conflicting duplicate cycle_id")
                continue
        except UsageError:
            errors.append(f"line {line_number}: invalid or conflicting usage record")
            continue
        seen[cycle_id] = record
        records.append(record)
    return records, errors


def _period_bounds(period: str, target: date) -> tuple[date, date]:
    if period == "day":
        return target, target
    if period == "week":
        start = target - timedelta(days=target.weekday())
        return start, start + timedelta(days=6)
    raise UsageError("period must be 'day' or 'week'")


def _metric_summary(records: list[dict[str, Any]], extractor: Any) -> dict[str, Any]:
    values: list[Decimal] = []
    for record in records:
        parsed = _non_negative_decimal(extractor(record))
        if parsed is not None:
            values.append(parsed)
    known = len(values)
    unknown = len(records) - known
    if known == 0:
        status = "unavailable"
        value: float | int | None = None
    else:
        status = "complete" if unknown == 0 else "partial"
        total = sum(values, Decimal("0"))
        value = int(total) if total == total.to_integral_value() else float(total)
    return {
        "value": value,
        "status": status,
        "known_cycles": known,
        "unknown_cycles": unknown,
    }


def summarize_records(
    records: list[dict[str, Any]],
    *,
    period: str,
    target_date: str | date,
    invalid_records: int = 0,
) -> dict[str, Any]:
    target = _parse_date(target_date)
    start, end = _period_bounds(period, target)
    selected: list[dict[str, Any]] = []
    for record in records:
        try:
            record_date = _parse_iso_datetime(str(record["ended_at"]), "ended_at").date()
        except (KeyError, UsageError):
            continue
        if start <= record_date <= end:
            selected.append(record)

    usage = {
        field: _metric_summary(
            selected,
            lambda record, token_field=field: record.get("usage", {}).get(token_field),
        )
        for field in TOKEN_FIELDS
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "period": period,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "cycles": len(selected),
        "cost_usd": _metric_summary(selected, lambda record: record.get("cost_usd")),
        "usage": usage,
        "latest_budget": selected[-1].get("budget") if selected else None,
        "invalid_records": invalid_records,
    }


def summarize_usage(path: Path, *, period: str, target_date: str | date) -> dict[str, Any]:
    records, errors = read_usage_records(path)
    summary = summarize_records(
        records,
        period=period,
        target_date=target_date,
        invalid_records=len(errors),
    )
    if errors:
        summary["diagnostics"] = errors
    return summary


def _threshold(value: Any, name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    parsed = _non_negative_decimal(value)
    if parsed is None or parsed == 0:
        raise UsageError(f"{name} must be a positive number")
    return parsed


def load_budget_config(
    env: Mapping[str, str] | None = None, **overrides: Any
) -> dict[str, Any]:
    source = os.environ if env is None else env
    period = str(overrides.get("period") or source.get("USAGE_BUDGET_PERIOD", "day"))
    if period not in {"day", "week"}:
        raise UsageError("USAGE_BUDGET_PERIOD must be 'day' or 'week'")

    values = {
        "warning_usd": overrides.get("warning_usd", source.get("USAGE_WARNING_USD")),
        "hard_usd": overrides.get("hard_usd", source.get("USAGE_HARD_LIMIT_USD")),
        "warning_tokens": overrides.get(
            "warning_tokens", source.get("USAGE_WARNING_TOKENS")
        ),
        "hard_tokens": overrides.get(
            "hard_tokens", source.get("USAGE_HARD_LIMIT_TOKENS")
        ),
    }
    config = {
        "period": period,
        **{name: _threshold(value, name) for name, value in values.items()},
    }
    for metric in ("usd", "tokens"):
        warning, hard = config[f"warning_{metric}"], config[f"hard_{metric}"]
        if warning is not None and hard is not None and warning > hard:
            raise UsageError(f"warning_{metric} must not exceed hard_{metric}")
    for name in ("warning_tokens", "hard_tokens"):
        if config[name] is not None and config[name] != config[name].to_integral_value():
            raise UsageError(f"{name} must be an integer")
    return config


def evaluate_budget(summary: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    limits = {
        name: _number_for_json(config.get(name))
        for name in ("warning_usd", "hard_usd", "warning_tokens", "hard_tokens")
    }
    if all(value is None for value in limits.values()):
        return {
            "state": "disabled",
            "period": config["period"],
            "start_date": summary["start_date"],
            "end_date": summary["end_date"],
            "limits": limits,
            "alerts": [],
        }

    metrics = {
        "cost_usd": summary["cost_usd"],
        "total_tokens": summary["usage"]["total_tokens"],
    }
    checks = (
        ("cost_usd", "hard", config.get("hard_usd")),
        ("total_tokens", "hard", config.get("hard_tokens")),
        ("cost_usd", "warning", config.get("warning_usd")),
        ("total_tokens", "warning", config.get("warning_tokens")),
    )
    alerts: list[dict[str, Any]] = []
    indeterminate = False
    unverifiable: list[str] = []
    for metric_name, level, limit in checks:
        if limit is None:
            continue
        metric = metrics[metric_name]
        actual = _non_negative_decimal(metric["value"])
        if summary["cycles"] == 0:
            continue
        if level == "hard" and (actual is None or metric["unknown_cycles"]):
            unverifiable.append(metric_name)
        if actual is None:
            indeterminate = True
            continue
        if metric["unknown_cycles"]:
            indeterminate = True
        if actual >= limit:
            alerts.append(
                {
                    "level": level,
                    "metric": metric_name,
                    "actual": _number_for_json(actual),
                    "limit": _number_for_json(limit),
                    "coverage": metric["status"],
                }
            )

    if any(alert["level"] == "hard" for alert in alerts):
        state = "hard_limit"
    elif unverifiable:
        state = "unverifiable"
    elif any(alert["level"] == "warning" for alert in alerts):
        state = "warning"
    elif indeterminate:
        state = "indeterminate"
    else:
        state = "ok"
    return {
        "state": state,
        "period": config["period"],
        "start_date": summary["start_date"],
        "end_date": summary["end_date"],
        "limits": limits,
        "alerts": alerts,
        "unverifiable_metrics": unverifiable,
    }


def _ledger_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(131072), b""):
                digest.update(chunk)
    except FileNotFoundError:
        pass
    return digest.hexdigest()


def _write_pause_marker(path: Path, record: dict[str, Any], ledger_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    marker = {
        "reason": "budget_unverifiable" if record["budget"]["state"] == "unverifiable" else "usage_hard_limit",
        "paused_at": record["ended_at"],
        "cycle_id": record["cycle_id"],
        "budget": record["budget"],
        "ledger_fingerprint": _ledger_fingerprint(ledger_path),
    }
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


@contextmanager
def _ledger_lock(path: Path) -> Iterable[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_name(path.name + ".lock").open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def append_cycle_record(
    path: Path,
    record: dict[str, Any],
    *,
    budget_config: dict[str, Any],
    pause_path: Path,
    reconcile_budget: bool = False,
) -> dict[str, Any]:
    with _ledger_lock(path):
        result = _append_cycle_record_locked(path, record, budget_config=budget_config, pause_path=pause_path,
                                             reconcile_budget=reconcile_budget)
        pending_path = path.with_name(path.name + ".pending")
        pending = read_pause_state(pending_path)
        if pending is not None and pending.get("cycle_id") == record["cycle_id"]:
            pending_path.unlink()
        return result


def _append_cycle_record_locked(
    path: Path,
    record: dict[str, Any],
    *,
    budget_config: dict[str, Any],
    pause_path: Path,
    reconcile_budget: bool = False,
) -> dict[str, Any]:
    existing, errors = read_usage_records(path)
    if errors:
        raise UsageError("usage ledger contains invalid records; repair it before recording another cycle")
    duplicates = [item for item in existing if item["cycle_id"] == record["cycle_id"]]
    if duplicates and _cycle_payload(duplicates[0]) != _cycle_payload(record):
        raise UsageError("cycle_id already exists with different usage data")
    record_date = _parse_iso_datetime(record["ended_at"], "ended_at").date()
    summary = summarize_records(
        existing if duplicates else existing + [record],
        period=budget_config["period"],
        target_date=record_date,
        invalid_records=len(errors),
    )
    record["budget"] = evaluate_budget(summary, budget_config)

    path.parent.mkdir(parents=True, exist_ok=True)
    if not duplicates:
        needs_newline = False
        if path.exists() and path.stat().st_size > 0:
            with path.open("rb") as handle:
                handle.seek(-1, os.SEEK_END)
                needs_newline = handle.read(1) != b"\n"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            if needs_newline:
                handle.write("\n")
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if record.get("clock_anomaly"):
            logging.getLogger(__name__).warning(
                "Cycle %s recorded despite wall-clock rollback (%s seconds); "
                "observed timestamps and usage were preserved",
                record["cycle_id"], record["clock_anomaly"]["wall_clock_delta_seconds"],
            )
    if reconcile_budget:
        # Harness intents can replay after resume or in a later budget period.
        # Reconstruct a missing current pause from the actual ledger, retaining
        # a valid one-use acknowledgement until a real provider dispatch.
        _check_budget_records_locked(path, existing if duplicates else existing + [record],
            budget_config=budget_config, pause_path=pause_path, target_date=datetime.now().date(), consume_resume=False)
    elif record["budget"]["state"] in {"hard_limit", "unverifiable"}:
        _write_pause_marker(pause_path, record, path)
    return record


def begin_cycle(path: Path, record: dict[str, Any]) -> None:
    """Reserve a durable identity before starting a potentially billable run."""
    with _ledger_lock(path):
        pending = path.with_name(path.name + ".pending")
        if pending.exists():
            raise UsageError("an unfinished usage cycle must be recovered first")
        temporary = pending.with_name(pending.name + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(pending)


def _recover_pending_locked(path: Path, budget_config: dict[str, Any], pause_path: Path) -> None:
    pending_path = path.with_name(path.name + ".pending")
    pending = read_pause_state(pending_path)
    if pending is None:
        return
    if pending.get("kind") != RECORD_KIND or not pending.get("cycle_id") or not pending.get("started_at"):
        raise UsageError("unfinished usage marker is invalid; repair it before starting a cycle")
    existing, errors = read_usage_records(path)
    if errors:
        raise UsageError("usage ledger contains invalid records; repair it before recovering a cycle")
    # A crash after fsync but before pending removal must not turn an already
    # completed cycle into a second interrupted record.
    if not any(record["cycle_id"] == pending["cycle_id"] for record in existing):
        try:
            interrupted = build_cycle_record(
                cycle_id=pending["cycle_id"], cycle_number=pending["cycle_number"],
                started_at=pending["started_at"], ended_at=datetime.now().astimezone().isoformat(),
                status="interrupted", exit_code=130,
                engine=pending["engine"], model=pending.get("model", "config-default"), metadata_raw="{}",
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise UsageError("unfinished usage identity is invalid") from exc
        interrupted["source"] = {"type": "cycle_recovery", "adapter": "unknown_usage"}
        for key in ("record_role", "logical_cycle_id", "attempt_id"):
            if key in pending:
                interrupted[key] = pending[key]
        _append_cycle_record_locked(path, interrupted, budget_config=budget_config, pause_path=pause_path)
    pending_path.unlink()


def recover_pending_cycle(path: Path, *, budget_config: dict[str, Any], pause_path: Path) -> None:
    with _ledger_lock(path):
        _recover_pending_locked(path, budget_config, pause_path)


def check_budget(
    path: Path, *, budget_config: dict[str, Any], pause_path: Path, target_date: str | date,
    consume_resume: bool = True,
) -> dict[str, Any]:
    """Check persisted history before spending; consume at most one resume."""
    with _ledger_lock(path):
        _recover_pending_locked(path, budget_config, pause_path)
        records, errors = read_usage_records(path)
        if errors:
            raise UsageError("usage ledger contains invalid records; repair it before starting a cycle")
        return _check_budget_records_locked(path, records, budget_config=budget_config, pause_path=pause_path,
                                           target_date=target_date, consume_resume=consume_resume)


def _check_budget_records_locked(path, records, *, budget_config, pause_path, target_date, consume_resume):
    summary = summarize_records(records, period=budget_config["period"], target_date=target_date)
    budget = evaluate_budget(summary, budget_config)
    resume_path = pause_path.with_name(pause_path.name + ".resume")
    acknowledgement = read_pause_state(resume_path)
    if acknowledgement is not None and consume_resume:
        resume_path.unlink(missing_ok=True)
    acknowledged = (
        isinstance(acknowledgement, dict)
        and acknowledgement.get("ledger_fingerprint") == _ledger_fingerprint(path)
        and isinstance(acknowledgement.get("budget"), dict)
        and acknowledgement["budget"].get("limits") == budget["limits"]
        and acknowledgement["budget"].get("period") == budget["period"]
    )
    if budget["state"] in {"hard_limit", "unverifiable"} and not acknowledged and not pause_path.exists():
        _write_pause_marker(pause_path, {
            "ended_at": datetime.now().astimezone().isoformat(),
            "cycle_id": records[-1]["cycle_id"] if records else "startup",
            "budget": budget,
        }, path)
    return budget


def read_pause_state(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {"reason": "invalid_pause_marker", "path": str(path)}
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, UnicodeError):
        return {"reason": "invalid_pause_marker", "path": str(path)}


def resume_budget(path: Path) -> bool:
    marker = read_pause_state(path)
    if marker is not None and marker.get("ledger_fingerprint"):
        resume_path = path.with_name(path.name + ".resume")
        temporary = resume_path.with_name(resume_path.name + ".tmp")
        temporary.write_text(json.dumps(marker, ensure_ascii=False), encoding="utf-8")
        temporary.replace(resume_path)
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    return True
