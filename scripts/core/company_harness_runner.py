"""Host-only Harness control steps used inside the existing loop/supervisor.

No provider is launched here. Dispatch, stops, governance and OS supervision
remain owned by auto-loop. Durable usage intents replay accounting, never work.
"""
import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import math
import mimetypes
import os
from pathlib import Path
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time

from company_harness import HarnessError, HarnessStore
from company_harness_inputs import load_inputs, write_inputs
from company_harness_client import PROTOCOL_LIMIT, PROTOCOL_ROOT, protocol_handoff_path, validate_protocol_handoff
from product_identity import atomic_write, cycle_projection, safe_path, update_cycle
from usage_lib import append_cycle_record, begin_cycle, build_cycle_record, check_budget, load_budget_config


def now():
    return datetime.now().astimezone().isoformat()


def row(store, cycle_id):
    return next(c for c in store.snapshot()["cycles"] if c["cycleId"] == cycle_id)


def host_path(root, name):
    return safe_path(root, ".autonomous-company/harness/" + name)


def write_fact(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(path, value)


def read_fact(path):
    return json.loads(path.read_text())


def host_admission(root, starting=False):
    from center_runner import admission
    admission(root)
    if starting and any((root / name).exists() for name in (".auto-loop-stop", ".auto-loop-paused", ".auto-loop-budget-paused")):
        raise HarnessError("HOST_PAUSED")


def policy():
    result = {}
    for name, default in (("CORRECTIONS", 2), ("RECOVERY_ATTEMPTS", 2), ("RECOVERY_SECONDS", 300), ("CLOSE_SECONDS", 60)):
        raw = os.environ.get("COMPANY_HARNESS_" + name, str(default))
        if not raw.isdecimal() or int(raw) < (0 if name in {"CORRECTIONS", "RECOVERY_ATTEMPTS"} else 1):
            raise HarnessError("INVALID_CONFIG", "COMPANY_HARNESS_" + name)
        result[name] = int(raw)
    return result


def next_contract(store, identity):
    from company_harness_quality import prepare_contract, _belongs
    snapshot = store.snapshot()
    applicable = [c for c in snapshot["cycles"] if _belongs(c, identity)]
    if not applicable:
        proposal = {"objective": "Select one authorized primary deliverable and submit its nextContract; do not implement it in this cycle.",
            "workKind": "objective_selection", "timeClass": "regular", "scope": ["select the next primary outcome only"], "inputRefs": [],
            "completionOrHandoff": "Readable proposal for one next primary deliverable", "prerequisiteRefs": [], "reviewRequirement": None}
    else:
        previous = applicable[-1]
        if previous["protocolState"] != "closed" or not previous["continuationDecision"].get("allowed"):
            raise HarnessError("CONTINUATION_BLOCKED")
        submission = next((s for s in previous["submissions"] if s["submissionId"] == previous["closeReceipt"]["input"]["submissionId"]), None)
        ref = submission["payload"].get("handoffRef") if submission else None
        evidence = store.read_evidence(ref["evidenceId"]) if ref else None
        if not evidence or evidence["sha256"] != ref.get("sha256"):
            raise HarnessError("HANDOFF_MISSING")
        proposal = json.loads(evidence["content"]).get("nextContract")
    return prepare_contract(store, proposal, identity)


def prepare(store, root, cycle_id):
    if any(c["cycleId"] == cycle_id for c in store.snapshot()["cycles"]):
        return row(store, cycle_id)
    identity = cycle_projection(root, cycle_id)
    if not identity or identity["state"] not in {"reserved", "dispatching"}:
        raise HarnessError("IDENTITY_UNCONFIRMED")
    scope = {"productId": identity.get("productId"), "explorationId": identity.get("explorationId")}
    reassess_continuation(store, root, scope)
    proposal = next_contract(store, scope)
    proposal.update(targetRangeSeconds=[180, 300] if proposal["timeClass"] == "regular" else None,
                    targetSeconds=300 if proposal["timeClass"] == "regular" else 600,
                    capabilities={"adapter": "codex", "liveTimeReminder": False, "submitFeedback": True,
                                  "recoveryBusinessReadonly": True, "recoveryInnerMode": "inherited",
                                  "supportedInnerModes": ["danger-full-access"], "protocolScratch": True})
    return store.create_cycle({**proposal, "cycleId": cycle_id, "productId": identity.get("productId"),
        "explorationId": identity.get("explorationId"), "sequenceNumber": identity["sequenceNumber"] or identity["productCycleNumber"],
        "project": identity["project"], "runCycleNumber": identity["runCycleNumber"]})


def ownership(root):
    manifest = os.environ.get("AUTONOMOUS_COMPANY_CENTER_MANIFEST")
    context = read_fact(Path(manifest)) if manifest else {}
    pid = int(os.environ.get("AUTONOMOUS_COMPANY_LOCK_PID", os.getppid()))
    start = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    return {**{key: context.get(key) for key in ("centerId", "runtimeId", "requestId", "dispatchId", "nonce")},
            "loopPid": pid, "loopProcessStart": start}


def begin_attempt(store, root, cycle_id):
    host_admission(root, starting=True)
    if os.environ.get("CODEX_SANDBOX_MODE", "danger-full-access") != "danger-full-access":
        raise HarnessError("UNSUPPORTED_INNER_SANDBOX", "CODEX_SANDBOX_MODE", "Harness v1 preserves explicit stricter modes and refuses unsupported nested sandbox execution")
    limits, cycle = policy(), row(store, cycle_id)
    materials = load_inputs(store, cycle['contract'])
    directory = Path(tempfile.mkdtemp(prefix='ac-harness-'))
    try:
        write_inputs(materials, directory / 'inputs')
        return begin_prepared_attempt(store, root, cycle_id, cycle, limits, directory)
    except BaseException:
        shutil.rmtree(directory)
        raise


def begin_prepared_attempt(store, root, cycle_id, cycle, limits, directory):
    config = load_budget_config(os.environ)
    ledger, pause = root / "logs/usage.jsonl", root / ".auto-loop-budget-paused"
    check_budget(ledger, budget_config=config, pause_path=pause, target_date=datetime.now().date(), consume_resume=False)
    if pause.exists():
        raise HarnessError("BUDGET_PAUSED")
    recovery = cycle["recoveries"][0] if cycle["recoveries"] else None
    normal_count = sum(a["recoveryId"] is None for a in cycle["attempts"])
    if not recovery:
        remaining, reliable = store._elapsed(cycle["budgetTimer"])
        if normal_count >= 1 + limits["CORRECTIONS"] or reliable != "reliable" or remaining >= cycle["budgetTimer"]["limitSeconds"]:
            if limits["RECOVERY_ATTEMPTS"] == 0:
                raise HarnessError("RECOVERY_EXHAUSTED")
            recovery = store.begin_recovery(cycle_id, "recovery-" + cycle_id, budget_seconds=limits["RECOVERY_SECONDS"], reason="Protocol correction budget exhausted")
    if recovery and sum(a["recoveryId"] is not None for a in cycle["attempts"]) >= limits["RECOVERY_ATTEMPTS"]:
        raise HarnessError("RECOVERY_EXHAUSTED")
    timer = recovery['timer'] if recovery else cycle['budgetTimer']
    consumed, reliable = store._elapsed(timer)
    seconds = math.floor(timer['limitSeconds'] - consumed)
    if reliable != 'reliable' or seconds < 1:
        raise HarnessError('BUDGET_EXHAUSTED')
    owner = ownership(root)
    attempt_id = "attempt-" + secrets.token_hex(16)
    check_budget(ledger, budget_config=config, pause_path=pause, target_date=datetime.now().date())
    if pause.exists():
        raise HarnessError('BUDGET_PAUSED')
    attempt = store.begin_attempt(cycle_id, attempt_id, owner, recovery_id=recovery["recoveryId"] if recovery else None,
        log_refs=[{"log": f"logs/{attempt_id}.log", "events": f"logs/{attempt_id}.events.jsonl", "metadata": f"logs/{attempt_id}.json"}])
    cycle = row(store, cycle_id)
    inputs = directory / "inputs"
    manifest = {"root": str(root), "context": attempt["context"], "token": secrets.token_hex(32),
        "socket": str(directory / "h.sock"), "ready": str(directory / "ready"), "temporary": str(directory),
        "collectRelative": ".autonomous-company/harness/" + attempt_id + ".collect.json",
        "timeoutSeconds": seconds, "recovery": bool(recovery), "inputsDirectory": str(inputs)}
    write_fact(host_path(root, attempt_id + ".json"), manifest)
    record = build_cycle_record(cycle_id=attempt_id, cycle_number=cycle["contract"]["runCycleNumber"],
        started_at=attempt["startedAt"], ended_at=attempt["startedAt"], status="interrupted", exit_code=130,
        engine="codex", model=os.environ.get("MODEL_LABEL", os.environ.get("MODEL", "config-default")), metadata_raw="{}")
    record.update(record_role="harness_attempt", logical_cycle_id=cycle_id, attempt_id=attempt_id)
    begin_cycle(ledger, record)
    prompt = "\n\n## Company Harness active contract\n" + json.dumps(cycle["contract"], ensure_ascii=False)
    prompt += "\nThis contract is one primary deliverable. Stay inside its scope. Use python3 /workspace/scripts/core/company_harness_client.py. "
    prompt += "Publish progress with --id and --payload JSON (reportRevision,title,summary,reportedPhase,blocker). "
    prompt += "Before exit, submit --id STABLE_ID --result completed|partial|blocked|failed --evidence RELATIVE_PATH (repeatable). "
    prompt += "Use --handoff RELATIVE_JSON_PATH for a file containing {nextContract:{objective,workKind,timeClass,scope,inputRefs,completionOrHandoff,prerequisiteRefs,reviewRequirement}}. "
    prompt += "Evidence is versioned by actual SHA256 bytes. Read receipts; fix rejected requests within the same deadline. "
    prompt += "Choose a single primary result using --primary PATH_OR_EVIDENCE_ID when providing multiple non-handoff materials; the client selects a unique non-handoff result automatically. "
    prompt += "For a review cycle, --payload JSON must include review:{targetRefs:EXACT_CONTRACT_INPUT_REFS,verdict:passed|changes_required|unverifiable,issues:[],qualityApplicability:[WORK_KINDS]}; the host binds actual independent reviewer identity. "
    prompt += "After accepted submit, stop ALL business writes and exit immediately; do not wait for closed. Lost ACK: reuse the same submission ID/content or query status. "
    prompt += "Do not invoke cycle_reports.py or create another deliverable/cycle. All teammate/tool work shares this deadline."
    prompt += "\nRegular work targets 3–5 minutes (180–300 seconds); development uses an engineering target of 600 seconds. "
    prompt += "Finish earlier when ready. If unfinished at the target, request_extension with reason and remainingSeconds; the fixed 480/720-second hard deadline never resets. "
    prompt += "This Codex adapter has no reliable live time reminder (liveTimeReminder=false); query status for remaining time and plan your own submission margin."
    prompt += "\nUse the READ-ONLY immutable input versions listed in /run/autonomous-company/harness-inputs/index.json. "
    prompt += "Each entry maps evidenceId/SHA256/mediaType to a readable file in that directory (including binary screenshots). Do not review a different mutable docs version."
    from company_harness_quality import ARTIFACTS, REQUIRED
    prompt += "\nAllowed workKind values: " + ", ".join([*ARTIFACTS, "revision"]) + ". revision also requires revisesKind naming its artifact kind. "
    prompt += "Typed prerequisites (each requires current version inputRefs plus independent-review prerequisiteRefs): " + json.dumps(REQUIRED) + ". "
    prompt += "Review/research/revision can recur; these are admission conditions, not a fixed cycle sequence."
    previous_result = host_path(root, cycle_id + ".result.json")
    if previous_result.exists():
        prompt += "\nPrior attempt's deterministic feedback (correct within this SAME deliverable): " + json.dumps(read_fact(previous_result), ensure_ascii=False)
    if recovery:
        prompt += "\nRECOVERY ONLY: products/docs/memories are kernel-mounted READ-ONLY. Inner mode is inherited, not automatically changed. "
        prompt += "Reconcile existing work; never continue product development. Submit partial/blocked/failed, never completed. "
        prompt += "For partial, cite an existing business artifact as primary and write ONLY the nextContract envelope to /workspace/" + protocol_handoff_path(attempt_id)
        prompt += ". This attempt-only handoff.json is limited to 16 KiB and cannot be primary business evidence. Use --handoff for it; put transient client --payload JSON in logs if needed."
    write_fact(host_path(root, attempt_id + ".prompt.json"), {"prompt": prompt})
    return manifest


def evidence_path(root, cycle, receipt, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise HarnessError("EVIDENCE_SCOPE", "path")
    project = cycle["contract"].get("project")
    if relative.startswith(PROTOCOL_ROOT + "/"):
        if relative != protocol_handoff_path(receipt.get("attemptId")) or not receipt.get("protocolRoot"):
            raise HarnessError("PROTOCOL_SCOPE", "path")
        return safe_path(Path(receipt["protocolRoot"]), "handoff.json")
    if relative.startswith("docs/"):
        return safe_path(Path(receipt["docsRoot"]), relative[5:])
    if relative == "memories/consensus.md" or (project and relative.startswith(project + "/")):
        return safe_path(root, relative)
    raise HarnessError("EVIDENCE_SCOPE", "path")


def validate_recovery_submission(attempt, payload, read_protocol):
    refs = payload.get("evidenceRefs", [])
    protocol = [ref for ref in refs if isinstance(ref, dict) and str(ref.get("path", "")).startswith(PROTOCOL_ROOT + "/")]
    if not attempt["recoveryId"]:
        if protocol:
            raise HarnessError("PROTOCOL_SCOPE", "evidenceRefs")
        return
    if payload.get("result") == "completed":
        raise HarnessError("RECOVERY_SCOPE", "result")
    business = [ref for ref in refs if ref not in protocol]
    if payload.get("result") == "partial" and not business:
        raise HarnessError("RECOVERY_PRIMARY_REQUIRED", "evidenceRefs")
    for ref in protocol:
        if ref.get("path") != protocol_handoff_path(attempt["attemptId"]):
            raise HarnessError("PROTOCOL_SCOPE", "path")
        if ref != payload.get("handoffRef") or ref.get("evidenceId") == payload.get("primaryEvidenceId"):
            raise HarnessError("PROTOCOL_PURPOSE", "evidenceRefs")
        try:
            validate_protocol_handoff(read_protocol(ref))
        except HarnessError:
            raise
        except ValueError as error:
            raise HarnessError(str(error), "handoffRef")


def capture_evidence(store, root, cycle, attempt, receipt, submission):
    from isolation_workspace import regular_bytes
    refs = submission["payload"].get("evidenceRefs", [])
    for ref in refs:
        path = evidence_path(root, cycle, receipt, ref.get("path"))
        protocol = ref.get("path", "").startswith(PROTOCOL_ROOT + "/")
        data = regular_bytes(path, PROTOCOL_LIMIT if protocol else 1024 * 1024)
        if hashlib.sha256(data).hexdigest() != ref["sha256"]:
            raise HarnessError("EVIDENCE_VERSION_MISMATCH", ref["evidenceId"])
        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError:
            content = data
        store.bind_evidence(cycle["cycleId"], ref["evidenceId"], content,
            media_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            source={"type": "isolated_collect", "attemptId": attempt["attemptId"], "workKind": cycle["workKind"],
                    "project": cycle["contract"].get("project"), "path": ref["path"]})
    return refs


def settle_usage_intent(store, root, record):
    append_cycle_record(root / "logs/usage.jsonl", record, budget_config=load_budget_config(os.environ),
                        pause_path=root / ".auto-loop-budget-paused", reconcile_budget=True)
    store.record_usage(record["logical_cycle_id"], record["attempt_id"], {
        "callId": record["attempt_id"] + "-provider", "coverage": "unknown",
        "cost": record["cost_usd"], "inputTokens": record["usage"]["input_tokens"], "outputTokens": record["usage"]["output_tokens"],
        "source": {"type": "usage_ledger_mirror", "ledgerId": record["attempt_id"], "providerCoverage": "unknown"}})


def sync_identity(root, cycle):
    identity = cycle_projection(root, cycle["cycleId"])
    if not identity:
        raise HarnessError("IDENTITY_UNCONFIRMED")
    status = "completed" if cycle["outcome"] == "completed" else "interrupted" if cycle["outcome"] in {"partial", "interrupted"} else "failed"
    if identity["state"] not in {"reserved", "dispatching", status}:
        raise HarnessError("IDENTITY_RESULT_MISMATCH")
    update_cycle(root, cycle["cycleId"], status, "Company Harness " + cycle["outcome"])


def publish_cycle_result(store, root, result):
    """Repair the latest attempt's derived result; old receipts stay historical."""
    cycle = row(store, result["cycleId"])
    if not cycle["attempts"] or cycle["attempts"][-1]["attemptId"] != result["attemptId"]:
        return False
    target = host_path(root, cycle["cycleId"] + ".result.json")
    if target.exists():
        existing = read_fact(target)
        if existing == result:
            return True
        if existing.get("attemptId") == result["attemptId"]:
            raise HarnessError("ID_CONFLICT", "cycleResult")
    write_fact(target, result)
    return True


def collect_events(store, root, context):
    """Bound optional stream reads; identity/conflicting IDs remain hard errors."""
    limit = 2 * 1024 * 1024
    path = safe_path(root, "logs/" + context["attemptId"] + ".events.jsonl")
    health = {"status": "missing", "truncated": False, "gaps": [], "bytesRead": 0,
              "recordsRead": 0, "asOf": now(), "errorCode": None}
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise HarnessError("EVENT_RESOURCE_UNSAFE")
            with os.fdopen(descriptor, "rb", closefd=False) as source:
                raw = source.read(limit + 1)
        finally:
            os.close(descriptor)
    except FileNotFoundError:
        return health
    except OSError:
        health.update(status="unavailable", errorCode="EVENT_READ_FAILED", gaps=[{"reason": "read_failed"}])
        return health
    health.update(status="available", bytesRead=min(len(raw), limit), truncated=len(raw) > limit)
    raw = raw[:limit]
    if raw and not raw.endswith(b"\n"):
        raw = raw.rsplit(b"\n", 1)[0] if b"\n" in raw else b""
        health["gaps"].append({"reason": "incomplete_record"})
    rows = raw.splitlines()
    if len(rows) > 2000:
        health["truncated"] = True
    if health["truncated"]:
        health["gaps"].append({"reason": "bounded_prefix"})
    expected = 1
    for raw in rows[:2000]:
        try:
            event = json.loads(raw)
            if not isinstance(event, dict) or type(event.get("sequence")) is not int or event["sequence"] < 1:
                raise ValueError("Invalid event sequence")
        except (ValueError, TypeError, RecursionError):
            health["gaps"].append({"reason": "invalid_record"})
            continue
        if event.get("cycleId") != context["attemptId"]:
            raise HarnessError("OWNER_MISMATCH", "event.cycleId")
        if event["sequence"] > expected:
            health["gaps"].append({"reason": "sequence_gap", "from": expected, "to": event["sequence"] - 1})
        expected = max(expected, event["sequence"] + 1)
        # Do not catch HarnessError (a ValueError subclass): duplicate sequence
        # with different content and stale ownership are not optional parse loss.
        store.record_event(context, event["sequence"], event)
        health["recordsRead"] += 1
    if health["gaps"]:
        health["status"] = "partial"
    return health


def finish_attempt(store, root, attempt_id, metadata, proof):
    manifest = read_fact(host_path(root, attempt_id + ".json"))
    cycle = row(store, manifest["context"]["cycleId"])
    attempt = next(a for a in cycle["attempts"] if a["attemptId"] == attempt_id)
    previous_finish = host_path(root, attempt_id + ".finish.json")
    if previous_finish.exists():
        result = read_fact(previous_finish)
        if result.get("cycleId") != cycle["cycleId"] or result.get("attemptId") != attempt_id:
            raise HarnessError("OWNER_MISMATCH", "finishReceipt")
        publish_cycle_result(store, root, result)
        return result
    if proof.get("cleanupFailed") is not False or not proof.get("supervisorOwner"):
        raise HarnessError("WRITERS_UNCONFIRMED")
    host_admission(root)
    proof_path = host_path(root, attempt_id + ".proof.json")
    proof_digest = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    if proof_path.exists():
        previous_proof = read_fact(proof_path)
        if previous_proof["metadataHash"] != proof_digest:
            raise HarnessError("ID_CONFLICT", "metadata")
        proof = previous_proof["proof"]
    else:
        write_fact(proof_path, {"proof": proof, "metadataHash": proof_digest})
    finished = now()
    success = metadata.get("exit_code") == 0 and metadata.get("status") == "success" and not metadata.get("timed_out")
    record = build_cycle_record(cycle_id=attempt_id, cycle_number=cycle["contract"]["runCycleNumber"],
        started_at=attempt["startedAt"], ended_at=finished, status="completed" if success else "failed",
        exit_code=metadata["exit_code"], engine="codex", model=os.environ.get("MODEL_LABEL", os.environ.get("MODEL", "config-default")), metadata_raw=json.dumps(metadata))
    record.update(record_role="harness_attempt", logical_cycle_id=cycle["cycleId"], attempt_id=attempt_id)
    # Intent precedes ledger fsync; startup replays only this immutable accounting
    # record. The logical cycle is never appended again as a second charge.
    intent = host_path(root, attempt_id + ".usage.json")
    if intent.exists():
        record = read_fact(intent)
    else:
        write_fact(intent, record)
    settle_usage_intent(store, root, record)
    submission = next((s for s in reversed(cycle["submissions"]) if s["attemptId"] == attempt_id), None)
    valid, refs, error = False, [], None
    receipt_path = safe_path(root, manifest["collectRelative"])
    collected = read_fact(receipt_path) if receipt_path.exists() else None
    if collected and any(collected.get(key) != manifest["context"].get(key) for key in ("cycleId", "attemptId", "generation")):
        raise HarnessError("COLLECTION_OWNER_MISMATCH")
    if collected and submission:
        try:
            from isolation_workspace import regular_bytes
            validate_recovery_submission(attempt, submission["payload"], lambda ref:
                regular_bytes(evidence_path(root, cycle, collected, ref.get("path")), PROTOCOL_LIMIT + 1))
            acceptance = submission.get("acceptanceVersions")
            if not acceptance or acceptance != collected.get("versions"):
                raise HarnessError("POST_SUBMISSION_CHANGE", "versions")
            refs = capture_evidence(store, root, cycle, attempt, collected, submission)
            valid = True
        except (HarnessError, OSError, ValueError) as caught:
            error = str(caught)
    events_health = collect_events(store, root, manifest["context"]) if attempt["status"] == "running" else attempt["actualResult"].get("eventsHealth")
    store.finish_attempt(manifest["context"], {"outcome": "completed" if success else "failed", "exitCode": metadata["exit_code"], "eventsHealth": events_health},
                         writers_stopped=True, observation=proof)
    if valid and success:
        from company_harness_quality import close_review, prepare_contract
        stopped_cycle = row(store, cycle["cycleId"])
        stopped_cycle["outcome"] = submission["payload"]["result"]
        try:
            quality = close_review(store, stopped_cycle, submission)
            handoff = submission["payload"].get("handoffRef")
            if handoff:
                if handoff not in refs:
                    raise HarnessError("HANDOFF_UNBOUND", "handoffRef")
                try:
                    proposal = json.loads(store.read_evidence(handoff["evidenceId"])["content"])["nextContract"]
                except (ValueError, KeyError, TypeError):
                    raise HarnessError("HANDOFF_INVALID", "nextContract")
                prepare_contract(store, proposal, {"productId": cycle["productId"], "explorationId": cycle["explorationId"]},
                    pending_cycle=stopped_cycle, pending_quality=quality)
        except HarnessError as caught:
            valid, error = False, str(caught)
    result = {"cycleId": cycle["cycleId"], "attemptId": attempt_id, "collected": bool(collected),
        "submissionId": submission["submissionId"] if submission else None, "validSubmission": valid,
        "evidenceRefs": refs, "error": error, "actualSuccess": success, "eventsHealth": events_health,
        "outcome": submission["payload"]["result"] if valid and success else "failed",
        "action": "close" if valid or not collected else "retry"}
    if not collected:
        result.update(action="human", error="COLLECTION_UNCONFIRMED")
    write_fact(previous_finish, result)
    publish_cycle_result(store, root, result)
    # Only remove our short-lived socket directory, never retained worker views.
    directory = Path(manifest["temporary"])
    if directory.resolve().parent == Path(tempfile.gettempdir()).resolve() and directory.name.startswith("ac-harness-"):
        shutil.rmtree(directory)
    return result


def close_cycle(store, root, cycle_id, governance_ok):
    from company_harness_quality import close_review, prepare_contract
    began, cycle = time.monotonic(), row(store, cycle_id)
    if cycle["protocolState"] == "closed":
        sync_identity(root, cycle)
        return {"receipt": cycle["closeReceipt"], "continuationAllowed": cycle["continuationDecision"]["allowed"],
                "continuationReason": cycle["continuationDecision"]["reason"], "outcome": cycle["outcome"]}
    result = read_fact(host_path(root, cycle_id + ".result.json"))
    if cycle["activeAttemptId"]:
        raise HarnessError("WRITERS_UNCONFIRMED")
    submission = next((s for s in cycle["submissions"] if s["submissionId"] == result["submissionId"]), None)
    outcome = result["outcome"] if governance_ok and result["validSubmission"] else "failed"
    quality = close_review(store, cycle, submission) if governance_ok and submission and result["validSubmission"] else []
    cycle["outcome"] = outcome
    continuation = evaluate_continuation(store, root, cycle, submission, pending_quality=quality)
    host_admission(root)
    if time.monotonic() - began >= policy()["CLOSE_SECONDS"]:
        raise HarnessError("CLOSE_BUDGET_EXHAUSTED")
    closed = store.close_cycle(cycle_id, "close-" + cycle_id, outcome=outcome,
        verification={"writersStopped": True, "attemptResults": [a["attemptId"] for a in cycle["attempts"]],
            "evidenceRefs": result["evidenceRefs"], "submittedVersionUnchanged": result["validSubmission"],
            "checkedAt": now(), "governanceVerified": governance_ok},
        continuation_decision=continuation, quality_applicability=quality, submission_id=result["submissionId"] if result["validSubmission"] else None)
    sync_identity(root, row(store, cycle_id))
    return {"receipt": closed, "continuationAllowed": continuation["allowed"], "continuationReason": continuation["reason"], "outcome": outcome}


def evaluate_continuation(store, root, cycle, submission, pending_quality=None):
    from company_harness_quality import prepare_contract
    continuation = {"allowed": False, "reason": "human_required", "checkedAt": now()}
    if cycle["outcome"] in {"completed", "partial"} and submission:
        ref = submission["payload"].get("handoffRef")
        if ref and ref in submission["payload"].get("evidenceRefs", []):
            evidence = store.read_evidence(ref["evidenceId"])
            try:
                if not evidence or evidence["sha256"] != ref.get("sha256") or evidence["cycleId"] != cycle["cycleId"]:
                    raise HarnessError("HANDOFF_UNBOUND")
                proposal = json.loads(evidence["content"]).get("nextContract")
                pending = cycle if cycle["protocolState"] != "closed" else None
                prepare_contract(store, proposal, {"productId": cycle["productId"], "explorationId": cycle["explorationId"]},
                                 pending_cycle=pending, pending_quality=pending_quality)
                continuation.update(allowed=True, reason="handoff_validated", basis={"handoffRef": ref, "governance": "verified"})
            except HarnessError as error:
                continuation["reason"] = error.code
    # Reuse the exact original P1 parser; verify permits newly discovered P1,
    # while current continuation must already reflect the resulting blocker.
    spec = importlib.util.spec_from_file_location("harness_consensus_rules", Path(__file__).with_name("consensus-format.py"))
    rules = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rules)
    try:
        p1_present = rules.unresolved_p1(rules.sections(safe_path(root, "memories/consensus.md"))[rules.HEADINGS[1]])
    except (OSError, ValueError):
        p1_present = None
    if p1_present is not False:
        reason = "unresolved_p1" if p1_present else "governance_unconfirmed"
        continuation.update(allowed=False, reason=reason)
        continuation.setdefault("basis", {})["governance"] = reason
    pause = safe_path(root, ".auto-loop-paused")
    if pause.exists():
        reason = next((line.partition("=")[2] for line in pause.read_text().splitlines()
                       if line.startswith("PAUSE_REASON=")), "host_paused") or "host_paused"
        continuation["allowed"] = False
        continuation.setdefault("basis", {})["hostPauseReason"] = reason
        if p1_present is False:
            continuation["reason"] = reason
    if (root / ".auto-loop-stop").exists() or (root / ".auto-loop-budget-paused").exists():
        otherwise_allowed = continuation["allowed"]
        continuation["allowed"] = False
        if p1_present is False and not pause.exists() and otherwise_allowed:
            continuation["reason"] = "stop_requested" if (root / ".auto-loop-stop").exists() else "budget_paused"
    return continuation


def reassess_continuation(store, root, identity):
    """Only next/prepare host control paths call this; snapshot/status never do."""
    from company_harness_quality import _belongs
    cycles = [cycle for cycle in store.snapshot()["cycles"] if _belongs(cycle, identity)]
    if not cycles:
        return
    cycle = cycles[-1]
    if (cycle["protocolState"] != "closed" or cycle["outcome"] not in {"completed", "partial"}
            or not cycle["closeReceipt"] or cycle["closeReceipt"]["source"] != "runtime"
            or cycle["activeAttemptId"] or any(not attempt["writersStopped"] for attempt in cycle["attempts"])):
        raise HarnessError("CONTINUATION_BLOCKED")
    host_admission(root, starting=True)
    guard = Path(__file__).with_name("consensus-guard.sh")
    checked = subprocess.run(["bash", str(guard), "check-admission", str(cycle["contract"]["runCycleNumber"])],
        env={**os.environ, "AUTONOMOUS_COMPANY_ROOT": str(root)}, capture_output=True, text=True, timeout=policy()["CLOSE_SECONDS"])
    if checked.returncode:
        raise HarnessError("GOVERNANCE_BLOCKED")
    check_budget(root / "logs/usage.jsonl", budget_config=load_budget_config(os.environ),
                 pause_path=root / ".auto-loop-budget-paused", target_date=datetime.now().date(), consume_resume=False)
    host_admission(root, starting=True)
    submission_id = cycle["closeReceipt"]["input"]["submissionId"]
    submission = next((value for value in cycle["submissions"] if value["submissionId"] == submission_id), None)
    decision = evaluate_continuation(store, root, cycle, submission)
    store.set_continuation_decision(cycle["cycleId"], decision)
    if not decision["allowed"]:
        raise HarnessError("CONTINUATION_BLOCKED", detail=decision["reason"])


def recover_stopped_cycles(store, root):
    """Complete only proven stopped bookkeeping; never relaunch unknown work."""
    for cycle in store.snapshot()["cycles"]:
        if cycle["protocolState"] == "closed":
            continue
        if not cycle["attempts"]:
            raise HarnessError("UNFINISHED_HARNESS", detail="Unconfirmed dispatch intent requires ownership reconciliation")
        close_deadline = time.monotonic() + policy()["CLOSE_SECONDS"]
        last = cycle["attempts"][-1]
        attempt_id = last["attemptId"]
        required = {suffix: host_path(root, attempt_id + suffix) for suffix in (".json", ".proof.json", ".usage.json", ".collect.json")}
        metadata_path = safe_path(root, "logs/" + attempt_id + ".json")
        if not metadata_path.exists() or any(not path.exists() for path in required.values()):
            raise HarnessError("UNFINISHED_HARNESS", detail="Writer/collection proof is missing; no automatic replay")
        proof = read_fact(required[".proof.json"])
        finish_attempt(store, root, attempt_id, read_fact(metadata_path), proof["proof"])
        refreshed = row(store, cycle["cycleId"])
        if refreshed["activeAttemptId"] or any(not a["writersStopped"] for a in refreshed["attempts"]):
            raise HarnessError("WRITERS_UNCONFIRMED")
        guard = root / "scripts/core/consensus-guard.sh"
        number = str(cycle["contract"]["runCycleNumber"])
        for action in ("verify", "snapshot", "close"):
            remaining = close_deadline - time.monotonic()
            if remaining <= 0:
                raise HarnessError("CLOSE_BUDGET_EXHAUSTED")
            result = subprocess.run(["bash", str(guard), action, number], cwd=root, capture_output=True,
                                    text=True, timeout=remaining)
            if result.returncode:
                raise HarnessError("GOVERNANCE_RECOVERY_REQUIRED", action)
        close_cycle(store, root, cycle["cycleId"], True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("action", choices=("startup", "recover-usage", "next", "prepare", "attempt", "remaining", "prompt", "finish", "close"))
    parser.add_argument("--cycle")
    parser.add_argument("--attempt")
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--supervisor-owner")
    parser.add_argument("--cleanup-failed", type=int, default=1)
    parser.add_argument("--governance-ok", type=int, default=0)
    parser.add_argument("--product", default="")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action in {"startup", "next", "prepare", "attempt"} and os.environ.get("CODEX_SANDBOX_MODE", "danger-full-access") != "danger-full-access":
        raise HarnessError("UNSUPPORTED_INNER_SANDBOX", "CODEX_SANDBOX_MODE")
    store = HarnessStore(root, create=True)
    if args.action in {"startup", "recover-usage"}:
        for path in sorted(host_path(root, "").glob("*.usage.json")):
            settle_usage_intent(store, root, read_fact(path))
        if args.action == "recover-usage":
            return 0
        recover_stopped_cycles(store, root)
        for cycle in store.snapshot()["cycles"]:
            if cycle["protocolState"] == "closed":
                sync_identity(root, cycle)
        if any(c["protocolState"] != "closed" for c in store.snapshot()["cycles"]):
            raise HarnessError("UNFINISHED_HARNESS", detail="Reconcile existing writer/collection/usage and governance before any new dispatch")
        store.claim_controller(secrets.token_hex(16))
    elif args.action == "next":
        from product_identity import get_identity
        identity = get_identity(root, args.product)
        if identity is None and not store.snapshot()["cycles"]:
            print(json.dumps({"initial": "objective_selection"}))
            return 0
        scope = {"productId": identity["id"] if identity and identity["kind"] == "product" else None,
            "explorationId": (identity["id"] if identity["kind"] == "exploration" else identity.get("explorationId")) if identity else None}
        reassess_continuation(store, root, scope)
        print(json.dumps(next_contract(store, scope)))
    elif args.action == "prepare":
        print(json.dumps(prepare(store, root, args.cycle)))
    elif args.action == "attempt":
        manifest = begin_attempt(store, root, args.cycle)
        print(manifest["context"]["attemptId"], manifest["timeoutSeconds"], int(manifest["recovery"]))
    elif args.action == "prompt":
        print(read_fact(host_path(root, args.attempt + ".prompt.json"))["prompt"])
    elif args.action == "remaining":
        manifest = read_fact(host_path(root, args.attempt + ".json"))
        cycle = row(store, manifest["context"]["cycleId"])
        recovery = cycle["recoveries"][0] if manifest["recovery"] else None
        store._budget(cycle, recovery)
        timer = recovery["timer"] if recovery else cycle["budgetTimer"]
        consumed, _ = store._elapsed(timer)
        remaining = math.floor(timer["limitSeconds"] - consumed)
        if remaining < 1:
            raise HarnessError("BUDGET_EXHAUSTED")
        print(remaining)
    elif args.action == "finish":
        result = finish_attempt(store, root, args.attempt, read_fact(args.metadata),
            {"cleanupFailed": bool(args.cleanup_failed), "supervisorOwner": args.supervisor_owner, "observedAt": now()})
        print(result["action"])
    elif args.action == "close":
        result = close_cycle(store, root, args.cycle, bool(args.governance_ok))
        print(result["outcome"], int(result["continuationAllowed"]), result["continuationReason"])
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.TimeoutExpired:
        print("Company Harness: CLOSE_BUDGET_EXHAUSTED", file=sys.stderr)
        sys.exit(78)
    except (HarnessError, OSError, ValueError, KeyError, StopIteration) as error:
        print("Company Harness: " + str(error), file=sys.stderr)
        sys.exit(78)
