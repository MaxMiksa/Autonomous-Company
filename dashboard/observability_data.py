"""Bounded, read-only projections of program-recorded events and artifacts."""
from __future__ import annotations

from datetime import datetime
import hashlib
import heapq
import http.client
import json
import re
from urllib.parse import urlsplit


CYCLE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")
ARTIFACT_ID = re.compile(r"[0-9a-f]{32}\Z")
MAX_ARTIFACT_FILES = 500
MAX_ARTIFACT_ITEMS = 100


def valid_time(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (ValueError, OverflowError):
        return None
    return parsed.isoformat() if parsed.tzinfo is not None else None


def rows(raw):
    for line in raw.splitlines():
        try:
            value = json.loads(line)
        except (ValueError, RecursionError):
            continue
        if isinstance(value, dict) and value.get("version") == 1:
            yield value


def _event(item, identity):
    kind = item.get("kind")
    observed = valid_time(item.get("observedAt"))
    if (item.get("cycleId") != identity or type(item.get("sequence")) is not int
            or item["sequence"] < 1 or not observed):
        return None
    event_type = {
        "process.started": "process", "process.exited": "process",
        "turn.started": "turn", "turn.completed": "turn", "turn.failed": "turn",
        "command": "command", "files": "files", "report": "report", "error": "error",
    }.get(kind)
    if not event_type:
        return None
    result = {"cycleId": identity, "sequence": item["sequence"], "observedAt": observed,
              "kind": kind, "eventType": event_type,
              "source": "agent_report" if kind == "report" and item.get("source") == "agent_report" else "runtime_events"}
    if kind in {"command", "files", "report"}:
        if isinstance(item.get("itemId"), str):
            result["itemId"] = item["itemId"][:120]
        if item.get("phase") in {"started", "updated", "completed"}:
            result["phase"] = item["phase"]
    if kind == "command":
        command = item.get("command", "") if isinstance(item.get("command"), str) else ""
        result["command"] = command[:1000]
        result["commandTruncated"] = item.get("commandTruncated") is True or len(command) > 1000
        result["exitCode"] = item.get("exitCode") if type(item.get("exitCode")) is int else None
    elif kind == "files":
        paths = item.get("paths")
        result["paths"] = [path[:300] for path in paths[:30] if isinstance(path, str)] if isinstance(paths, list) else []
    elif kind == "report":
        result["text"] = item.get("text", "")[:3000] if isinstance(item.get("text"), str) else ""
    elif kind == "process.exited":
        result["exitCode"] = item.get("exitCode") if type(item.get("exitCode")) is int else None
        result["interrupted"] = item.get("interrupted") is True
        result["dropped"] = item.get("dropped") if type(item.get("dropped")) is int and item["dropped"] >= 0 else None
    return result


def cycle_events(source, cycle):
    identity = cycle["id"]
    path = f"logs/{identity}.events.jsonl"
    try:
        head, _ = source.read(path, 32 * 1024)
        tail, truncated = source.read(path, 128 * 1024, tail=True)
    except (OSError, ValueError):
        return {"events": [], "eventStatus": "unavailable", "observedConfig": None}
    raw_values = list(rows(head + "\n" + tail))
    values = {}
    conflicting = 0
    for item in raw_values:
        sequence = item.get("sequence")
        if item.get("cycleId") != identity or type(sequence) is not int:
            continue
        if sequence in values:
            conflicting += item != values[sequence]
            continue
        values[sequence] = item
    ordered = [values[key] for key in sorted(values)]
    config = next((item for item in ordered if item.get("kind") == "session.config"
                   and item.get("source") == "session_context"
                   and isinstance(item.get("model"), str) and isinstance(item.get("reasoning"), str)
                   and item["reasoning"] in {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"}
                   and valid_time(item.get("observedAt"))), None)
    if config:
        config = {"model": config["model"][:200], "reasoning": config["reasoning"][:40],
                  "source": "session_context", "observedAt": valid_time(config["observedAt"])}
    events = [event for event in (_event(item, identity) for item in ordered) if event is not None][-80:]
    dropped = any(type(item.get("dropped")) is int and item["dropped"] > 0 for item in ordered)
    terminal = any(item.get("kind") == "process.exited" for item in ordered)
    interrupted = cycle.get("status") == "interrupted" or any(item.get("interrupted") is True for item in ordered)
    invalid = sum(_event(item, identity) is None and item.get("kind") != "session.config" for item in ordered)
    return {"events": events,
            "eventStatus": "partial" if truncated or dropped or interrupted or invalid or conflicting or (not cycle.get("active") and not terminal) else "recorded",
            "observedConfig": config}


def preview_available(record):
    # No redirects, DNS, inherited proxies, remote hosts or arbitrary paths.
    value = record.get("url")
    token = record.get("token")
    if record.get("state") != "running" or not isinstance(value, str) or not isinstance(token, str) or not re.fullmatch(r"[0-9a-f]{32}", token):
        return False
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError:
        return False
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not port or parsed.username or parsed.password or parsed.path != "/" or parsed.query or parsed.fragment:
        return False
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=0.25)
    try:
        connection.request("GET", "/.autonomous-company-health", headers={"X-Autonomous-Company-Preview": token})
        response = connection.getresponse()
        return response.status == 204 and response.getheader("X-Autonomous-Company-Preview") == token
    except (OSError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def _counts(value):
    keys = ("tests", "failures", "errors", "skipped")
    if (not isinstance(value, dict) or any(type(value.get(key)) is not int or not 0 <= value[key] <= 1000000 for key in keys)
            or value["failures"] + value["errors"] + value["skipped"] > value["tests"]):
        return None
    return {key: value[key] for key in keys}


def _artifact_owner(source, state, record, historical_paths):
    """Resolve recorded identity from the ledger, never from file equality."""
    product_id = record.get("productId")
    row = state["cycles"].get(record.get("cycleId"))
    if product_id is not None:
        if not isinstance(product_id, str) or not ARTIFACT_ID.fullmatch(product_id):
            raise ValueError("Invalid artifact product identity")
        product = state["identities"].get(product_id)
        if not product or product["kind"] != "product":
            return None
        if row and product_id not in [row["identityId"], *row.get("createdProductIds", [])]:
            raise ValueError("Artifact identity conflicts with its cycle")
        return product_id
    if not row:
        return None
    owner = state["identities"][row["identityId"]]
    if owner["kind"] == "product" and record["project"] in {row.get("project"), owner["project"]}:
        return owner["id"]
    created = row.get("createdProductIds", [])
    if owner["kind"] == "exploration" and len(created) == 1 and owner.get("linkedProductId") == created[0]:
        # Legacy creation records predate productId. A unique creation still
        # needs positive path evidence: that cycle could inspect other products.
        if any(item["kind"] == "product" and item["id"] != created[0] and item["project"] == record["project"]
               for item in state["identities"].values()):
            return None
        current_project = state["identities"][created[0]]["project"]
        if record["project"] != current_project and record["project"] not in historical_paths.get(created[0], set()):
            # A retained marker can prove a copied source; an absent old source
            # cannot prove relocation. Missing path history stays unassociated.
            try:
                raw, truncated = source.read(record["project"] + "/.autonomous-company/identity.json", 4096)
                marker = json.loads(raw)
                if truncated or marker.get("schemaVersion") != 1 or marker.get("id") != created[0]:
                    return None
            except (OSError, ValueError, TypeError, AttributeError):
                return None
        return created[0]
    elif owner["kind"] == "product":
        matches = [identity for identity in created if state["identities"][identity]["project"] == record["project"]]
        return matches[0] if len(matches) == 1 else None
    return None


def _artifact_entry(source, selected, record, preview_probe, scope):
    kind = record.get("kind")
    identity = record.get("id")
    cycle = record.get("cycleId")
    recorded = valid_time(record.get("recordedAt"))
    if (record.get("version") != 1 or record.get("source") != "runner"
            or kind not in {"document", "check", "preview"} or not isinstance(identity, str)
            or not ARTIFACT_ID.fullmatch(identity) or not recorded
            or (cycle is not None and (not isinstance(cycle, str) or not CYCLE_ID.fullmatch(cycle)))):
        return None
    relative = record.get("path")
    recorded_project = record["project"]
    associated, product_id = scope
    entry = {"id": identity, "kind": kind, "project": selected, "cycleId": cycle,
             "associationStatus": "bound" if associated and cycle else "product" if associated and product_id else "unbound", "recordedAt": recorded,
             "source": "runner", "label": relative or kind, "available": False,
             "evidenceStatus": "unavailable", "recordedProject": recorded_project, "productId": product_id}
    if isinstance(relative, str) and relative.startswith(recorded_project + "/"):
        entry["recordedPath"] = relative
        relative = selected + relative[len(recorded_project):]
        entry["path"] = relative
    if not associated:
        entry["associationStatus"] = "unknown"
        return entry
    if kind == "preview":
        available = preview_probe and preview_available(record)
        state = record.get("state") if record.get("state") in {"running", "stopped", "interrupted", "launch_failed"} else "invalid"
        entry.update(label="preview", available=available, state=state,
                     startedAt=valid_time(record.get("startedAt")), endedAt=valid_time(record.get("endedAt")),
                     evidenceStatus="running" if available else "invalid" if state == "invalid" else "stale")
        if available:
            entry["url"] = record["url"]
        return entry
    if isinstance(relative, str) and relative.startswith(selected + "/"):
        entry.update(path=relative, fileStatus="unavailable")
        try:
            _, truncated = source.read(relative, 1024 * 1024)
            target = source.safe_path(relative)
            with target.open("rb") as data:
                payload = data.read(1024 * 1024 + 1)
            digest = hashlib.sha256(payload).hexdigest()
            valid = not truncated and len(payload) <= 1024 * 1024 and digest == record.get("sha256")
            entry.update(available=valid, fileStatus="recorded" if valid else "changed",
                         evidenceStatus="completed" if valid else "stale")
        except (OSError, ValueError):
            pass
    if kind == "document":
        entry["modifiedAt"] = valid_time(record.get("modifiedAt"))
        return entry

    state = record.get("state")
    if state is None and type(record.get("exitCode")) is int:
        state = "completed"
    if state not in {"running", "completed", "interrupted", "launch_failed"}:
        state = "invalid"
    started, ended = valid_time(record.get("startedAt")), valid_time(record.get("endedAt"))
    if started and ended and datetime.fromisoformat(ended) < datetime.fromisoformat(started):
        state = "invalid"
    raw_command = record.get("command")
    command = None
    command_truncated = False
    if isinstance(raw_command, list) and all(isinstance(arg, str) for arg in raw_command):
        command_truncated = (record.get("commandTruncated") is True or len(raw_command) > 100
                             or any(len(arg) > 2000 for arg in raw_command[:100]))
        command = [arg[:2000] for arg in raw_command[:100]]
    entry.update(state=state, startedAt=started, endedAt=ended,
                 adapter=record.get("adapter") if record.get("adapter") in {"junit", "python-unittest", "node-test", "playwright", "exit-code"} else None,
                 command=command, commandTruncated=command_truncated,
                 exitCode=record.get("exitCode") if type(record.get("exitCode")) is int else None)
    counts = _counts(record.get("tests"))
    if counts is not None and entry["available"]:
        entry["tests"] = counts
        entry["countsStatus"] = "recorded"
    elif "tests" in record:
        entry["countsStatus"] = "invalid"
    else:
        entry["countsStatus"] = "unavailable"
    report_status = record.get("reportStatus")
    if report_status not in {"pending", "fresh", "recorded", "missing_or_stale", "unsupported", "unavailable"}:
        report_status = entry.get("fileStatus", "unavailable")
    freshness = ("invalid" if entry["countsStatus"] == "invalid" else
                 "fresh" if report_status in {"fresh", "recorded"} and entry["available"] else
                 "stale" if report_status == "missing_or_stale" or entry.get("fileStatus") == "changed" else
                 "invalid" if report_status == "unsupported" or state == "invalid" else "unavailable")
    evidence = ("running" if state == "running" else "interrupted" if state == "interrupted" else
                "invalid" if state in {"invalid", "launch_failed"} or freshness == "invalid" else
                "stale" if freshness == "stale" else "completed" if state == "completed" else "unavailable")
    entry.update(reportStatus=report_status, freshness=freshness, evidenceStatus=evidence)
    return entry


def artifact_projection(source, selected=None):
    selected = (source.project()["id"] or "") if selected is None else selected
    if not re.fullmatch(r"projects/[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", selected):
        return {"items": [], "status": "unavailable", "selectedProject": None,
                "invalidRecords": 0, "truncated": False, "scannedRecords": 0, "returnedRecords": 0}
    try:
        folder = source.safe_path("logs/artifacts")
        if not folder.exists():
            files, truncated, candidate_count, scan_invalid = [], False, 0, 0
        elif not folder.is_dir():
            raise ValueError("Artifact source is not a directory")
        else:
            newest = []
            candidate_count = scan_invalid = 0
            for path in folder.iterdir():
                if not path.name.endswith(".json"):
                    continue
                candidate_count += 1
                try:
                    item = (path.lstat().st_mtime_ns, path.name, path)
                except OSError:
                    scan_invalid += 1
                    continue
                if len(newest) < MAX_ARTIFACT_FILES:
                    heapq.heappush(newest, item)
                elif item[:2] > newest[0][:2]:
                    heapq.heapreplace(newest, item)
            truncated = candidate_count > MAX_ARTIFACT_FILES
            files = [item[2] for item in sorted(newest, reverse=True)]
    except (OSError, ValueError):
        return {"items": [], "status": "unavailable", "selectedProject": selected,
                "invalidRecords": 0, "truncated": False, "scannedRecords": 0, "returnedRecords": 0}
    # One ledger snapshot for the entire collection, including cycles outside
    # the journal's display window. A missing/mismatched marker fails closed.
    from product_identity import get_identity, read_state
    try:
        identity_state = read_state(source.root)
        selected_identity = get_identity(source.root, selected, create=False)
        selected_id = selected_identity["id"] if selected_identity else None
        legacy = not identity_state["identities"]
    except (OSError, ValueError, TypeError, KeyError):
        identity_state, selected_id, legacy = None, None, False
    historical_paths = {}
    if identity_state:
        for row in identity_state["cycles"].values():
            owner = identity_state["identities"][row["identityId"]]
            if owner["kind"] == "product" and isinstance(row.get("project"), str):
                historical_paths.setdefault(owner["id"], set()).add(row["project"])
    result = []
    invalid = scan_invalid
    preview_count = 0
    for path in files:
        try:
            raw, raw_truncated = source.read(path.relative_to(source.root).as_posix(), 16 * 1024)
            if raw_truncated:
                invalid += 1
                continue
            record = json.loads(raw)
            if not isinstance(record, dict):
                invalid += 1
                continue
            record_project = record.get("project")
            if not isinstance(record_project, str) or not re.fullmatch(r"projects/[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", record_project):
                invalid += 1
                continue
            product_id = _artifact_owner(source, identity_state, record, historical_paths) if identity_state is not None else None
            if product_id and product_id != selected_id:
                continue
            if not product_id and record_project != selected:
                continue
            associated = bool(product_id and product_id == selected_id) or (legacy and record.get("productId") is None and not product_id
                                                                           and record.get("cycleId") not in identity_state["cycles"])
            if record.get("kind") == "preview":
                preview_count += 1
            entry = _artifact_entry(source, selected, record, preview_count <= 3, (associated, product_id))
            if entry is None:
                invalid += 1
                continue
            result.append(entry)
        except (OSError, ValueError, TypeError, RecursionError, OverflowError):
            invalid += 1
    # Unassociated history cannot hide a verified current resource. Within each
    # group, program timestamps (never file copy times) determine the newest.
    result.sort(key=lambda entry: (entry["associationStatus"] != "unknown",
                                   datetime.fromisoformat(entry["recordedAt"]), entry["id"]), reverse=True)
    deduped, seen = [], set()
    for entry in result:
        key = (entry["kind"], entry.get("path") if entry["kind"] == "document" else
               "project_preview" if entry["kind"] == "preview" else entry["id"])
        if key not in seen:
            seen.add(key)
            deduped.append(entry)
    result = deduped
    if len(result) > MAX_ARTIFACT_ITEMS:
        truncated = True
        result = result[:MAX_ARTIFACT_ITEMS]
    status = "partial" if invalid or truncated else "recorded" if result else "empty"
    return {"items": result, "status": status, "selectedProject": selected,
            "invalidRecords": invalid, "truncated": truncated, "scannedRecords": candidate_count,
            "returnedRecords": len(result)}


def registered_artifacts(source):
    """Compatibility list for existing document and preview consumers."""
    return artifact_projection(source)["items"]
