"""Host-only Harness control steps used inside the existing loop/supervisor.

No provider is launched here. Dispatch, stops, governance and OS supervision
remain owned by auto-loop. Durable usage intents replay accounting, never work.
"""
import argparse
from contextlib import contextmanager
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
from cycle_reports import PHASES
from product_identity import atomic_write, cycle_projection, read_state, safe_path, update_cycle
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
    for name, default in (("CORRECTIONS", 2), ("RECOVERY_ATTEMPTS", 2), ("RECOVERY_SECONDS", 300), ("CLOSE_SECONDS", 60), ("MAX_SAME_ERROR", 2)):
        raw = os.environ.get("COMPANY_HARNESS_" + name, str(default))
        if not raw.isdecimal() or int(raw) < (0 if name in {"CORRECTIONS", "RECOVERY_ATTEMPTS"} else 1):
            raise HarnessError("INVALID_CONFIG", "COMPANY_HARNESS_" + name)
        result[name] = int(raw)
    return result


_EMPTY_OVERRIDE_TOKENS = {"", "(none)", "- (none)", "none", "- none", "无", "- 无", "-（无）", "（无）", "n/a", "- n/a", "-"}


def _has_explicit_human_override(root):
    if root is None:
        return False
    consensus_path = safe_path(root, "memories/consensus.md")
    if not consensus_path.is_file():
        return False
    lines = consensus_path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_section = False
    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            if stripped == "## Human Overrides":
                in_section = True
            continue
        if in_section and stripped.lower() not in _EMPTY_OVERRIDE_TOKENS:
            return True
    return False


def _initial_proposal(root=None, project=""):
    override = os.environ.get("COMPANY_HARNESS_INITIAL_WORK_KIND", "").strip()
    if override:
        if override not in {"objective_selection", "research", "direction"}:
            raise HarnessError("INVALID_CONFIG", "COMPANY_HARNESS_INITIAL_WORK_KIND")
        kind = override
    elif root is not None and _has_explicit_human_override(root):
        kind = "direction"
    elif root is not None and project:
        kind = "research"
    else:
        kind = "objective_selection"
    if kind == "direction":
        return {
            "objective": "Establish the authorized product direction and bounded MVP scope from Human Overrides, then propose its independent review.",
            "workKind": "direction", "timeClass": "regular",
            "scope": ["commit concrete product direction and bounded scope from Human Overrides"],
            "inputRefs": [], "completionOrHandoff": "Versioned direction document ready for independent review",
            "prerequisiteRefs": [], "reviewRequirement": None,
        }
    if kind == "research":
        return {
            "objective": "Assess current state of the active project and identify the highest-value next deliverable, then propose its concrete nextContract.",
            "workKind": "research", "timeClass": "regular",
            "scope": ["assess active project state and select concrete next deliverable"],
            "inputRefs": [], "completionOrHandoff": "Concise research note with nextContract for the next milestone",
            "prerequisiteRefs": [], "reviewRequirement": None,
        }
    return {
        "objective": "Select one authorized primary deliverable (for blank exploration, propose one bounded 2-3 candidate research comparison to commit a winner) and submit its nextContract; do not implement it in this cycle.",
        "workKind": "objective_selection", "timeClass": "regular",
        "scope": ["select the next primary outcome only"],
        "inputRefs": [], "completionOrHandoff": "Readable proposal for one next primary deliverable",
        "prerequisiteRefs": [], "reviewRequirement": None,
    }


