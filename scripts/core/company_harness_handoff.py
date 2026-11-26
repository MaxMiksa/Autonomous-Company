"""Compile explicit outcome selectors into the existing nextContract envelope.

Generation does not submit or grant quality approval. Use the original client
afterwards, and never regenerate after an accepted submission.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys

from company_harness_client import material, request, protocol_handoff_path, validate_protocol_handoff
from company_harness_contract import MAX_INPUTS, MAX_BYTES, MATERIAL_LIMIT, ARTIFACTS
from isolation_workspace import regular_bytes
from product_identity import atomic_write, safe_path
from project_isolation import IsolationError

INPUT_DIRECTORY = Path('/run/autonomous-company/harness-inputs')
FIELDS = {'objective', 'workKind', 'timeClass', 'scope', 'completionOrHandoff',
          'reviewRequirement', 'revisesKind'}


def reference(value):
    return {key: value[key] for key in ('evidenceId', 'sha256')}


def unique(refs):
    by_id = {}
    for ref in refs:
        previous = by_id.get(ref['evidenceId'])
        if previous is not None and previous != ref:
            raise ValueError('CONFLICTING_REFERENCE')
        by_id[ref['evidenceId']] = ref
    return list(by_id.values())


def compile_plan(plan, primary, inputs, local):
    if (not isinstance(plan, dict) or set(plan) != {'contract', 'inputs', 'prerequisites'}
            or not isinstance(plan['contract'], dict) or set(plan['contract']) - FIELDS
            or not isinstance(plan['inputs'], list) or not isinstance(plan['prerequisites'], list)):
        raise ValueError('PLAN_FIELDS')
    contract = deepcopy(plan['contract'])
    for field in ('objective', 'completionOrHandoff'):
        if not isinstance(contract.get(field), str) or not contract[field].strip():
            raise ValueError('PLAN_FIELD: ' + field)
    kind = contract.get('workKind')
    if (not isinstance(kind, str) or kind not in {*ARTIFACTS, 'revision'}
            or len(contract['objective']) > 256 or not contract.get('scope')):
        raise ValueError('PLAN_FIELD: workKind/objective/scope')
    artifact = contract.get('revisesKind') if kind == 'revision' else ARTIFACTS[kind]
    if kind == 'revision' and (not isinstance(artifact, str) or artifact not in set(ARTIFACTS.values()) - {'objective', 'review', 'delivery'}):
        raise ValueError('PLAN_FIELD: revisesKind')
    time_class = contract.get('timeClass', 'regular')
    if time_class not in ('regular', 'development') or time_class == 'development' and artifact != 'implementation':
        raise ValueError('PLAN_FIELD: timeClass')

    def resolve(selector):
        if selector == {'primary': True} and type(selector['primary']) is bool:
            return reference(primary)
        if not isinstance(selector, dict) or len(selector) != 1:
            raise ValueError('SELECTOR')
        key, value = next(iter(selector.items()))
        table = inputs if key == 'input' else local if key == 'evidence' else {}
        if not isinstance(value, str) or value not in table:
            raise ValueError('SELECTOR: ' + str(selector))
        return reference(table[value])

    contract['inputRefs'] = unique([reference(primary)] + [resolve(x) for x in plan['inputs']])
    contract['prerequisiteRefs'] = unique([resolve(x) for x in plan['prerequisites']])
    refs = unique(contract['inputRefs'] + contract['prerequisiteRefs'])
    if len(refs) > MAX_INPUTS:
        raise ValueError('INPUT_PACKAGE_LIMIT: count')
    return {'nextContract': contract}


def active_status(attempt_id):
    status = request('status')
    cycle, attempt = status.get('cycle') or {}, status.get('attempt') or {}
    if attempt.get('acceptedSubmissionId') or cycle.get('protocolState') == 'submitted':
        raise ValueError('SUBMISSION_ALREADY_ACCEPTED: query status or replay the original submit ID/content; no writes')
    if (status.get('writeAllowed') is not True or attempt.get('attemptId') != attempt_id or cycle.get('activeAttemptId') != attempt_id
            or attempt.get('status') != 'running' or cycle.get('protocolState') not in ('executing', 'recovering')
            or bool(attempt.get('recoveryId')) != status.get('recovery')
            or status.get('remainingSeconds') is None or status['remainingSeconds'] <= 0):
        raise ValueError('ATTEMPT_NOT_ACTIVE: status unavailable, expired or mismatched; no writes')
    return status


def relative_path(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or '\\' in name:
        raise ValueError('RELATIVE_PATH_REQUIRED')
    if any(part in ('', '.', '..') for part in name.split('/')):
        raise ValueError('RELATIVE_PATH_REQUIRED')
    return safe_path(root, name)


def generate(plan_path, primary, evidence, *, input_directory=INPUT_DIRECTORY):
    root = Path(os.environ.get('AUTONOMOUS_COMPANY_ROOT', '/workspace')).resolve()
    attempt_id = os.environ['AUTONOMOUS_COMPANY_ATTEMPT_ID']
    initial = active_status(attempt_id)
    recovery = initial['recovery']
    if recovery != (os.environ.get('COMPANY_HARNESS_RECOVERY', '0') == '1'):
        raise ValueError('RECOVERY_MISMATCH')
    output = protocol_handoff_path(attempt_id) if recovery else f'docs/harness/{attempt_id}-handoff.json'
    target = relative_path(root, output)
    observations = {}

    def read(path, limit):
        data = regular_bytes(path, limit)
        observations[path] = (data, limit)
        return data

    plan = json.loads(read(relative_path(root, plan_path), MATERIAL_LIMIT))
    paths = list(dict.fromkeys([primary] + evidence))
    local, sizes = {}, {}
    project = initial['cycle']['contract'].get('project')
    for name in paths:
        path = relative_path(root, name)
        if name == output or not (name.startswith('docs/') or name == 'memories/consensus.md'
                                  or project and name.startswith(project + '/')):
            raise ValueError('EVIDENCE_SCOPE: ' + name)
        data = read(path, MATERIAL_LIMIT)
        ref, _ = material(name)
        if ref['sha256'] != hashlib.sha256(data).hexdigest():
            raise ValueError('MATERIAL_CHANGED: ' + name)
        local[name] = ref
        sizes[ref['evidenceId']] = len(data)

    inputs = {}
    index = json.loads(read(safe_path(input_directory, 'index.json'), MATERIAL_LIMIT))
    if not isinstance(index, list):
        raise ValueError('INPUT_INDEX')
    # Only selected immutable materials contribute bytes; never copy history into docs.
    selectors = plan.get('inputs', []) + plan.get('prerequisites', []) if isinstance(plan, dict) and isinstance(plan.get('inputs'), list) and isinstance(plan.get('prerequisites'), list) else []
    selected = [s['input'] for s in selectors if isinstance(s, dict) and set(s) == {'input'} and isinstance(s['input'], str)]
    for name in dict.fromkeys(selected):
        entries = [x for x in index if isinstance(x, dict) and x.get('file') == name]
        if len(entries) != 1:
            raise ValueError('INPUT_INDEX: ' + name)
        entry = entries[0]
        if (not isinstance(entry.get('evidenceId'), str) or not entry['evidenceId']
                or not isinstance(entry.get('mediaType'), str) or not entry['mediaType']):
            raise ValueError('INPUT_INDEX: ' + name)
        data = read(relative_path(input_directory, name), MATERIAL_LIMIT)
        if hashlib.sha256(data).hexdigest() != entry.get('sha256'):
            raise ValueError('INPUT_SHA: ' + name)
        inputs[name] = entry
        sizes[entry['evidenceId']] = len(data)
    envelope = compile_plan(plan, local[primary], inputs, local)
    refs = unique(envelope['nextContract']['inputRefs'] + envelope['nextContract']['prerequisiteRefs'])
    input_bytes = sum(sizes[ref['evidenceId']] for ref in refs)
    if input_bytes > MAX_BYTES:
        raise ValueError('INPUT_PACKAGE_LIMIT: bytes')
    data = (json.dumps(envelope, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8')
    if recovery:
        validate_protocol_handoff(data)
    elif len(data) > MATERIAL_LIMIT:
        raise ValueError('MATERIAL_LIMIT: handoff')
    current = active_status(attempt_id)
    if current['recovery'] != recovery or current['cycle']['contract'] != initial['cycle']['contract']:
        raise ValueError('ATTEMPT_CHANGED')
    for path, (original, limit) in observations.items():
        if regular_bytes(path, limit) != original:
            raise ValueError('MATERIAL_CHANGED: ' + str(path))
    # Host version verification still owns races after this check. One coordinator
    # must serialize generation and submission within the attempt.
    target = relative_path(root, output)
    if target.exists():
        regular_bytes(target, MATERIAL_LIMIT)
    if recovery:
        # The kernel-provisioned directory permits exactly handoff.json, no temp siblings.
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
        with os.fdopen(os.open(target, flags, 0o600), 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(target, envelope)
    if regular_bytes(target, MATERIAL_LIMIT) != data:
        raise ValueError('OUTPUT_CHANGED')
    return {'handoffPath': output, 'primaryPath': primary, 'evidencePaths': paths + [output],
            'inputCount': len(refs), 'inputBytes': input_bytes, 'outputSha256': hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--primary', required=True)
    parser.add_argument('--evidence', action='append', default=[])
    args = parser.parse_args()
    print(json.dumps(generate(args.plan, args.primary, args.evidence), ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (KeyError, OSError, ValueError, TypeError, IsolationError) as error:
        print(json.dumps({'status': 'rejected', 'errorCode': 'HANDOFF_ERROR', 'detail': str(error)}, ensure_ascii=False))
        sys.exit(2)
