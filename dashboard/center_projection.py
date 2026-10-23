"""Versioned read aggregation. HTTP routing and execution stay outside this module."""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from functools import partial
import base64
import hashlib
import json
import math
import re
import secrets
import threading
import time
import uuid
from urllib.parse import quote, urlencode

from center_store import CenterError
from harness_projection import project_cycles, legacy_cycle, _in_scope
from journal_data import timestamp, CYCLE_ID
from company_harness import HarnessStore
from product_identity import list_cycle_projections


def now():
    return datetime.now(timezone.utc).isoformat()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def core_cycle(row):
    timing = row.get('time') or {}
    return {**{key: row.get(key) for key in ('id', 'sequenceNumber', 'number', 'objective', 'workKind',
        'protocolState', 'outcome', 'activeAttemptId', 'status', 'active', 'qualityApplicability', 'executionIssue')},
        'continuationDecision': {key: value for key, value in (row.get('continuationDecision') or {}).items()
                                 if key not in {'checkedAt', 'observedAt', 'confirmedAt'}},
        'time': {key: timing.get(key) for key in ('startedAt', 'endedAt', 'deadline', 'timeClass', 'hardLimitSeconds', 'reliability')},
        'attempts': [{key: attempt.get(key) for key in ('attemptId', 'status', 'recoveryId', 'startedAt', 'endedAt', 'writersStopped')}
                     for attempt in row.get('attempts', [])]}


