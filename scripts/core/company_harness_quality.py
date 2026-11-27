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

MILESTONE_ORDER = ('direction', 'definition', 'visual_direction', 'prototype', 'implementation', 'delivery')
GATED_ARTIFACTS = {artifact for reqs in REQUIRED.values() for artifact in reqs}
DOWNSTREAM_CONSUMERS = {
    artifact: tuple(work_kind for work_kind, reqs in REQUIRED.items() if artifact in reqs)
    for artifact in GATED_ARTIFACTS
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


def _advancing_flags(cycles):
    """Mark closed cycles that materially advance a milestone or unlock a new gate."""
    unlocked = set()
    flags = []
    for cycle in cycles:
        advances = False
        if cycle.get('outcome') == 'completed':
            if cycle['contract'].get('artifactKind') in MILESTONE_ORDER:
                advances = True
            elif cycle['contract'].get('workKind') == 'review':
                for record in cycle.get('qualityApplicability', []):
                    ak = record.get('artifactKind')
                    if ak not in GATED_ARTIFACTS:
                        continue
                    target = record.get('targetRef') or {}
                    key_base = (ak, target.get('evidenceId'), target.get('sha256'))
                    for wk in record.get('workKinds', []):
                        if wk not in DOWNSTREAM_CONSUMERS.get(ak, ()):
                            continue
                        gate = (*key_base, wk)
                        if record.get('verdict') == 'passed':
                            if gate not in unlocked:
                                unlocked.add(gate)
                                advances = True
        flags.append(advances)
    return flags


def _latest_passed_review(cycles, artifact_kind, head_ref, consumer_work_kind):
    records = [
        record
        for cycle in cycles if cycle.get('outcome') == 'completed'
        for record in cycle.get('qualityApplicability', [])
        if record.get('artifactKind') == artifact_kind
        and record.get('targetRef') == head_ref
        and consumer_work_kind in record.get('workKinds', [])
    ]
    return bool(records and records[-1].get('verdict') == 'passed')


def progression_state(store, identity, *, pending_cycle=None, pending_quality=None):
    """Summarize milestone progression, consecutive non-advancing streaks, and anti-spin advice."""
    cycles = _closed(store, identity, pending_cycle, pending_quality)
    state = artifact_state(store, identity, pending_cycle=pending_cycle, pending_quality=pending_quality)
    heads = state['heads']
    highest_milestone = None
    for milestone in MILESTONE_ORDER:
        if milestone in heads:
            highest_milestone = milestone
    if highest_milestone is None:
        next_milestone = 'direction'
    elif highest_milestone == 'delivery':
        next_milestone = 'refinement'
    else:
        next_milestone = MILESTONE_ORDER[MILESTONE_ORDER.index(highest_milestone) + 1]

    cycles_since_milestone = 0
    for cycle in reversed(cycles):
        if cycle.get('outcome') == 'completed' and cycle['contract'].get('artifactKind') in MILESTONE_ORDER:
            break
        cycles_since_milestone += 1

    advancing = _advancing_flags(cycles)
    consecutive_non_advancing = 0
    for did_advance in reversed(advancing):
        if did_advance:
            break
        consecutive_non_advancing += 1

    consecutive_same_work_kind = None
    if cycles:
        last_wk = cycles[-1]['contract'].get('workKind')
        same_count = 0
        for cycle in reversed(cycles):
            if cycle['contract'].get('workKind') != last_wk:
                break
            same_count += 1
        consecutive_same_work_kind = {'workKind': last_wk, 'count': same_count}

    consecutive_partial = {}
    for item in state['incomplete']:
        ak = item['artifactKind']
        partial_count = 0
        for cycle in reversed(cycles):
            if cycle['contract'].get('artifactKind') == ak and cycle.get('outcome') == 'partial':
                partial_count += 1
            elif cycle['contract'].get('artifactKind') == ak:
                break
        consecutive_partial[ak] = partial_count

    if consecutive_non_advancing >= 5 or cycles_since_milestone >= 6:
        stagnation_level = 'critical'
    elif consecutive_non_advancing >= 3 or cycles_since_milestone >= 4:
        stagnation_level = 'warning'
    else:
        stagnation_level = 'none'

    advisory = None
    if stagnation_level != 'none':
        if state['incomplete']:
            producers = ', '.join(item['requiredProductionWorkKind'] for item in state['incomplete'])
            advisory = (
                f'STAGNATION ({stagnation_level}): incomplete partial artifact(s) blocking progress; '
                f'finish via original production workKind ({producers}) and submit completed.'
            )
        elif highest_milestone is None:
            advisory = (
                f'STAGNATION ({stagnation_level}): {consecutive_non_advancing} consecutive non-advancing cycles '
                'with no direction head. Compare 2-3 bounded feasible candidates now and propose '
                'workKind=direction for the strongest winner (commercial validation is deferred), or record a concrete blocker.'
            )
        else:
            next_work_kind = PRODUCER_FOR_ARTIFACT.get(next_milestone, next_milestone)
            missing_heads = [ak for ak in REQUIRED.get(next_work_kind, ()) if ak not in heads]
            if missing_heads:
                producers = ', '.join(PRODUCER_FOR_ARTIFACT.get(ak, ak) for ak in missing_heads)
                advisory = (
                    f'STAGNATION ({stagnation_level}): {next_work_kind} is missing completed prerequisite head(s) '
                    f'({", ".join(missing_heads)}); produce via workKind={producers}.'
                )
            else:
                missing_reviews = [
                    ak for ak in REQUIRED.get(next_work_kind, ())
                    if not _latest_passed_review(
                        cycles, ak,
                        {'evidenceId': heads[ak]['evidenceId'], 'sha256': heads[ak]['sha256']},
                        next_work_kind,
                    )
                ]
                if missing_reviews:
                    advisory = (
                        f'STAGNATION ({stagnation_level}): completed head(s) ({", ".join(missing_reviews)}) '
                        f'lack a passed independent review covering {next_work_kind}; propose workKind=review targeting only those head(s).'
                    )
                else:
                    advisory = (
                        f'STAGNATION ({stagnation_level}): prerequisites for {next_work_kind} are already satisfied; '
                        f'propose workKind={next_work_kind} directly instead of repeating research or review.'
                    )

    return {
        'closedCycles': len(cycles),
        'highestMilestone': highest_milestone,
        'nextMilestone': next_milestone,
        'cyclesSinceLastMilestone': cycles_since_milestone,
        'consecutiveNonAdvancing': consecutive_non_advancing,
        'consecutiveSameWorkKind': consecutive_same_work_kind,
        'consecutivePartialByArtifact': consecutive_partial,
        'stagnationLevel': stagnation_level,
        'advisory': advisory,
    }


def _target_already_satisfied(cycles, target_ref, producer_artifact):
    records = [
        record
        for cycle in cycles if cycle.get('outcome') == 'completed'
        for record in cycle.get('qualityApplicability', [])
        if record.get('targetRef') == target_ref
    ]
    if not records:
        return False
    consumers = DOWNSTREAM_CONSUMERS.get(producer_artifact, ())
    if not consumers:
        return records[-1].get('verdict') == 'passed'
    for work_kind in consumers:
        matching = [record for record in records if work_kind in record.get('workKinds', [])]
        if not matching or matching[-1].get('verdict') != 'passed':
            return False
    return True


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
    if (kind == 'objective_selection' and cycles
            and cycles[-1]['contract'].get('workKind') == 'objective_selection'
            and cycles[-1].get('outcome') == 'completed'):
        raise HarnessError(
            'SPIN_GUARD', 'workKind',
            'previous cycle already completed objective_selection; propose an actionable workKind (research, direction, definition, etc.) instead of chaining objective_selection',
        )
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
    review_targets = None
    if kind == 'review':
        if not inputs:
            raise HarnessError('EVIDENCE_MISSING', 'inputRefs')
        req_cfg = proposal.get('reviewRequirement')
        if req_cfg is not None:
            if not isinstance(req_cfg, dict):
                raise HarnessError('INVALID_FIELD', 'reviewRequirement')
            raw_targets = req_cfg.get('targetRefs')
            if raw_targets is not None:
                if not isinstance(raw_targets, list) or not raw_targets:
                    raise HarnessError('INVALID_FIELD', 'reviewRequirement', 'targetRefs must be a non-empty list')
                normalized = [_ref(ref) for ref in raw_targets]
                review_targets = [ref for idx, ref in enumerate(normalized) if ref not in normalized[:idx]]
                if any(ref not in inputs for ref in review_targets):
                    raise HarnessError(
                        'INVALID_FIELD', 'reviewRequirement',
                        'every reviewRequirement.targetRefs entry must also appear in inputRefs',
                    )
        if review_targets is None:
            review_targets = [ref for idx, ref in enumerate(inputs) if ref not in inputs[:idx]]
        target_producers = [_evidence(store, ref, cycles)[1] for ref in review_targets]
        if all(producer['contract'].get('artifactKind') == 'review' for producer in target_producers):
            raise HarnessError(
                'SPIN_GUARD', 'inputRefs',
                'cannot propose review solely on prior review artifact(s); act on the verdict or propose the next production workKind',
            )
        if all(_target_already_satisfied(cycles, ref, producer['contract'].get('artifactKind'))
               for ref, producer in zip(review_targets, target_producers)):
            raise HarnessError(
                'REDUNDANT_REVIEW', 'inputRefs',
                'target version(s) already have passed independent review(s) covering all required downstream stages; advance to the next production workKind instead of repeating review',
            )
    result = {key: deepcopy(proposal[key]) for key in (
        'objective', 'workKind', 'scope', 'completionOrHandoff', 'reviewRequirement', 'revisesKind') if key in proposal}
    result.update(timeClass=time_class, artifactKind=artifact, inputRefs=inputs,
                  prerequisiteRefs=prerequisites)
    if kind == 'review':
        result['reviewRequirement'] = {'independent': True, 'targetRefs': review_targets}
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
    req_targets = (cycle['contract'].get('reviewRequirement') or {}).get('targetRefs')
    expected_source = req_targets if isinstance(req_targets, list) and req_targets else cycle['contract'].get('inputRefs', [])
    expected = [_ref(ref) for ref in expected_source]
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
