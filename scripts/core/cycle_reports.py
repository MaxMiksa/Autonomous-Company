"""Versioned, optional model work reports; never control the execution loop."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

LIMIT = 16 * 1024
IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")
PHASES = ("planning", "implementing", "validating", "blocked", "review")
FIELDS = {"title": 60, "summary": 500, "blocker": 300}
KEYS = {"version", "cycle_id", "project", "recorded_at", "source", "final", "phase", *FIELDS}
LEGACY_KEYS = KEYS | {"next_action", "next_action_kind"}


def validate(value, cycle):
    if not isinstance(value, dict) or set(value) != KEYS:
        raise ValueError("Unexpected work report fields")
    if type(value["version"]) is not int or value["version"] != 2:
        raise ValueError("Unsupported work report version")
    if not isinstance(cycle, str) or not IDENTITY.fullmatch(cycle) or value["cycle_id"] != cycle:
        raise ValueError("Work report cycle does not match")
    if value["source"] != "model_report" or type(value["final"]) is not bool:
        raise ValueError("Invalid report metadata")
    project = value["project"]
    if not isinstance(project, str) or (project and not re.fullmatch(r"projects/[a-z0-9][a-z0-9-]*", project)):
        raise ValueError("Invalid report project")
    for key, maximum in FIELDS.items():
        text = value[key]
        if not isinstance(text, str) or len(text) > maximum or text != text.strip():
            raise ValueError(f"Invalid {key}: maximum {maximum} characters, trimmed text required")
        if any(ord(char) < 32 for char in text):
            raise ValueError(f"Invalid control character in {key}")
    if not value["title"] or not value["summary"]:
        raise ValueError("Title and summary are required")
    if value["phase"] not in PHASES:
        raise ValueError("Invalid phase")
    if (value["phase"] == "blocked") != bool(value["blocker"]):
        raise ValueError("Only blocked work requires a blocker")
    if not isinstance(value["recorded_at"], str):
        raise ValueError("Invalid report timestamp")
    parsed = datetime.fromisoformat(value["recorded_at"])
    if parsed.tzinfo is None:
        raise ValueError("Work report timestamp requires a timezone")
    return value


def decode(raw, cycle):
    if len(raw.encode("utf-8")) > LIMIT:
        raise ValueError("Work report is too large")
    value = json.loads(raw)
    # Project historical records into the current contract without rewriting them.
    if isinstance(value, dict) and type(value.get("version")) is int and value["version"] == 1:
        if set(value) != LEGACY_KEYS:
            raise ValueError("Unexpected legacy work report fields")
        value = {key: value[key] for key in KEYS}
        value["version"] = 2
    return validate(value, cycle)


def read_report(source, cycle):
    """Use the journal's existing bounded, link-safe file reader."""
    try:
        raw, truncated = source.read(f"logs/{cycle['id']}.work.json", LIMIT)
        if truncated:
            raise ValueError("Work report is too large")
        report = decode(raw, cycle["id"])
    except FileNotFoundError:
        return {"workReport": None, "workReportStatus": "missing"}
    except (OSError, ValueError, TypeError, RecursionError, OverflowError):
        return {"workReport": None, "workReportStatus": "invalid"}
    return {"workReport": report, "workReportStatus": "valid"}


def linked(path):
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def write_report(root, cycle, fields, project=""):
    if not isinstance(cycle, str) or not IDENTITY.fullmatch(cycle):
        raise ValueError("A valid AUTONOMOUS_COMPANY_CYCLE_ID is required")
    root = Path(root).resolve(strict=True)
    value = {"version": 2, "cycle_id": cycle, "project": project,
             "recorded_at": datetime.now(timezone.utc).isoformat(), "source": "model_report", **fields}
    validate(value, cycle)
    folder = root / "logs"
    if linked(folder):
        raise ValueError("Linked log directory is not allowed")
    folder.mkdir(exist_ok=True)
    target = folder / f"{cycle}.work.json"
    if linked(target) or (target.exists() and not stat.S_ISREG(target.stat().st_mode)):
        raise ValueError("Work report target must be a regular file")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{cycle}.work-", dir=folder)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
            json.dump(value, output, ensure_ascii=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return value


PROMPT = """## Dashboard work report (version 2; coordinator only)
In addition to the existing consensus and normal final answer, publish a concise work report early in this cycle, after meaningful progress/blockers, and once before finishing with --final. Do not ask subagents to write it. Use the current product language for the field values. Do not change product work, consensus headings, Human Overrides, selection, stopping, or permissions to satisfy this reporting requirement.
Run this tool from the framework directory (use its absolute path if working in a product):
python3 scripts/core/cycle_reports.py write --title 'Short concrete business task' --summary 'What has actually been done so far' --phase implementing
Required fields: --title (1-60 characters, a task rather than a success claim); --summary (1-500 characters, one paragraph); --phase (planning|implementing|validating|blocked|review).
Use --blocker 'Specific missing input or obstacle' (1-300 characters) only with phase blocked. Phase review means ready for human review, never independent acceptance. Add --final only to your last report; it means this cycle's report is final, not that the whole product is complete. All text fields must be single-line, plain text. Prefer at most 4 meaningful reports per cycle.
The tool supplies cycle identity, project and timestamp from runtime context. Never invent test results, execution state, percentages or timing in its place. Tests and artifacts retain their existing program-owned records. If reporting fails, fix field/quoting errors at most once; continue the original task and required consensus work. Never retry the model or fail/stop the cycle just because the report is unavailable.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prompt")
    writer = commands.add_parser("write")
    for name in ("title", "summary", "phase"):
        writer.add_argument("--" + name, required=True)
    writer.add_argument("--blocker", default="")
    writer.add_argument("--final", action="store_true")
    args = parser.parse_args()
    if args.command == "prompt":
        print(PROMPT)
        return 0
    try:
        root = os.environ.get("AUTONOMOUS_COMPANY_ROOT") or str(Path(__file__).resolve().parents[2])
        value = write_report(root, os.environ.get("AUTONOMOUS_COMPANY_CYCLE_ID", ""),
            {"title": args.title, "summary": args.summary, "phase": args.phase,
             "blocker": args.blocker, "final": args.final}, os.environ.get("ACTIVE_PROJECT", ""))
        print(json.dumps({"ok": True, "cycle_id": value["cycle_id"], "recorded_at": value["recorded_at"]}))
        return 0
    except (OSError, ValueError, TypeError, RecursionError, OverflowError) as error:
        print(f"Work report unavailable: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