def next_contract(store, identity, *, root=None, project=""):
    from company_harness_quality import prepare_contract, _belongs
    snapshot = store.snapshot()
    applicable = [c for c in snapshot["cycles"] if _belongs(c, identity)]
    if not applicable:
        proposal = _initial_proposal(root=root, project=project)
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
    proposal = next_contract(store, scope, root=root, project=identity.get("project") or "")
    proposal.update(targetRangeSeconds=[180, 300] if proposal["timeClass"] == "regular" else None,
                    targetSeconds=300 if proposal["timeClass"] == "regular" else 600,
                    capabilities={"adapter": "codex", "liveTimeReminder": False, "receiptTimeReminder": True,
                                  "submitFeedback": True, "recoveryBusinessReadonly": True,
                                  "recoveryInnerMode": "inherited",
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
        if normal_count >= 1 + limits["CORRECTIONS"] or reliable != "reliable" or math.floor(cycle["budgetTimer"]["limitSeconds"] - remaining) < 1:
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
    write_fact(host_path(root, attempt_id + '.launch.json'), {'context': attempt['context'], 'phase': 'prepared'})
    record = build_cycle_record(cycle_id=attempt_id, cycle_number=cycle["contract"]["runCycleNumber"],
        started_at=attempt["startedAt"], ended_at=attempt["startedAt"], status="interrupted", exit_code=130,
        engine="codex", model=os.environ.get("MODEL_LABEL", os.environ.get("MODEL", "config-default")), metadata_raw="{}")
    record.update(record_role="harness_attempt", logical_cycle_id=cycle_id, attempt_id=attempt_id)
    begin_cycle(ledger, record)
    prompt = "\n\n## Company Harness active contract\n" + json.dumps(cycle["contract"], ensure_ascii=False)
    prompt += "\nThis contract is one primary deliverable. Stay inside its scope. Use python3 /workspace/scripts/core/company_harness_client.py. "
    prompt += "For every action, --payload is a PATH to a UTF-8 JSON FILE, never an inline JSON string. "
    prompt += "Publish progress with --id and --payload FILE (reportRevision,title,summary,reportedPhase,blocker). "
    prompt += "reportedPhase must be one of " + ", ".join(PHASES) + "; it is distinct from workKind. "
    prompt += 'Progress blocker is a string: use "" unless reportedPhase is blocked. '
    prompt += "Before exit, submit --id STABLE_ID --result completed|partial|blocked|failed --evidence RELATIVE_PATH (repeatable). "
    prompt += "Use --handoff RELATIVE_JSON_PATH for a file containing {nextContract:{objective,workKind,timeClass,scope,inputRefs,completionOrHandoff,prerequisiteRefs,reviewRequirement}}. "
    prompt += "Evidence is versioned by actual SHA256 bytes. Read receipts; fix rejected requests within the same deadline. "
    prompt += "Choose a single primary result using --primary PATH_OR_EVIDENCE_ID when providing multiple non-handoff materials; the client selects a unique non-handoff result automatically. "
    prompt += "For a review cycle, --payload JSON must include review:{targetRefs:EXACT_REVIEW_TARGET_REFS,verdict:passed|changes_required|unverifiable,issues:[],qualityApplicability:[WORK_KINDS]}; use status.cycle.contract.reviewRequirement.targetRefs (or status.cycle.contract.inputRefs if unset) and the host binds actual independent reviewer identity. "
    prompt += "qualityApplicability names the DOWNSTREAM workKinds this reviewed version is sufficient to enter, not the reviewed artifact kind. For example, a passed direction review enabling definition uses [\"definition\"], not [\"direction\"]. Name only the downstream scopes actually assessed; this does not approve their future outputs or waive other prerequisites. "
    prompt += "After accepted submit, stop ALL business writes and exit immediately; do not wait for closed. Lost ACK: reuse the same submission ID/content or query status. "
    prompt += "Do not invoke cycle_reports.py or create another deliverable/cycle. All teammate/tool work shares this deadline."
    prompt += "\nRegular work targets 3–5 minutes (180–300 seconds); development uses an engineering target of 600 seconds. "
    prompt += "Finish earlier when ready. If unfinished at the target, request_extension with reason and remainingSeconds; the fixed 480/720-second hard deadline never resets. "
    prompt += "Every company_harness_client.py receipt reports remainingSeconds and timePhase (plus a stderr warning at <=120s); query status when unsure and stop feature work immediately at <=120s to generate handoff and submit."
    prompt += "\nUse the READ-ONLY immutable input versions listed in /run/autonomous-company/harness-inputs/index.json. "
    prompt += "Each entry maps evidenceId/SHA256/mediaType/sourceOutcome/isCompletedHead to a readable file in that directory (including binary screenshots). Do not review a different mutable docs version."
    handoff_path = protocol_handoff_path(attempt_id) if recovery else "docs/harness/" + attempt_id + "-handoff.json"
    prompt += "\nCLI Quick Reference (do not inspect company_harness_client.py source or run --help; use these exact commands):"
    prompt += "\n- Status: python3 /workspace/scripts/core/company_harness_client.py status"
    prompt += "\n- Progress: python3 /workspace/scripts/core/company_harness_client.py publish_progress --id prog-1 --payload logs/prog.json"
    prompt += "\n- Compile handoff: python3 /workspace/scripts/core/company_harness_handoff.py --plan logs/next-plan.json --primary docs/result.md"
    prompt += "\n- Submit: python3 /workspace/scripts/core/company_harness_client.py submit --id sub-1 --result completed --primary docs/result.md --evidence docs/result.md --handoff " + handoff_path + " --payload logs/submit.json"
    prompt += "\nPrefer the deterministic handoff helper instead of hand-copying hashes. Write logs/next-plan.json with "
    prompt += '{"contract":{"objective":"YOUR NEXT OUTCOME","workKind":"research","timeClass":"regular","scope":["AUTHORIZED SCOPE"],"completionOrHandoff":"USABLE RESULT","reviewRequirement":null},"inputs":[],"prerequisites":[]}. '
    prompt += 'Choose the actual workKind/scope (for review with read-only background inputs, optionally list only reviewed items in "reviewTargets":[...]). Select historical refs as {"input":"EXACT file FROM index.json"}, listed local attachments as {"evidence":"docs/result-data.json"}, or the current primary as {"primary":true}. '
    prompt += "The primary is automatically the first input. For a current independent review needed by the next stage, explicitly put {\"primary\":true} in prerequisites; host closure still decides applicability. "
    prompt += "Run: python3 /workspace/scripts/core/company_harness_handoff.py --plan logs/next-plan.json --primary docs/result.md (add --evidence PATH for attachments). "
    prompt += "Use your actual primary path. The helper returns handoffPath=" + handoff_path + "; submit separately with --primary docs/result.md --evidence docs/result.md --handoff " + handoff_path + ". "
    prompt += "Also submit listed attachments. No document needs its own hash. For review payload targetRefs, use status.cycle.contract.reviewRequirement.targetRefs (or status.cycle.contract.inputRefs) exactly; verdict/issues/applicability require actual independent assessment. "
    prompt += "Serialize generation and submission. After accepted, never rerun the helper; query status or replay the original submit ID/content. The original handwritten handoff remains supported."
    from company_harness_quality import ARTIFACTS, REQUIRED, artifact_state, progression_state
    prompt += "\nAllowed workKind values: " + ", ".join([*ARTIFACTS, "revision"]) + ". revision also requires revisesKind naming its artifact kind. "
    prompt += "Typed prerequisites (each requires current version inputRefs plus independent-review prerequisiteRefs): " + json.dumps(REQUIRED) + ". "
    prompt += "Review/research/revision can recur; these are admission conditions, not a fixed cycle sequence."
    scope = {"productId": cycle.get("productId"), "explorationId": cycle.get("explorationId")}
    heads_summary = artifact_state(store, scope)
    prog_summary = progression_state(store, scope)
    prompt += "\nCurrent artifact head status (partial cycles NEVER create a completed head; if a required artifactKind has no completed head, propose its original production workKind to finish the gap and submit completed—never propose review or revision): " + json.dumps(heads_summary, ensure_ascii=False)
    prompt += "\nCurrent progression & anti-spin state: " + json.dumps(prog_summary, ensure_ascii=False)
    if prog_summary.get("advisory"):
        prompt += "\nANTI-SPIN ADVISORY: " + prog_summary["advisory"]
    previous_result = host_path(root, cycle_id + ".result.json")
    if previous_result.exists():
        prompt += "\nPrior attempt's deterministic feedback (correct within this SAME deliverable): " + json.dumps(read_fact(previous_result), ensure_ascii=False)
    if recovery:
        prompt += "\nRECOVERY ONLY: products/docs/memories are kernel-mounted READ-ONLY. Inner mode is inherited, not automatically changed. "
        prompt += "Reconcile existing work; never continue product development. Submit partial/blocked/failed, never completed. "
        prompt += "For partial, cite an existing business artifact as primary and write ONLY the nextContract envelope to /workspace/" + protocol_handoff_path(attempt_id)
        prompt += ". This attempt-only handoff.json is limited to 16 KiB and cannot be primary business evidence. Use --handoff for it; put transient client --payload JSON in logs if needed."
    else:
        prompt += "\nNORMAL EXECUTION: put transient --payload JSON in logs/ and the --handoff nextContract JSON in docs/ (for example docs/harness/next-contract.json). "
        prompt += "Do not use .company-harness-protocol/ during normal execution; that collection route is reserved for recovery."
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
    raise HarnessError("EVIDENCE_SCOPE", "path", relative)


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
    if (record.get('source') or {}).get('type') == 'host_pre_dispatch_cancel':
        launch = read_fact(host_path(root, record['attempt_id'] + '.launch.json'))
        if launch.get('phase') != 'cancelled' or launch['fact']['record'] != record:
            raise HarnessError('ID_CONFLICT', 'unstartedUsage')
        fact = launch['fact']
        store.finish_attempt(launch['context'], fact['actualResult'], writers_stopped=True, observation=fact['proof'])
        store.confirm_usage(record['logical_cycle_id'], record['attempt_id'], [], source='host_pre_dispatch_cancel', observation=fact['proof'])
        append_cycle_record(root / 'logs/usage.jsonl', record, budget_config=load_budget_config(os.environ),
                            pause_path=root / '.auto-loop-budget-paused', reconcile_budget=True)
        return
    append_cycle_record(root / "logs/usage.jsonl", record, budget_config=load_budget_config(os.environ),
                        pause_path=root / ".auto-loop-budget-paused", reconcile_budget=True)
    usage = record.get("usage") or {}
    in_tok, out_tok = usage.get("input_tokens"), usage.get("output_tokens")
    has_tokens = (
        isinstance(in_tok, (int, float)) and not isinstance(in_tok, bool) and math.isfinite(in_tok)
        and isinstance(out_tok, (int, float)) and not isinstance(out_tok, bool) and math.isfinite(out_tok)
    )
    store.record_usage(record["logical_cycle_id"], record["attempt_id"], {
        "callId": record["attempt_id"] + "-provider", "coverage": "self" if has_tokens else "unknown",
        "cost": record["cost_usd"], "inputTokens": in_tok, "outputTokens": out_tok,
        "source": {"type": "usage_ledger_mirror", "ledgerId": record["attempt_id"],
                   "providerCoverage": "root_cli_self" if has_tokens else "unknown"}})


def process_start(pid):
    try:
        fields = Path('/proc/' + str(pid) + '/stat').read_text().rsplit(')', 1)[1].split()
        return fields[19] if fields[0] != 'Z' else None
    except FileNotFoundError:
        return None


def live_launch_owner(manifest):
    owner = manifest['context']['ownership']
    pid = owner.get('loopPid')
    if (pid != os.getppid() or str(pid) != os.environ.get('AUTONOMOUS_COMPANY_LOCK_PID', str(os.getppid())) or
            process_start(pid) != owner.get('loopProcessStart')):
        raise HarnessError('OWNER_MISMATCH', 'livePreDispatch')


@contextmanager
def launch_lock(root, attempt_id):
    import fcntl
    with host_path(root, attempt_id + '.launch.lock').open('a+b') as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        yield


def mark_dispatch(store, root, attempt_id):
    with launch_lock(root, attempt_id):
        return mark_live_dispatch(store, root, attempt_id)


def mark_live_dispatch(store, root, attempt_id):
    host_admission(root, starting=True)
    manifest = read_fact(host_path(root, attempt_id + '.json'))
    live_launch_owner(manifest)
    with store._transaction() as tx:
        cycle, attempt = store._context(tx, manifest['context'])
    launch_path = host_path(root, attempt_id + '.launch.json')
    launch = read_fact(launch_path)
    if launch.get('context') != manifest['context'] or launch.get('phase') != 'prepared':
        raise HarnessError('DISPATCH_UNCONFIRMED')
    timer = next(r['timer'] for r in cycle['recoveries'] if r['recoveryId'] == attempt['recoveryId']) if attempt['recoveryId'] else cycle['budgetTimer']
    consumed, reliable = store._elapsed(timer)
    if reliable != 'reliable':
        raise HarnessError('TIME_UNCONFIRMED', 'bootId')
    seconds = math.floor(timer['limitSeconds'] - consumed)
    if seconds < 1:
        raise HarnessError('BUDGET_EXHAUSTED', 'time')
    write_fact(launch_path, {**launch, 'phase': 'provider_dispatch_intent', 'recordedAt': now(), 'timeoutSeconds': seconds})
    return seconds


def complete_unstarted(store, root, launch):
    fact, context = launch['fact'], launch['context']
    attempt_id = context['attemptId']
    log = safe_path(root, 'logs/' + attempt_id + '.log')
    diagnostic = 'Host: providerInvoked=false; dispatch was not attempted because its pre-dispatch deadline expired.\n'
    if log.exists() and log.read_text() != diagnostic:
        raise HarnessError('ID_CONFLICT', 'unstartedLog')
    log.write_text(diagnostic)
    write_fact(safe_path(root, 'logs/' + attempt_id + '.json'), fact['metadata'])
    intent = host_path(root, attempt_id + '.usage.json')
    if intent.exists() and read_fact(intent) != fact['record']:
        raise HarnessError('ID_CONFLICT', 'unstartedUsage')
    write_fact(intent, fact['record'])
    settle_usage_intent(store, root, fact['record'])
    write_fact(host_path(root, attempt_id + '.finish.json'), fact['result'])
    publish_cycle_result(store, root, fact['result'])
    directory = Path(read_fact(host_path(root, attempt_id + '.json'))['temporary'])
    if directory.resolve().parent == Path(tempfile.gettempdir()).resolve() and directory.name.startswith('ac-harness-'):
        shutil.rmtree(directory, ignore_errors=True)
    return fact['result']


def settle_unstarted(store, root, attempt_id, bridge_pid):
    """Only the same live controller may prove it never attempted dispatch."""
    with launch_lock(root, attempt_id):
        return settle_live_unstarted(store, root, attempt_id, bridge_pid)


def settle_live_unstarted(store, root, attempt_id, bridge_pid):
    host_admission(root)
    manifest = read_fact(host_path(root, attempt_id + '.json'))
    live_launch_owner(manifest)
    launch_path = host_path(root, attempt_id + '.launch.json')
    launch = read_fact(launch_path)
    if launch.get('context') != manifest['context']:
        raise HarnessError('OWNER_MISMATCH', 'launch')
    if launch.get('phase') == 'cancelled':
        if launch['fact']['proof']['bridgePid'] != bridge_pid:
            raise HarnessError('OWNER_MISMATCH', 'bridge')
        return complete_unstarted(store, root, launch)
    if launch.get('phase') != 'prepared':
        raise HarnessError('DISPATCH_UNCONFIRMED')
    with store._transaction() as tx:
        cycle, attempt = store._context(tx, manifest['context'], business=False)
    timer = next(r['timer'] for r in cycle['recoveries'] if r['recoveryId'] == attempt['recoveryId']) if attempt['recoveryId'] else cycle['budgetTimer']
    consumed, reliable = store._elapsed(timer)
    if reliable != 'reliable' or math.floor(timer['limitSeconds'] - consumed) >= 1 or attempt['calls'] or attempt['acceptedSubmissionId']:
        raise HarnessError('UNSTARTED_UNCONFIRMED')
    ready = read_fact(Path(manifest['ready']))
    if (ready.get('pid') != bridge_pid or ready.get('attemptId') != attempt_id or
            ready.get('loopPid') != manifest['context']['ownership']['loopPid'] or not ready.get('processStart') or process_start(bridge_pid)):
        raise HarnessError('WRITERS_UNCONFIRMED', 'bridge')
    identity = read_state(root)['cycles'][cycle['cycleId']]['identityId']
    active = safe_path(root, '.autonomous-company/isolation/' + identity + '/active-run.json')
    if active.exists():
        worker = read_fact(active)
        if (type(worker.get('pid')) is not int or not worker.get('processStart') or not worker.get('attemptId') or
                worker.get('attemptId') == attempt_id or process_start(worker['pid'])):
            raise HarnessError('WRITERS_UNCONFIRMED', 'worker')
    checked = now()
    proof = {'type': 'live_pre_dispatch_cancel', 'loopPid': os.getppid(), 'loopProcessStart': process_start(os.getppid()),
             'bridgePid': bridge_pid, 'bridgeProcessStart': ready['processStart'], 'providerDispatchAttempted': False, 'observedAt': checked}
    metadata = {'status': 'not_started', 'exit_code': None, 'providerInvoked': False,
                'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0, 'cost_usd': 0, 'source': 'host_pre_dispatch_cancel'}
    record = build_cycle_record(cycle_id=attempt_id, cycle_number=cycle['contract']['runCycleNumber'],
        started_at=attempt['startedAt'], ended_at=checked, status='not_started', exit_code=None,
        engine='codex', model=os.environ.get('MODEL_LABEL', os.environ.get('MODEL', 'config-default')), metadata_raw=json.dumps(metadata))
    record.update(record_role='harness_attempt', logical_cycle_id=cycle['cycleId'], attempt_id=attempt_id,
                  provider_invoked=False, source={'type': 'host_pre_dispatch_cancel'})
    result = {'cycleId': cycle['cycleId'], 'attemptId': attempt_id, 'submissionId': None, 'validSubmission': False,
              'actualSuccess': False, 'providerInvoked': False, 'collected': False, 'collectionStatus': 'not_applicable',
              'evidenceRefs': [], 'error': 'PREDISPATCH_BUDGET_EXHAUSTED', 'outcome': 'not_started', 'action': 'retry'}
    launch.update(phase='cancelled', fact={'proof': proof, 'actualResult': {'outcome': 'not_started', 'providerInvoked': False},
        'metadata': metadata, 'record': record, 'result': result})
    write_fact(launch_path, launch)
    return complete_unstarted(store, root, launch)


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
    if collected and not submission:
        error = "SUBMISSION_MISSING"
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
    if not success:
        error = 'EXECUTION_FAILED' + (': ' + error if error else '')
    result = {"cycleId": cycle["cycleId"], "attemptId": attempt_id, "collected": bool(collected),
        "submissionId": submission["submissionId"] if submission else None, "validSubmission": valid,
        "evidenceRefs": refs, "error": error, "actualSuccess": success, "eventsHealth": events_health,
        "outcome": submission["payload"]["result"] if valid and success else "failed",
        "action": "close" if valid and success else "retry"}
    if not collected:
        result.update(action="human", error="COLLECTION_UNCONFIRMED")
    if result["action"] == "retry" and error:
        def _sig(text):
            parts = str(text or "").split(": ", 2)
            return ": ".join(parts[:2]) if len(parts) >= 2 else parts[0]
        cur_sig = _sig(error)
        repeat_count = 1
        prior_attempts = [a for a in cycle["attempts"] if a["attemptId"] != attempt_id]
        for prior in reversed(prior_attempts):
            pf = host_path(root, prior["attemptId"] + ".finish.json")
            if not pf.exists():
                break
            prev_err = read_fact(pf).get("error") or ""
            if _sig(prev_err) == cur_sig:
                repeat_count += 1
            else:
                break
        max_same = policy()["MAX_SAME_ERROR"]
        if repeat_count >= max_same:
            result["repeatedErrorCount"] = repeat_count
            result["guidance"] = "Repeated identical rejection; change strategy/workKind instead of repeating the same rejected contract"
            normal_count = sum(a["recoveryId"] is None for a in cycle["attempts"])
            if attempt.get("recoveryId") or normal_count >= 1 + policy()["CORRECTIONS"]:
                result["action"] = "human"
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
        launch_path = host_path(root, attempt_id + '.launch.json')
        if launch_path.exists() and read_fact(launch_path).get('phase') == 'cancelled':
            complete_unstarted(store, root, read_fact(launch_path))
            raise HarnessError('UNFINISHED_HARNESS', detail='Known unstarted settlement replayed; restart never infers permission to dispatch')
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


def reconcile_crash(store, root, reason="operator_crash_reconcile"):
    """Close proven-stopped orphaned Harness cycles after an unclean host crash."""
    host_admission(root)
    reconciled = []
    for cycle in store.snapshot()["cycles"]:
        if cycle["protocolState"] == "closed":
            continue
        identity_id = (read_state(root).get("cycles") or {}).get(cycle["cycleId"], {}).get("identityId")
        if identity_id:
            active = safe_path(root, ".autonomous-company/isolation/" + identity_id + "/active-run.json")
            if active.exists():
                worker = read_fact(active)
                wpid = worker.get("pid")
                if isinstance(wpid, int) and process_start(wpid) == worker.get("processStart") and process_start(wpid) is not None:
                    raise HarnessError("WRITERS_UNCONFIRMED", "worker")
        for attempt in cycle["attempts"]:
            aid = attempt["attemptId"]
            mpath = host_path(root, aid + ".json")
            if mpath.exists():
                manifest = read_fact(mpath)
                rpath = Path(manifest["ready"])
                if rpath.exists():
                    ready = read_fact(rpath)
                    bpid = ready.get("pid")
                    if isinstance(bpid, int) and process_start(bpid) == ready.get("processStart") and process_start(bpid) is not None:
                        raise HarnessError("WRITERS_UNCONFIRMED", "bridge")
                tmp_dir = Path(manifest["temporary"])
                if tmp_dir.resolve().parent == Path(tempfile.gettempdir()).resolve() and tmp_dir.name.startswith("ac-harness-"):
                    shutil.rmtree(tmp_dir, ignore_errors=True)
            if attempt["status"] != "finished" or not attempt["writersStopped"]:
                store.finish_attempt(
                    attempt["context"],
                    {"outcome": "interrupted", "exitCode": None, "crashReconciled": True},
                    writers_stopped=True,
                    observation={"type": "operator_crash_reconcile", "reason": reason, "checkedAt": now()},
                )
        pending_file = safe_path(root, "memories/.consensus-cycle-pending")
        if pending_file.exists() or pending_file.is_symlink():
            guard = Path(__file__).with_name("consensus-guard.sh")
            res = subprocess.run(["bash", str(guard), "recover"], env={**os.environ, "AUTONOMOUS_COMPANY_ROOT": str(root)},
                                 capture_output=True, text=True, timeout=policy()["CLOSE_SECONDS"])
            if res.returncode not in (0, 42):
                raise HarnessError("GOVERNANCE_RECOVERY_REQUIRED", "recover")
        refreshed = row(store, cycle["cycleId"])
        store.close_cycle(
            cycle["cycleId"],
            "reconcile-" + cycle["cycleId"],
            outcome="interrupted",
            verification={"writersStopped": True, "crashReconciled": True,
                          "attemptResults": [a["attemptId"] for a in refreshed["attempts"]],
                          "evidenceRefs": [], "reason": reason, "checkedAt": now()},
            continuation_decision={"allowed": False, "reason": "crash_reconciled_human_review", "checkedAt": now()},
        )
        sync_identity(root, row(store, cycle["cycleId"]))
        reconciled.append(cycle["cycleId"])
    return {"reconciledCycles": reconciled, "reason": reason}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("action", choices=("startup", "recover-usage", "reconcile-crash", "next", "prepare", "attempt", "remaining", "prompt", "finish", "close", "dispatch", "unstarted"))
    parser.add_argument("--cycle")
    parser.add_argument("--attempt")
    parser.add_argument('--bridge-pid', type=int)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--supervisor-owner")
    parser.add_argument("--cleanup-failed", type=int, default=1)
    parser.add_argument("--governance-ok", type=int, default=0)
    parser.add_argument("--product", default="")
    parser.add_argument("--reason", default="operator_crash_reconcile")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.action in {"startup", "next", "prepare", "attempt"} and os.environ.get("CODEX_SANDBOX_MODE", "danger-full-access") != "danger-full-access":
        raise HarnessError("UNSUPPORTED_INNER_SANDBOX", "CODEX_SANDBOX_MODE")
    store = HarnessStore(root, create=True)
    if args.action == "reconcile-crash":
        for path in sorted(host_path(root, "").glob("*.usage.json")):
            settle_usage_intent(store, root, read_fact(path))
        print(json.dumps(reconcile_crash(store, root, args.reason), ensure_ascii=False))
        return 0
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
            print(json.dumps({"initial": _initial_proposal(root=root, project=args.product)["workKind"]}))
            return 0
        scope = {"productId": identity["id"] if identity and identity["kind"] == "product" else None,
            "explorationId": (identity["id"] if identity["kind"] == "exploration" else identity.get("explorationId")) if identity else None}
        reassess_continuation(store, root, scope)
        print(json.dumps(next_contract(store, scope, root=root, project=identity.get("project") if identity else args.product)))
    elif args.action == "prepare":
        print(json.dumps(prepare(store, root, args.cycle)))
    elif args.action == "attempt":
        manifest = begin_attempt(store, root, args.cycle)
        print(manifest["context"]["attemptId"], manifest["timeoutSeconds"], int(manifest["recovery"]))
    elif args.action == 'dispatch':
        print(mark_dispatch(store, root, args.attempt))
    elif args.action == 'unstarted':
        print(settle_unstarted(store, root, args.attempt, args.bridge_pid)['action'])
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
