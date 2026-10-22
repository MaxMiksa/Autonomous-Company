"""Pure read adapters for logical cycles; never migrates source records."""
from copy import deepcopy


OUTCOMES = {
    'completed': 'completed', 'complete': 'completed',
    'partial': 'handoff', 'handoff': 'handoff', 'partial_handoff': 'handoff',
    'blocked': 'blocked', 'failed': 'failed', 'interrupted': 'interrupted',
    'not_started': 'not_started', 'submission_missing': 'interrupted',
}
STATES = {
    'allocated': 'not_started', 'assigned': 'not_started',
    'executing': 'running', 'running': 'running', 'correcting': 'correcting',
    'submitted': 'validating', 'validating': 'validating', 'closing': 'closing',
    'recovering': 'recovering', 'recovery_pending': 'recovering', 'awaiting_recovery': 'recovering',
    'attention': 'unknown', 'needs_attention': 'unknown',
}


def _in_scope(cycle, scope):
    if scope.get('productId'):
        if cycle.get('productId'):
            return cycle['productId'] == scope['productId']
        return bool(scope.get('includeExploration') is True and scope.get('explorationId')
                    and cycle.get('explorationId') == scope['explorationId'])
    return bool(scope.get('explorationId') and not cycle.get('productId')
                and cycle.get('explorationId') == scope['explorationId'])


def _verify_overlay(cycle, recorded, scope):
    product = recorded.get('stableProductId') or recorded.get('productId')
    exploration = recorded.get('explorationId')
    kind = recorded.get('identityKind') or ('product' if product else 'exploration' if exploration else None)
    if ((product and product != cycle.get('productId'))
            or (exploration and exploration != cycle.get('explorationId'))
            or (kind == 'exploration' and cycle.get('productId'))
            or (kind == 'product' and not cycle.get('productId'))):
        raise ValueError('Cycle ownership conflicts with journal identity')
    if scope and not _in_scope(cycle, scope):
        raise ValueError('Cycle is outside the selected identity scope')
    if (scope and scope.get('productId') and kind == 'exploration'
            and recorded.get('linkedProductId') and recorded['linkedProductId'] != scope['productId']):
        raise ValueError('Exploration association conflicts with selected product')
    if not scope and not (product or exploration):
        raise ValueError('Cycle ownership cannot be verified')


def legacy_cycle(row):
    """A virtual legacy attempt preserves original identities and uncertainty."""
    result = deepcopy(row)
    identity = row['id']
    result.update(protocolState='legacy', outcome=None, harnessVersion=None,
                  activeAttemptId=None, recoveries=[], qualityApplicability=[],
                  continuationDecision={'allowed': False, 'reason': 'legacy_not_recorded'})
    result['attempts'] = [{
        'attemptId': 'legacy:' + identity, 'cycleId': identity, 'legacy': True,
        'status': row.get('status', 'unknown'),
        'startedAt': row.get('startedAt'), 'endedAt': row.get('endedAt'),
        'report': deepcopy(row.get('workReport')),
        'events': deepcopy(row.get('events', [])),
        'usage': deepcopy(row.get('usage')),
        'provenance': 'legacy_cycle',
    }]
    result['harnessReport'] = {'status': row.get('workReportStatus', 'missing'),
                               'source': 'legacy', 'value': deepcopy(row.get('workReport'))}
    return result


