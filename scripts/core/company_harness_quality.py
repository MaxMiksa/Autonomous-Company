"""Versioned quality prerequisites; host decisions, never model permissions."""
from copy import deepcopy

from company_harness import HarnessError
from company_harness_inputs import load_inputs
from company_harness_contract import ARTIFACTS


REQUIRED = {
    'definition': ('direction',), 'experience': ('direction',),
    'visual_exploration': ('definition',),
    'prototype': ('definition', 'visual_direction'),
    'implementation': ('definition', 'prototype'),
    'refinement': ('definition', 'prototype'),
    'delivery': ('definition', 'prototype', 'implementation'),
}

PRODUCER_FOR_ARTIFACT = {
    'objective': 'objective_selection',
    'research': 'research',
    'direction': 'direction',
    'definition': 'definition',
    'experience': 'experience',
    'visual_direction': 'visual_exploration',
    'prototype': 'prototype',
    'implementation': 'implementation',
    'review': 'review',
    'validation': 'validation',
    'delivery': 'delivery',
}


def _ref(value):
    if (not isinstance(value, dict) or not isinstance(value.get('evidenceId'), str)
            or not value['evidenceId'] or not isinstance(value.get('sha256'), str)
            or len(value['sha256']) != 64):
        raise HarnessError('INVALID_FIELD', 'evidenceRef')
    return {key: value[key] for key in ('evidenceId', 'sha256')}


def _belongs(cycle, identity):
    if identity.get('productId'):
        return (cycle.get('productId') == identity['productId'] or
                not cycle.get('productId') and identity.get('explorationId') and
                cycle.get('explorationId') == identity['explorationId'])
    return bool(identity.get('explorationId') and not cycle.get('productId') and
                cycle.get('explorationId') == identity['explorationId'])


def _closed(store, identity, pending_cycle=None, pending_quality=None):
    cycles = [cycle for cycle in store.snapshot()['cycles']
              if _belongs(cycle, identity) and cycle.get('protocolState') == 'closed']
    if pending_cycle is not None:
        if (not _belongs(pending_cycle, identity) or pending_cycle.get('activeAttemptId') or
                not pending_cycle.get('attempts') or
                any(not attempt.get('writersStopped') for attempt in pending_cycle['attempts'])):
            raise HarnessError('WRITERS_UNCONFIRMED', 'pendingCycle')
        pending = deepcopy(pending_cycle)
        outcome = pending.get('outcome') or 'completed'
        if outcome not in {'completed', 'partial'}:
            raise HarnessError('CONTINUATION_BLOCKED', 'pendingCycle')
        pending.update(protocolState='closed', outcome=outcome,
                       qualityApplicability=deepcopy(pending_quality or []))
        cycles = [cycle for cycle in cycles if cycle['cycleId'] != pending['cycleId']] + [pending]
    return cycles


def _evidence(store, ref, cycles):
    ref = _ref(ref)
    value = store.read_evidence(ref['evidenceId'])
    if not value or value['sha256'] != ref['sha256']:
        raise HarnessError('EVIDENCE_MISSING', ref['evidenceId'])
    owner = next((cycle for cycle in cycles if cycle['cycleId'] == value['cycleId']), None)
    if owner is None:
        raise HarnessError('OWNER_MISMATCH', ref['evidenceId'])
    return value, owner


def _submission(cycle):
    close_input = (cycle.get('closeReceipt') or {}).get('input') or {}
    identity = close_input.get('submissionId')
    if identity:
        return next((row for row in cycle.get('submissions', []) if row['submissionId'] == identity), None)
    return cycle.get('submissions', [None])[-1] if cycle.get('submissions') else None


def _primary(cycle, submission):
    if not submission or submission['payload'].get('result') != 'completed':
        return None
    refs = submission['payload'].get('evidenceRefs', [])
    primary_id = submission['payload'].get('primaryEvidenceId')
    if primary_id:
        matches = [ref for ref in refs if ref.get('evidenceId') == primary_id]
    else:
        matches = refs if len(refs) == 1 else []
    if len(matches) != 1:
        raise HarnessError('PRIMARY_EVIDENCE_REQUIRED', 'primaryEvidenceId')
    return _ref(matches[0])