class CenterProjection:
    """Center-owned versions/cursors never write source records or grant execution."""
    def __init__(self, catalog):
        self.catalog, self.store = catalog, catalog.store
        self.lock = threading.RLock()
        self.cursors = {}
        self.ledger_cache = {}

    def binding(self, source, reader, authority):
        root = reader.root.stat()
        facts = [str(reader.root), root.st_dev, root.st_ino, source['kind'], source.get('productId'),
                 source.get('explorationId'), reader.scope.project]
        with self.store.transaction() as tx:
            current = tx.get('sources', source['sourceId'])
            if not current or current.get('detached') or any(current.get(key) != source.get(key) for key in
                    ('root', 'productId', 'explorationId', 'kind', 'revision')):
                raise CenterError('SOURCE_CHANGED', 'Source changed while reading its projection.', 409)
            record = tx.get('projection_bindings', source['sourceId'])
            binding_hash = fingerprint(facts)
            changed = not record or record['bindingFingerprint'] != binding_hash
            if changed:
                record = {'sourceBindingVersion': (record['sourceBindingVersion'] if record else 0) + 1,
                          'bindingFingerprint': binding_hash, 'authorityEpoch': authority,
                          'projectionEpoch': 'projection-' + uuid.uuid4().hex}
            elif record['authorityEpoch'] is not None and authority is None:
                raise CenterError('HARNESS_UNAVAILABLE', 'Previously authoritative Harness records are missing.', 503)
            elif record['authorityEpoch'] != authority:
                record.update(authorityEpoch=authority, projectionEpoch='projection-' + uuid.uuid4().hex)
            tx.put('projection_bindings', source['sourceId'], record)
        return record

    def version(self, source, binding, component, facts, *, status='available', as_of=None,
                error=None, truncated=False, gaps=None, target=None, observation=None, publish_current=False):
        identity = fingerprint([source['sourceId'], binding['sourceBindingVersion'], binding['projectionEpoch'], component, target])
        with self.store.transaction() as tx:
            current = tx.get('projection_bindings', source['sourceId'])
            if not current or any(current.get(key) != binding.get(key) for key in ('projectionEpoch', 'sourceBindingVersion')):
                raise CenterError('SOURCE_CHANGED', 'Source changed while reading a component.', 409)
            record = tx.get('projection_versions', identity)
            digest = fingerprint(facts)
            older = observation is not None and record and record.get('observation', 0) > observation
            if older and record['fingerprint'] != digest:
                if component == 'runtime':
                    raise CenterError('PROJECTION_RETRY', 'A newer observation already published the core.', 503)
                return {**self.not_requested(), 'status': 'unavailable', 'freshness': 'stale',
                        'asOf': record.get('asOf'), 'errorCode': 'STALE_OBSERVATION', 'target': target,
                        'lastConfirmedRevision': record['revision']}
            unavailable = status in {'unavailable', 'invalid'} and facts is None
            if not older and not unavailable and (record is None or record['fingerprint'] != digest):
                record = {'fingerprint': digest, 'revision': (record['revision'] if record else 0) + 1,
                          'asOf': as_of}
                tx.put('projection_versions', identity, record)
            elif not older and record is not None and as_of is not None and record.get('asOf') != as_of:
                record['asOf'] = as_of
                tx.put('projection_versions', identity, record)
            if not older and record is not None and observation is not None:
                record['observation'] = observation
                tx.put('projection_versions', identity, record)
            if not older and component == 'runtime' and record and publish_current:
                tx.put('projection_current', source['sourceId'], {'projectionEpoch': binding['projectionEpoch'],
                       'revision': record['revision']})
        if record is None:
            record = {'revision': None, 'asOf': None}
        return {'status': status, 'freshness': 'fresh' if status in {'available', 'partial'} else
                'stale' if unavailable and record['revision'] is not None else 'unknown',
                'revision': record['revision'], 'asOf': record['asOf'], 'errorCode': error,
                'truncated': truncated, 'gaps': gaps or [], 'target': target}

    def observe(self, source):
        with self.store.transaction() as tx:
            record = tx.get('projection_observations', source['sourceId']) or {'issued': 0}
            record['issued'] += 1
            tx.put('projection_observations', source['sourceId'], record)
            return record['issued']

    def current_version(self, source, binding):
        with self.store.transaction() as tx:
            current = tx.get('projection_current', source['sourceId'])
        return {**self.not_requested(), 'revision': current.get('revision') if current and
                current.get('projectionEpoch') == binding['projectionEpoch'] else None}

    @staticmethod
    def authority_stamp(reader):
        paths = ['.autonomous-company/product-state.json', '.auto-loop-state', '.auto-loop.pid',
                 'logs/usage.jsonl', 'logs/usage.jsonl.pending']
        values = []
        for relative in paths:
            try:
                info = reader.safe_path(relative).stat()
                values.append((relative, info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns))
            except FileNotFoundError:
                values.append((relative, None))
        return values

    def verify_observation(self, reader, index):
        meta = HarnessStore(reader.root).read_metadata()
        if (any(meta.get(key) != index.get(key) for key in ('projectionEpoch', 'snapshotRevision')) or
                self.authority_stamp(reader) != reader.projection_authority):
            raise CenterError('PROJECTION_RETRY', 'Authority changed while collecting the projection.', 503)

    def ledger(self, reader, source):
        path = reader.root / 'logs/usage.jsonl'
        try:
            info = path.stat()
            signature = (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size,
                         reader.scope, fingerprint(reader.identity_state()))
        except OSError:
            signature = None
        with self.lock:
            cached = self.ledger_cache.get(source['sourceId'])
            if cached and cached[0] == signature:
                return deepcopy(cached[1])
            result = reader.ledger(include_attempts=True)
            self.ledger_cache[source['sourceId']] = (signature, deepcopy(result))
            return result

    def context(self, entry_id, query, *, usage=False):
        entry, source, reader = self.catalog.resolve_source(entry_id, query.get('sourceId'))
        reader.projection_version = 2
        reader.projection_observation = self.observe(source)
        reader.projection_authority = self.authority_stamp(reader)
        store = HarnessStore(reader.root)
        try:
            index = store.snapshot(compact=True, catalog=not usage)
        except Exception as error:
            raise CenterError('HARNESS_UNAVAILABLE', 'Authoritative Harness records are unavailable.', 503) from error
        scope = {'productId': source.get('productId'), 'explorationId': reader.scope.exploration_id,
                 'includeExploration': True}
        index['cycles'] = [row for row in index['cycles'] if _in_scope(row, scope)]
        reader.projection_index = index
        binding = self.binding(source, reader, index.get('projectionEpoch'))
        for key, actual in (('sourceBindingVersion', str(binding['sourceBindingVersion'])), ('projectionEpoch', binding['projectionEpoch'])):
            if query.get(key) is not None and str(query[key]) != actual:
                raise CenterError('SOURCE_BINDING_CHANGED' if key == 'sourceBindingVersion' else 'PROJECTION_EPOCH_CHANGED',
                                  'The resource belongs to a different source binding or projection.', 409)
        return entry, source, reader, store, index, scope, binding

    def identity(self, entry, source, binding):
        return {'projectionVersion': 2, 'centerId': self.store.center_id, 'entryId': entry['entryId'],
                'sourceId': source['sourceId'], 'sourceRevision': source.get('sourceRevision'),
                'sourceBindingVersion': binding['sourceBindingVersion'], 'productId': source.get('productId'),
                'explorationId': source.get('explorationId'), 'projectionEpoch': binding['projectionEpoch'],
                'generatedAt': now()}

    def inventory(self, reader, index, records):
        legacy = [record for record in records if record.get('record_role') != 'harness_attempt']
        rows = {record['cycle_id']: {'id': record['cycle_id'], 'startedAt': timestamp(record.get('started_at')),
                 'endedAt': timestamp(record.get('ended_at')), 'status': record.get('status'),
                 'reservedAt': None, 'identityKind': 'legacy', 'number': record['cycle_number']} for record in legacy}
        projections = list_cycle_projections(reader.root, product_id=reader.scope.product_id or reader.scope.exploration_id,
                                             limit=None) if reader.scope.product_id or reader.scope.exploration_id else {'cycles': []}
        for row in projections['cycles']:
            prior = rows.get(row['cycleId'], {})
            rows[row['cycleId']] = {'id': row['cycleId'], 'startedAt': prior.get('startedAt') or row.get('startedAt'), 'reservedAt': row['reservedAt'],
                'sequenceNumber': row.get('sequenceNumber'), 'identityKind': row['kind']}
            rows[row['cycleId']].update(status=prior.get('status') or {'reserved': 'not_started', 'dispatching': 'startup_unconfirmed'}.get(row['state'], row['state']),
                                        endedAt=prior.get('endedAt') or row.get('endedAt'))
        for row in index['cycles']:
            rows[row['cycleId']] = {'id': row['cycleId'], 'startedAt': row['startedAt'], 'reservedAt': row['createdAt'],
                'sequenceNumber': row['sequenceNumber'], 'identityKind': 'product' if row.get('productId') else 'exploration'}
            rows[row['cycleId']].update(status=row['protocolState'], endedAt=row['endedAt'])
        result = list(rows.values())
        result.sort(key=lambda row: (row.get('sequenceNumber') or row.get('number') or 0,
                                    row.get('startedAt') or row.get('reservedAt') or '', row['id']), reverse=True)
        return result, legacy

    def page(self, inventory, query, scope_key, limit):
        boundary = query.get('before')
        with self.lock:
            expired = [token for token, row in self.cursors.items() if row['expires'] < time.monotonic()]
            for token in expired:
                self.cursors.pop(token, None)
            if boundary:
                cursor = self.cursors.get(boundary)
                if not cursor or cursor['scope'] != scope_key:
                    raise CenterError('CURSOR_EXPIRED', 'Fixed history snapshot expired; reload history.', 409)
                remaining, total, history_id = cursor['ids'], cursor['total'], cursor['historyId']
                if not set(remaining).issubset({row['id'] for row in inventory}):
                    raise CenterError('CURSOR_EXPIRED', 'Fixed history is no longer available.', 409)
            else:
                remaining, total = [row['id'] for row in inventory], len(inventory)
                history_id = fingerprint(remaining)
            selected, rest = remaining[:limit], remaining[limit:]
            token = None
            if rest:
                token = secrets.token_urlsafe(24)
                if len(self.cursors) >= 128:
                    self.cursors.pop(next(iter(self.cursors)))
                self.cursors[token] = {'scope': scope_key, 'ids': rest, 'total': total,
                                       'historyId': history_id, 'expires': time.monotonic() + 600}
            return selected, total, token, history_id

    def links(self, data, entry, source, binding, records):
        base = '/api/center/v1/entries/' + quote(entry['entryId']) + '/resources/'
        suffix = '?' + urlencode({'projectionVersion': 2, 'sourceId': source['sourceId'],
            'sourceBindingVersion': binding['sourceBindingVersion'], 'projectionEpoch': binding['projectionEpoch']})
        by_attempt = {record['cycle_id']: record for record in records}
        def evidence_url(identity):
            opaque = hashlib.sha256(identity.encode('utf-8')).hexdigest()
            key = base64.urlsafe_b64encode(identity.encode('utf-8')).decode().rstrip('=')
            return base + 'evidence-' + opaque + suffix + '&evidenceKey=' + quote(key, safe='')
        for cycle in data.get('cycles', []):
            for attempt in cycle.get('attempts', []):
                identity = attempt['attemptId']
                log_id = cycle['id'] if attempt.get('legacy') else identity
                attempt['logUrl'] = base + 'log-' + quote(log_id) + suffix
                record = by_attempt.get(log_id) or {}
                attempt['engine'] = record.get('engine') or (cycle.get('contract') or {}).get('capabilities', {}).get('adapter') or None
                attempt['model'] = record.get('model') or None
            chosen = next((attempt for attempt in cycle.get('attempts', []) if attempt['attemptId'] == cycle.get('activeAttemptId')),
                          cycle.get('attempts', [])[-1] if cycle.get('attempts') else None)
            cycle['logUrl'] = chosen.get('logUrl') if chosen else None
            cycle['logAvailable'] = bool(chosen)
            if chosen:
                cycle.update(engine=chosen.get('engine') or 'unknown', model=chosen.get('model') or 'unknown')
            for quality in cycle.get('qualityApplicability', []):
                candidates = quality.get('reviewEvidenceRefs', [])
                primary = next((ref for ref in candidates if ref.get('evidenceId') == cycle.get('primaryEvidenceId')), None)
                if primary:
                    quality['evidenceRef'] = deepcopy(primary)
                ref = quality.get('evidenceRef')
                if isinstance(ref, dict) and ref.get('evidenceId'):
                    ref['url'] = evidence_url(ref['evidenceId'])
                for ref in candidates:
                    if ref.get('evidenceId'):
                        ref['url'] = evidence_url(ref['evidenceId'])
            cycle['evidenceRefs'] = deepcopy(cycle.get('evidenceRefs', []))
            for ref in cycle['evidenceRefs']:
                if ref.get('evidenceId'):
                    ref['url'] = evidence_url(ref['evidenceId'])
        artifacts = list(data.get('artifacts', [])) + [item for cycle in data.get('cycles', []) for item in cycle.get('artifacts', [])]
        for item in artifacts:
            if item.get('kind') != 'preview' and item.get('id'):
                item['url'] = base + ('artifact-' if not item['id'].startswith('reference-') else '') + quote(item['id']) + suffix
        media = data.get('productMedia') or {}
        for item in [media.get('icon'), *((media.get('screenshot') or {}).get('latestSuccess') or {}).get('variants', [])]:
            if item and item.get('name'):
                item['href'] = base + 'media-' + quote(item['name']) + suffix

    def execution_issues(self, cycles, reader):
        """Adapt retained host receipts without changing historical authority."""
        for cycle in cycles:
            if cycle.get('harnessVersion') != 2 or cycle.get('protocolState') != 'closed' or cycle.get('outcome') != 'failed':
                continue
            attempts = cycle.get('attempts') or []
            attempt = attempts[-1] if attempts else None
            if not attempt or not attempt.get('writersStopped') or not CYCLE_ID.fullmatch(attempt.get('attemptId', '')):
                continue
            try:
                raw, truncated = reader.read('.autonomous-company/harness/' + attempt['attemptId'] + '.finish.json', 32768)
                receipt = json.loads(raw)
                if truncated or receipt.get('cycleId') != cycle['id'] or receipt.get('attemptId') != attempt['attemptId']:
                    continue
                code = str(receipt.get('error') or '').split(':', 1)[0]
                if not re.fullmatch(r'[A-Z][A-Z0-9_]{0,63}', code):
                    continue
                cycle['executionIssue'] = {'code': code, 'attemptId': attempt['attemptId'],
                    'source': 'host_finish', 'recordedAt': cycle.get('endedAt')}
            except (OSError, ValueError, TypeError, AttributeError):
                continue

    def journal(self, entry_id, query, *, record_id=None):
        entry, source, reader, store, index, scope, binding = self.context(entry_id, query)
        if query.get('component') == 'media':
            return self.media(entry, source, reader, binding)
        records, warnings = self.ledger(reader, source)
        if index.get('projectionEpoch') is None and any(record.get('record_role') == 'harness_attempt' for record in records):
            raise CenterError('HARNESS_UNAVAILABLE', 'Harness metering exists but its authoritative records are missing.', 503)
        inventory, legacy = self.inventory(reader, index, records)
        current_inventory = inventory
        if query.get('section') == 'exploration':
            inventory = [row for row in inventory if row.get('identityKind') == 'exploration']
        scope_key = fingerprint([entry_id, source['sourceId'], binding, query.get('section')])
        if record_id:
            if record_id not in {row['id'] for row in inventory}:
                raise CenterError('RECORD_NOT_FOUND', 'Record does not belong to this identity.', 404)
            ids, total, token, history_id = [record_id], len(inventory), None, record_id
        else:
            from center_catalog import bounded_int
            ids, total, token, history_id = self.page(inventory, query, scope_key, bounded_int(query.get('limit'), 20, 100))
        if query.get('component') not in {None, 'media'}:
            raise CenterError('INVALID_INPUT', 'Unknown journal component.')
        # Only selected rows receive legacy sidecars; optional media never enters
        # the five-second core path. Full Harness event payloads are detail-only.
        selected_index = store.snapshot(ids, compact=not bool(record_id))
        if (selected_index.get('projectionEpoch') != index.get('projectionEpoch') or
                selected_index.get('snapshotRevision') != index.get('snapshotRevision')):
            raise CenterError('PROJECTION_RETRY', 'Harness records changed during reading; retry.', 503)
        data, observation = self.catalog._snapshot(source, reader, cycle_ids=set(ids), include_media=False,
            include_events=bool(record_id), include_documents=bool(record_id),
            ledger_records=(legacy, list(warnings)), detail_cycle_id=record_id)
        data['cycles'] = project_cycles(data['cycles'], selected_index, scope)
        self.execution_issues(data['cycles'], reader)
        usage_observed_at = now()
        for cycle in data['cycles']:
            if cycle.get('harnessVersion'):
                cycle['active'] = bool(data['runtime'].get('active') and data['runtime'].get('currentCycleId') == cycle['id'])
                if data['runtime'].get('currentCycleId') == cycle['id']:
                    timing = cycle.get('time') or {}
                    data['runtime'].update(elapsedReliable=timing.get('reliability') == 'reliable',
                        elapsedSeconds=timing.get('executionSeconds') if timing.get('reliability') == 'reliable' else None)
        data['cycles'].sort(key=lambda row: ids.index(row['id']))
        data['readonlyObservation'] = observation
        current_id = data['runtime'].get('currentCycleId') or (current_inventory[0]['id'] if current_inventory else None)
        data.update(self.identity(entry, source, binding))
        data['harnessCapability'] = source.get('capabilities', {}).get('harness') or {
            'supported': bool(index.get('projectionEpoch')), 'enabled': bool(index.get('projectionEpoch')),
            'reason': None if index.get('projectionEpoch') else 'not_selected'}
        protocol_ids = {row['cycleId'] for row in index['cycles']}
        legacy_core = []
        for item in inventory:
            if item['id'] in protocol_ids:
                continue
            actual = bool(data['runtime'].get('active') and data['runtime'].get('currentCycleId') == item['id'])
            legacy_core.append(core_cycle(legacy_cycle({**item, 'active': actual,
                'status': 'running' if actual else item.get('status', 'unknown')})))
        protocol_core = project_cycles([], index, scope)
        for row in protocol_core:
            row['active'] = bool(data['runtime'].get('active') and data['runtime'].get('currentCycleId') == row['id'])
        core_facts = {'currentCycleId': current_id,
                      'cycles': [core_cycle(row) for row in protocol_core],
                      'legacyCycles': legacy_core,
                      'runtime': {key: data['runtime'].get(key) for key in ('state', 'processState', 'currentCycleId', 'active', 'pid', 'available', 'pauseReason', 'engine', 'model', 'reasoning')}}
        self.verify_observation(reader, index)
        version = partial(self.version, source, binding, observation=reader.projection_observation)
        core_read = not record_id and not query.get('before') and not query.get('section')
        runtime = version('runtime', core_facts,
            status='available' if data['runtime'].get('available') else 'unavailable',
            as_of=(observation or {}).get('observedAt'), error=None if data['runtime'].get('available') else 'CONTROL_UNCONFIRMED',
            publish_current=True) if core_read else self.current_version(source, binding)
        data['snapshotRevision'] = runtime['revision']
        reports = [{'cycleId': row['id'], 'report': row.get('workReport'), 'status': row.get('workReportStatus')} for row in data['cycles']]
        report_time = max((row['report'].get('recorded_at') for row in reports if row['report'] and row['report'].get('recorded_at')), default=None)
        component_target = {'cycleIds': ids}
        report = version('report', reports, as_of=report_time, target=component_target) if record_id or all(row.get('harnessVersion') for row in data['cycles']) else self.not_requested()
        check_rows = [check for row in data['cycles'] for check in row.get('checks', [])]
        collection = data.get('artifactCollection') or {}
        checks_supported = bool(reader.scope.project or reader.scope.kind == 'exploration')
        checks_unavailable = collection.get('status') == 'unavailable' and checks_supported
        checks = version('checks', None if checks_unavailable else check_rows,
            status='unavailable' if checks_unavailable else 'partial' if collection.get('status') == 'partial' else
                   'available' if check_rows else 'missing' if checks_supported else 'not_applicable',
            as_of=max((item.get('recordedAt') for item in check_rows if item.get('recordedAt')), default=None),
            truncated=bool(collection.get('truncated')), target=component_target)
        history = version('history', [[row['id'], row.get('status'), row.get('activeAttemptId')] for row in data['cycles']],
                               as_of=None, target={'historyId': history_id, 'cycleIds': ids})
        event_health = [row.get('eventsHealth') for row in data['cycles'] if row.get('eventsHealth')]
        events = version('events', [row.get('events', []) for row in data['cycles']],
            status='partial' if any(item.get('status') == 'partial' for item in event_health) else 'available',
            truncated=any(item.get('truncated') for item in event_health),
            gaps=[gap for item in event_health for gap in item.get('gaps', [])], target=component_target) if record_id else self.not_requested()
        data['partitions'] = {'runtime': runtime, 'report': report, 'checks': checks, 'history': history, 'events': events,
            'media': {'status': 'missing', 'freshness': 'unknown', 'revision': None, 'asOf': None, 'errorCode': 'NOT_REQUESTED'},
            'usage': {'status': 'missing', 'freshness': 'unknown', 'revision': None, 'asOf': None, 'errorCode': 'NOT_REQUESTED'}}
        for cycle in data['cycles']:
            target = {'cycleId': cycle['id'], 'attemptId': cycle.get('activeAttemptId') or
                      (cycle.get('attempts') or [{}])[-1].get('attemptId')}
            cycle_report = cycle.get('workReport')
            health = cycle.get('eventsHealth') or {}
            cycle['partitions'] = {
                'usage': version('usage', {**{key: cycle.get(key) for key in ('usage', 'costUsd', 'costStatus')},
                    'attempts': [{'attemptId': attempt.get('attemptId'), 'usage': attempt.get('usage')}
                                 for attempt in cycle.get('attempts', [])]}, target=target,
                    status='available' if (cycle.get('usage') or {}).get('status') in {'available', 'reported'} and
                        cycle.get('costStatus') == 'reported' else 'partial', as_of=usage_observed_at),
                'report': version('report', [cycle_report, cycle.get('workReportStatus'), cycle.get('summary'), cycle.get('reportObservedAt')], target=target,
                    status='available' if cycle.get('workReportStatus') == 'valid' or cycle.get('reportObservedAt') else 'missing',
                    as_of=cycle_report.get('recorded_at') if cycle_report else cycle.get('reportObservedAt')) if record_id or cycle.get('harnessVersion') else self.not_requested(),
                'documents': version('documents', None if checks_unavailable else [item for item in cycle.get('artifacts', []) if item.get('kind') == 'document'], target=target,
                    status='unavailable' if checks_unavailable else 'partial' if collection.get('status') == 'partial' else 'available',
                    error='DOCUMENTS_UNAVAILABLE' if checks_unavailable else None, truncated=bool(collection.get('truncated')),
                    as_of=max((item.get('recordedAt') for item in cycle.get('artifacts', []) if item.get('kind') == 'document' and item.get('recordedAt')), default=None)) if record_id else self.not_requested(),
                'checks': version('checks', cycle.get('checks', []), target=target,
                    status='unavailable' if (cycle.get('executionIssue') or {}).get('code') == 'COLLECTION_UNCONFIRMED' else
                           'partial' if collection.get('status') == 'partial' else 'available' if cycle.get('checks') else 'missing',
                    error='COLLECTION_UNCONFIRMED' if (cycle.get('executionIssue') or {}).get('code') == 'COLLECTION_UNCONFIRMED' else None) if not checks_unavailable else {
                        **self.not_requested(), 'status': 'unavailable', 'errorCode': 'CHECKS_UNAVAILABLE'},
                'events': version('events', [cycle.get('events', []), health], target=target,
                    status=health.get('status') if health.get('status') in {'available', 'partial', 'missing', 'invalid', 'unavailable'} else 'available' if cycle.get('events') else 'missing',
                    as_of=health.get('asOf'), truncated=bool(health.get('truncated')), gaps=health.get('gaps', [])) if record_id else self.not_requested(health)}
        self.links(data, entry, source, binding, records)
        data.update(currentCycleId=current_id, currentCycle=next((row for row in data['cycles'] if row['id'] == current_id), None),
                    nextBefore=token, hasMore=bool(token), total=total,
                    entry=self.catalog.get_entry(entry_id, source['sourceId']))
        if record_id:
            return {**data['cycles'][0], **self.identity(entry, source, binding), 'snapshotRevision': runtime['revision'],
                    'partitions': {**data['partitions'], **data['cycles'][0]['partitions']}, 'currentCycleId': current_id}
        return data

    def media(self, entry, source, reader, binding):
        key = fingerprint([source['sourceId'], binding['sourceBindingVersion'], binding['projectionEpoch']])
        try:
            data, _ = self.catalog._snapshot(source, reader, cycle_ids=set(), include_media=True,
                                             include_events=False, ledger_records=([], []))
            self.links(data, entry, source, binding, [])
            facts = {'artifacts': data['artifacts'], 'productMedia': data['productMedia']}
            if 'product_media_unavailable' in data['warnings']:
                raise ValueError('media unavailable')
            dates = [item.get('recordedAt') for item in facts['artifacts']]
            dates.append((((facts.get('productMedia') or {}).get('screenshot') or {}).get('latestSuccess') or {}).get('capturedAt'))
            self.verify_observation(reader, reader.projection_index)
            partition = self.version(source, binding, 'media', facts, as_of=max((value for value in dates if timestamp(value)), default=None),
                                     observation=reader.projection_observation)
            with self.store.transaction() as tx:
                cached = tx.get('projection_media', key)
                newer_cache = cached and cached.get('observation', 0) > reader.projection_observation
                if partition.get('errorCode') == 'STALE_OBSERVATION' or newer_cache and cached.get('facts') != facts:
                    facts = (cached or {}).get('facts', {'artifacts': [], 'productMedia': None})
                    partition = {**partition, 'status': 'unavailable', 'freshness': 'stale', 'revision': None,
                                 'errorCode': 'STALE_OBSERVATION'}
                elif not newer_cache:
                    tx.put('projection_media', key, {'observation': reader.projection_observation, 'facts': facts})
        except (OSError, ValueError, TypeError, KeyError):
            with self.store.transaction() as tx:
                cached = tx.get('projection_media', key) or {}
                facts = cached.get('facts', {'artifacts': [], 'productMedia': None})
            partition = self.version(source, binding, 'media', None, status='unavailable', error='MEDIA_UNAVAILABLE',
                                     observation=reader.projection_observation)
        with self.store.transaction() as tx:
            core = tx.get('projection_current', source['sourceId'])
        return {**self.identity(entry, source, binding), **facts, 'snapshotRevision':
                core.get('revision') if core and core.get('projectionEpoch') == binding['projectionEpoch'] else None,
                'partitions': {'media': partition}}

    @staticmethod
    def not_requested(health=None):
        health = health or {}
        return {'status': 'missing', 'freshness': 'unknown', 'revision': None, 'asOf': health.get('asOf'),
                'errorCode': 'NOT_REQUESTED', 'truncated': bool(health.get('truncated')), 'gaps': health.get('gaps', [])}

    def usage(self, entry_id, query):
        entry, source, reader, store, index, scope, binding = self.context(entry_id, query, usage=True)
        records, warnings = self.ledger(reader, source)
        if index.get('projectionEpoch') is None and any(record.get('record_role') == 'harness_attempt' for record in records):
            raise CenterError('HARNESS_UNAVAILABLE', 'Harness metering exists but its authoritative records are missing.', 503)
        by_attempt = {row['cycle_id']: row for row in records}
        units, mirrored = [], set()
        state = reader.identity_state()
        projections = {row['cycleId']: row for row in list_cycle_projections(reader.root, limit=None)['cycles']}
        def name(value):
            return value[:200] if isinstance(value, str) and value and value not in {'unknown', 'config-default', 'unavailable'} else None
        def cost(value):
            return value if type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 2**53 - 1 else None
        include = query.get('includeExploration') in {True, 'true', '1'}
        for cycle in index['cycles']:
            if source.get('productId') and not cycle.get('productId') and not include:
                continue
            for ordinal, attempt in enumerate(cycle['attempts'], 1):
                record = by_attempt.get(attempt['attemptId'], {})
                mirrored.add(attempt['attemptId'])
                units.append({'engine': name(record.get('engine')) or name(cycle['contract'].get('capabilities', {}).get('adapter')),
                              'model': name(record.get('model')), 'usage': attempt['usage'], 'cycleId': cycle['cycleId'],
                              'attemptId': attempt['attemptId'], 'attemptNumber': ordinal, 'sequenceNumber': cycle['sequenceNumber'],
                              'date': record.get('ended_at') or attempt.get('endedAt') or attempt.get('startedAt')})
        for record in records:
            if record['cycle_id'] in mirrored:
                continue
            # All actual attempts charge once. The authoritative DB above wins
            # over its ledger mirror; orphan ledger attempts retain real usage.
            logical = record.get('logical_cycle_id') or record['cycle_id']
            if not include and source.get('productId'):
                identity = state['cycles'].get(logical)
                if identity and identity['identityId'] == source.get('explorationId'):
                    continue
            usage = record.get('usage') or {}
            from journal_data import token_count
            units.append({'engine': name(record.get('engine')), 'model': name(record.get('model')), 'cycleId': logical,
                'attemptId': record.get('attempt_id') if record.get('record_role') == 'harness_attempt' else 'legacy:' + logical,
                'attemptNumber': 1 if record.get('record_role') != 'harness_attempt' else None,
                'sequenceNumber': projections.get(logical, {}).get('sequenceNumber') or record['cycle_number'],
                'date': record.get('ended_at') or record.get('started_at'),
                'usage': {'inputTokens': token_count(usage.get('input_tokens')), 'outputTokens': token_count(usage.get('output_tokens')),
                          'totalTokens': token_count(usage.get('total_tokens')), 'cost': cost(record.get('cost_usd')),
                          'inputTokensComplete': False, 'outputTokensComplete': False, 'totalTokensComplete': False, 'costComplete': False}})
        period = query.get('period', 'day' if query.get('date') else 'all')
        if period not in {'all', 'day', 'week'}:
            raise CenterError('INVALID_INPUT', 'Unsupported usage period.')
        start = end = None
        unknown_time = 0
        if period != 'all':
            try:
                target = date.fromisoformat(query['date']) if query.get('date') else datetime.now().date()
            except ValueError as error:
                raise CenterError('INVALID_INPUT', 'Invalid usage date.') from error
            start = target if period == 'day' else target - timedelta(days=target.weekday())
            end = start if period == 'day' else start + timedelta(days=6)
            selected = []
            for unit in units:
                value = timestamp(unit['date'])
                if not value:
                    unknown_time += 1
                elif start <= datetime.fromisoformat(value).astimezone().date() <= end:
                    selected.append(unit)
            units = selected
        def aggregate(rows):
            usage = {}
            for key in ('cost', 'inputTokens', 'outputTokens', 'totalTokens'):
                known = [row['usage'].get(key) for row in rows if type(row['usage'].get(key)) in (int, float)]
                usage[key] = sum(known) if known else None
                usage[key + 'Complete'] = bool(rows) and all(row['usage'].get(key + 'Complete') is True for row in rows)
            usage['status'] = 'available' if all(usage[key + 'Complete'] for key in ('cost', 'inputTokens', 'outputTokens', 'totalTokens')) else 'partial'
            recorded = sum(row['usage'].get('totalTokens') is not None for row in rows)
            return {'usage': usage, 'costUsd': usage['cost'], 'costKnown': sum(row['usage'].get('cost') is not None for row in rows),
                    'count': len(rows), 'recorded': recorded, 'unknown': len(rows) - recorded}
        def group_key(unit):
            return unit['engine'], unit['model'], unit['attemptId'] if not unit['engine'] or not unit['model'] else None
        keys = sorted({group_key(unit) for unit in units}, key=lambda key: tuple(value or '' for value in key))
        groups = []
        for engine, model, individual in keys:
            selected = [unit for unit in units if group_key(unit) == (engine, model, individual)]
            identity = {key: selected[0].get(key) for key in ('cycleId', 'attemptId', 'attemptNumber', 'sequenceNumber')} if individual else {}
            groups.append({'engine': engine, 'model': model, **identity, **aggregate(selected)})
        dates = sorted(unit['date'] for unit in units if timestamp(unit['date']))
        result = {**self.identity(entry, source, binding), **aggregate(units), 'groups': groups, 'period': period,
                  'startDate': start.isoformat() if start else None, 'endDate': end.isoformat() if end else None,
                  'unknownTime': unknown_time, 'warnings': warnings, 'truncated': any('truncated' in value for value in warnings),
                  'coverageStart': dates[0] if dates else None, 'coverageEnd': dates[-1] if dates else None,
                  'conflicting': sum(int(value.rsplit(':', 1)[1]) for value in warnings if value.startswith('ledger_conflicting_ids:'))}
        facts = {key: value for key, value in result.items() if key not in {'generatedAt', 'sourceRevision'}}
        partial = bool(warnings or unknown_time or result['usage']['status'] == 'partial' or
                       any(not group.get('engine') or not group.get('model') for group in groups))
        self.verify_observation(reader, index)
        usage = self.version(source, binding, 'usage', facts, status='partial' if partial else 'available',
                             as_of=max((unit['date'] for unit in units if unit['date']), default=None),
                             truncated=result['truncated'], target=[period, result['startDate'], result['endDate'], include],
                             observation=reader.projection_observation)
        with self.store.transaction() as tx:
            core = tx.get('projection_current', source['sourceId'])
        result.update(snapshotRevision=core.get('revision') if core and core.get('projectionEpoch') == binding['projectionEpoch'] else None,
                      partitions={'usage': usage})
        return result

    def resource(self, entry_id, resource_id, query):
        if query.get('sourceBindingVersion') is None or not query.get('projectionEpoch'):
            raise CenterError('SOURCE_BINDING_REQUIRED', 'Versioned resource requires its source binding.', 409)
        entry, source, reader, store, index, scope, binding = self.context(entry_id, query)
        if resource_id.startswith('evidence-'):
            try:
                key = query.get('evidenceKey', '')
                if not isinstance(key, str) or len(key) > 2048:
                    raise ValueError()
                identity = base64.b64decode(key + '=' * (-len(key) % 4), altchars=b'-_', validate=True).decode('utf-8')
                if not 1 <= len(identity) <= 256 or hashlib.sha256(identity.encode('utf-8')).hexdigest() != resource_id[len('evidence-'):]:
                    raise ValueError()
            except (ValueError, UnicodeError) as error:
                raise CenterError('RESOURCE_NOT_FOUND', 'Evidence reference is invalid.', 404) from error
            evidence = store.read_evidence(identity)
            if not evidence or evidence['cycleId'] not in {cycle['cycleId'] for cycle in index['cycles']}:
                raise CenterError('RESOURCE_NOT_FOUND', 'Evidence does not belong to this identity.', 404)
            raw = base64.b64decode(evidence['content']) if evidence.get('contentEncoding') == 'base64' else evidence['content'].encode()
            if hashlib.sha256(raw).hexdigest() != evidence['sha256']:
                raise CenterError('EVIDENCE_INVALID', 'Evidence version could not be verified.', 409)
            return raw, evidence.get('mediaType') or 'application/octet-stream'
        if resource_id.startswith('log-'):
            identity = resource_id[4:]
            allowed = {attempt['attemptId'] for cycle in index['cycles'] for attempt in cycle['attempts']}
            if identity in allowed:
                return self.catalog._read_log(source, reader, identity)
        return self.catalog.resource(entry_id, resource_id, source['sourceId'])