def protocol_cycle(cycle, recorded=None):
    """Derive compatible presentation fields from one authoritative cycle."""
    result = deepcopy(recorded or {})
    identity = cycle['cycleId']
    state = cycle.get('protocolState', 'unknown')
    outcome = cycle.get('outcome')
    timing = deepcopy(cycle.get('time') or {})
    attempts = deepcopy(cycle.get('attempts') or [])
    for attempt in attempts:
        attempt.pop('context', None)
        attempt.pop('ownership', None)
    active = next((attempt for attempt in attempts
                   if attempt.get('attemptId') == cycle.get('activeAttemptId')), None)
    status = OUTCOMES.get(outcome, 'unknown') if state == 'closed' else STATES.get(state, 'unknown')
    result.update(id=identity, cycleId=identity, harnessVersion=2,
                  protocolState=state, outcome=outcome, status=status,
                  objective=cycle.get('objective'), workKind=cycle.get('workKind'),
                  contract=deepcopy(cycle.get('contract') or {}),
                  timeClass=cycle.get('timeClass'), time=timing,
                  activeAttemptId=cycle.get('activeAttemptId'), attempts=attempts,
                  recoveries=deepcopy(cycle.get('recoveries') or []),
                  evidenceRefs=deepcopy(((cycle.get('closeReceipt') or {}).get('input') or {}).get('verification', {}).get('evidenceRefs', [])),
                  primaryEvidenceId=cycle.get('primaryEvidenceId'),
                  qualityApplicability=deepcopy(cycle.get('qualityApplicability') or []),
                  continuationDecision=deepcopy(cycle.get('continuationDecision') or {
                      'allowed': False, 'reason': 'not_evaluated'}))
    # Formal numbering comes from the original identity ledger, never list length.
    if cycle.get('sequenceNumber') is not None:
        result['sequenceNumber'] = cycle['sequenceNumber']
    for key in ('productId', 'explorationId'):
        if key in cycle:
            result[key] = cycle[key]
    result['startedAt'] = timing.get('startedAt')
    result['endedAt'] = timing.get('endedAt')
    result['elapsedSeconds'] = timing.get('totalSeconds')
    result['elapsedReliable'] = timing.get('reliability') == 'reliable'
    result['active'] = bool(state != 'closed' and active and active.get('status') == 'running')
    usage = deepcopy(cycle.get('usage') or {
        'status': 'partial', 'cost': None, 'inputTokens': None, 'outputTokens': None,
        'totalTokens': None, 'costComplete': False, 'inputTokensComplete': False,
        'outputTokensComplete': False, 'totalTokensComplete': False,
        'coverage': {'scope': 'cycle', 'callSetConfirmed': False}})
    result['usage'] = usage
    result['costUsd'] = usage.get('cost')
    result['costStatus'] = ('reported' if usage.get('costComplete') is True else
                            'partial' if usage.get('cost') is not None else 'unavailable')
    result['harnessReport'] = deepcopy(cycle.get('report') or {'status': 'missing'})
    if result.get('primaryEvidenceId') is None:
        submission_id = ((cycle.get('closeReceipt') or {}).get('input') or {}).get('submissionId')
        submission = next((row for row in cycle.get('submissions', []) if row['submissionId'] == submission_id), None)
        if submission:
            refs = submission['payload'].get('evidenceRefs', [])
            result['primaryEvidenceId'] = submission['payload'].get('primaryEvidenceId') or (refs[0]['evidenceId'] if len(refs) == 1 else None)
    report = result['harnessReport']
    # The legacy report field is text. New structured content stays in its own field.
    value = report if isinstance(report, dict) else {}
    usable = isinstance(value, dict) and report.get('status', 'available') not in {'missing', 'invalid'}
    result['workReport'] = None
    result['workReportStatus'] = 'missing'
    result['report'] = result['summary'] = ''
    if usable:
        result['workReport'] = {key: value[key] for key in ('title', 'summary', 'blocker') if key in value}
        result['workReport']['phase'] = value.get('reportedPhase')
        result['workReport'].update(recorded_at=value.get('reportedAt'), final=False,
            source='model_report', reportSource='publish_progress', reporterAttemptId=value.get('reporterAttemptId'),
            reportRevision=value.get('reportRevision'))
        result['workReportStatus'] = 'valid'
        result['report'] = result['summary'] = value.get('summary', '')
    selected = active or (attempts[-1] if attempts else None)
    for attempt in attempts:
        attempt['eventsHealth'] = deepcopy((attempt.get('actualResult') or {}).get('eventsHealth') or {
            'status': 'missing', 'truncated': False, 'gaps': [], 'asOf': None})
    result['eventsHealth'] = deepcopy(selected['eventsHealth']) if selected else {
        'status': 'missing', 'truncated': False, 'gaps': [], 'asOf': None}
    result['events'] = []
    for event in selected.get('events', []) if selected else []:
        value = deepcopy(event.get('event', event))
        value.update(sequence=event.get('sequence'), observedAt=event.get('observedAt'),
                     attemptId=selected['attemptId'], cycleId=identity)
        result['events'].append(value)
    result['eventStatus'] = 'partial' if result['eventsHealth'].get('status') == 'partial' else 'recorded' if result['events'] else 'missing'
    return result


def project_cycles(recorded_cycles, harness_snapshot=None, identity_scope=None):
    """Overlay cycles by ID without changing order, numbering or old records."""
    snapshot = harness_snapshot or {}
    logical = {}
    for cycle in snapshot.get('cycles', []):
        identity = cycle['cycleId']
        if identity in logical:
            raise ValueError('Conflicting cycle identity in Harness snapshot')
        logical[identity] = cycle
    result = []
    seen = set()
    for row in recorded_cycles:
        identity = row['id']
        if identity in seen:
            raise ValueError('Conflicting cycle identity in journal projection')
        seen.add(identity)
        if identity in logical:
            _verify_overlay(logical[identity], row, identity_scope)
            result.append(protocol_cycle(logical[identity], row))
        else:
            result.append(legacy_cycle(row))
    # Newly reserved cycles may not have a legacy usage row yet.
    for cycle in snapshot.get('cycles', []):
        belongs = identity_scope and _in_scope(cycle, identity_scope)
        if belongs and cycle['cycleId'] not in seen:
            seen.add(cycle['cycleId'])
            result.append(protocol_cycle(cycle))
    return result