def _primary_or_none(submission):
    if not submission:
        return None
    payload = submission.get('payload') or {}
    refs = payload.get('evidenceRefs', [])
    primary_id = payload.get('primaryEvidenceId')
    if primary_id:
        match = next((ref for ref in refs if ref.get('evidenceId') == primary_id), None)
        return _ref(match) if match else None
    if len(refs) == 1:
        return _ref(refs[0])
    return None


def artifact_state(store, identity, *, pending_cycle=None, pending_quality=None):
    """Summarize completed artifact heads vs partial/unclosed artifact kinds."""
    cycles = _closed(store, identity, pending_cycle, pending_quality)
    heads = {}
    latest = {}
    for cycle in cycles:
        artifact_kind = cycle['contract'].get('artifactKind')
        if not artifact_kind or artifact_kind == 'review':
            continue
        submission = _submission(cycle)
        outcome = cycle.get('outcome')
        if outcome == 'completed':
            primary = _primary(cycle, submission)
            if primary:
                heads[artifact_kind] = {
                    **primary,
                    'cycleId': cycle['cycleId'],
                    'workKind': cycle.get('workKind'),
                }
        primary_any = _primary_or_none(submission)
        latest[artifact_kind] = {
            'cycleId': cycle['cycleId'],
            'workKind': cycle.get('workKind'),
            'outcome': outcome,
            'primaryEvidenceId': primary_any['evidenceId'] if primary_any else None,
        }
    for artifact_kind, head in heads.items():
        head_ref = {'evidenceId': head['evidenceId'], 'sha256': head['sha256']}
        passed_work_kinds = []
        for cycle in cycles:
            if cycle.get('outcome') != 'completed':
                continue
            for record in cycle.get('qualityApplicability', []):
                if (record.get('artifactKind') == artifact_kind
                        and record.get('targetRef') == head_ref
                        and record.get('verdict') == 'passed'):
                    passed_work_kinds = list(record.get('workKinds', []))
        head['passedWorkKinds'] = passed_work_kinds
    for artifact_kind, info in latest.items():
        info['hasCompletedHead'] = artifact_kind in heads
    incomplete = [
        {
            'artifactKind': artifact_kind,
            'latestWorkKind': info['workKind'],
            'latestOutcome': info['outcome'],
            'requiredProductionWorkKind': PRODUCER_FOR_ARTIFACT.get(artifact_kind, info['workKind']),
        }
        for artifact_kind, info in latest.items()
        if not info['hasCompletedHead'] and info['outcome'] == 'partial'
    ]
    return {'heads': heads, 'latest': latest, 'incomplete': incomplete}


def prepare_contract(store, proposal, identity, *, pending_cycle=None, pending_quality=None):
    """Validate a proposal; dispatch must recheck after any prospective closure."""
    if not isinstance(identity, dict) or not (identity.get('productId') or identity.get('explorationId')):
        raise HarnessError('OWNER_MISMATCH', 'identity')
    if (not isinstance(proposal, dict) or not isinstance(proposal.get('workKind'), str)
            or proposal['workKind'] not in {*ARTIFACTS, 'revision'}):
        raise HarnessError('INVALID_FIELD', 'workKind')
    kind = proposal['workKind']
    for field in ('objective', 'scope', 'completionOrHandoff'):
        if not proposal.get(field):
            raise HarnessError('INVALID_FIELD', field)
    if not isinstance(proposal['objective'], str) or len(proposal['objective']) > 256:
        raise HarnessError('INVALID_FIELD', 'objective')
    artifact = ARTIFACTS.get(kind)
    if kind == 'revision':
        artifact = proposal.get('revisesKind')
        if not isinstance(artifact, str) or artifact not in set(ARTIFACTS.values()) - {'objective', 'review', 'delivery'}:
            raise HarnessError('INVALID_FIELD', 'revisesKind')
    time_class = proposal.get('timeClass', 'regular')
    development = kind in {'implementation', 'refinement'} or kind == 'revision' and artifact == 'implementation'
    if (not isinstance(time_class, str) or time_class not in {'regular', 'development'}
            or time_class == 'development' and not development):
        raise HarnessError('INVALID_FIELD', 'timeClass')
    cycles = _closed(store, identity, pending_cycle, pending_quality)
    for field in ('inputRefs', 'prerequisiteRefs'):
        if not isinstance(proposal.get(field, []), list):
            raise HarnessError('INVALID_FIELD', field)
    inputs = [_ref(ref) for ref in proposal.get('inputRefs', [])]
    prerequisites = [_ref(ref) for ref in proposal.get('prerequisiteRefs', [])]
    for ref in inputs + prerequisites:
        _evidence(store, ref, cycles)
    load_inputs(store, {'inputRefs': inputs, 'prerequisiteRefs': prerequisites})
    state = artifact_state(store, identity, pending_cycle=pending_cycle, pending_quality=pending_quality)
    heads = {
        ak: {'evidenceId': info['evidenceId'], 'sha256': info['sha256']}
        for ak, info in state['heads'].items()
    }
    needed = REQUIRED.get(kind, ())
    if kind == 'revision':
        producer_wk = PRODUCER_FOR_ARTIFACT.get(artifact, artifact)
        if artifact not in heads:
            latest_info = state['latest'].get(artifact)
            if latest_info and latest_info.get('outcome') == 'partial':
                raise HarnessError(
                    'STALE_INPUT', 'revisesKind',
                    f"no completed head exists for {artifact} (latest {producer_wk} closed partial); finish it with workKind={producer_wk} instead of revision",
                )
            raise HarnessError(
                'STALE_INPUT', 'revisesKind',
                f"no completed head exists for {artifact}; produce it with workKind={producer_wk} instead of revision",
            )
        if heads[artifact] not in inputs:
            raise HarnessError(
                'STALE_INPUT', 'revisesKind',
                f"include current completed {artifact} head {heads[artifact]['evidenceId']} in inputRefs",
            )
        downstream = next((name for name, value in ARTIFACTS.items() if value == artifact), None)
        needed = REQUIRED.get(downstream, ())
    for artifact_kind in needed:
        head = heads.get(artifact_kind)
        producer_wk = PRODUCER_FOR_ARTIFACT.get(artifact_kind, artifact_kind)
        if not head:
            latest_info = state['latest'].get(artifact_kind)
            if latest_info and latest_info.get('outcome') == 'partial':
                raise HarnessError(
                    'PREREQUISITE_MISSING', artifact_kind,
                    f"{artifact_kind} has no completed head (latest {producer_wk} closed partial); finish it with workKind={producer_wk} reusing existing assets before review/downstream, not review or revision",
                )
            raise HarnessError(
                'PREREQUISITE_MISSING', artifact_kind,
                f"{artifact_kind} has no completed head; produce it with workKind={producer_wk} first",
            )
        if head not in inputs:
            raise HarnessError(
                'PREREQUISITE_MISSING', artifact_kind,
                f"include current completed {artifact_kind} head {head['evidenceId']} in inputRefs",
            )
        applicable = [record
            for cycle in cycles if cycle.get('outcome') == 'completed'
            for record in cycle.get('qualityApplicability', [])
            if record.get('artifactKind') == artifact_kind and record.get('targetRef') == head
            and kind in record.get('workKinds', [])]
        current = applicable[-1] if applicable else {}
        if current.get('verdict') != 'passed' or not any(
                _ref(ref) in prerequisites for ref in current.get('reviewEvidenceRefs', [])):
            if current.get('verdict') == 'passed' and current.get('reviewEvidenceRefs'):
                review_id = current['reviewEvidenceRefs'][0]['evidenceId']
                detail = (
                    f"include passed independent review {review_id} "
                    f"(for {artifact_kind} head {head['evidenceId']} covering {kind}) in prerequisiteRefs"
                )
            else:
                detail = (
                    f"no passed independent review exists for {artifact_kind} head {head['evidenceId']} "
                    f"covering {kind}; run workKind=review on it first"
                )
            raise HarnessError('REVIEW_REQUIRED', artifact_kind, detail)
    if kind == 'review' and not inputs:
        raise HarnessError('EVIDENCE_MISSING', 'inputRefs')
    result = {key: deepcopy(proposal[key]) for key in (
        'objective', 'workKind', 'scope', 'completionOrHandoff', 'reviewRequirement', 'revisesKind') if key in proposal}
    result.update(timeClass=time_class, artifactKind=artifact, inputRefs=inputs,
                  prerequisiteRefs=prerequisites)
    if kind == 'review':
        result['reviewRequirement'] = {'independent': True, 'targetRefs': inputs}
    return result


def close_review(store, cycle, submission):
    """Bind an actual independent reviewer to immutable versions, without permission."""
    if not submission:
        return []
    primary = _primary(cycle, submission)
    if primary:
        value = store.read_evidence(primary['evidenceId'])
        if not value or value['cycleId'] != cycle['cycleId'] or value['sha256'] != primary['sha256']:
            raise HarnessError('EVIDENCE_MISSING', 'primaryEvidenceId')
    if cycle['contract'].get('workKind') != 'review' or submission['payload'].get('result') != 'completed':
        return []
    review = submission['payload'].get('review')
    if (not isinstance(review, dict) or not isinstance(review.get('verdict'), str)
            or review['verdict'] not in {'passed', 'changes_required', 'unverifiable'}):
        raise HarnessError('INVALID_REVIEW', 'verdict')
    if not isinstance(review.get('targetRefs'), list):
        raise HarnessError('INVALID_REVIEW', 'targetRefs')
    targets = [_ref(ref) for ref in review['targetRefs']]
    expected = [_ref(ref) for ref in cycle['contract'].get('inputRefs', [])]
    if not targets or targets != expected:
        raise HarnessError('INVALID_REVIEW', 'targetRefs')
    if not isinstance(review.get('issues'), list) or any(
            isinstance(issue, dict) and 'blocking' in issue and type(issue['blocking']) is not bool
            for issue in review['issues']) or (
            review['verdict'] == 'passed' and any(isinstance(issue, dict) and issue.get('blocking') is True
                                                 for issue in review['issues'])):
        raise HarnessError('INVALID_REVIEW', 'issues')
    work_kinds = review.get('qualityApplicability')
    if not isinstance(work_kinds, list) or not all(isinstance(kind, str) and kind in {*ARTIFACTS, 'revision'} for kind in work_kinds):
        raise HarnessError('INVALID_REVIEW', 'qualityApplicability')
    reviewer = next((attempt for attempt in cycle['attempts']
                     if attempt['attemptId'] == submission['attemptId']), None)
    if reviewer is None:
        raise HarnessError('OWNER_MISMATCH', 'reviewerAttemptId')
    identity = {key: cycle.get(key) for key in ('productId', 'explorationId')}
    previous = _closed(store, identity)
    result = []
    for target in targets:
        evidence, producer = _evidence(store, target, previous)
        producer_attempt = (evidence.get('source') or {}).get('attemptId')
        if (producer['cycleId'] == cycle['cycleId'] or not producer_attempt or
                producer_attempt == reviewer['attemptId'] or
                producer_attempt not in {attempt['attemptId'] for attempt in producer.get('attempts', [])}):
            raise HarnessError('REVIEW_INDEPENDENCE_UNCONFIRMED', target['evidenceId'])
        result.append({'artifactKind': producer['contract'].get('artifactKind'), 'targetRef': target,
                       'verdict': review['verdict'], 'workKinds': work_kinds,
                       'issues': deepcopy(review['issues']), 'source': 'independent_review',
                       'reviewerAttemptId': reviewer['attemptId'], 'reviewCycleId': cycle['cycleId'],
                       'reviewEvidenceRefs': [_ref(ref) for ref in submission['payload']['evidenceRefs']]})
    return result
