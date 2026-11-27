"""Scoped v2 reads, independent versions and immutable history; no model calls."""
import hashlib
import http.client
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'dashboard'), str(ROOT / 'scripts/core')]
from center_catalog import CenterCatalog
from center_store import CenterStore, CenterError
from company_harness import HarnessStore
from journal_data import JournalSource
import product_identity as products


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'source'
        (self.root / 'projects/one').mkdir(parents=True)
        self.center_path = self.base / 'center'
        self.store = CenterStore(self.center_path)
        self.addCleanup(self.store.close)
        self.catalog = CenterCatalog(self.store)
        self.harness = HarnessStore(self.root, create=True)
        self.number = 0

    def cycle(self, *, close=True, report=True, project='projects/one', engine='codex', tokens=5, evidence_id=None, ownership=None):
        self.number += 1
        identity = products.reserve_cycle(self.root, project, 'reserve-' + str(self.number), self.number, engine, 'model-' + engine)
        cycle_id = identity['cycleId']
        self.harness.create_cycle({'cycleId': cycle_id, 'productId': identity['productId'], 'explorationId': identity.get('explorationId'),
            'sequenceNumber': identity['sequenceNumber'], 'objective': 'One bounded result ' + str(self.number), 'workKind': 'research',
            'project': project, 'capabilities': {'adapter': engine}})
        attempt = self.harness.begin_attempt(cycle_id, 'attempt-' + str(self.number), ownership or {'dispatchId': 'owned'})['context']
        if report:
            self.harness.publish_progress(attempt, 'report-1', {'reportRevision': 1, 'title': 'Actual result ' + str(self.number),
                'summary': 'A real stored report', 'reportedPhase': 'review'})
        self.harness.record_usage(cycle_id, attempt['attemptId'], {'callId': 'call-' + str(self.number), 'coverage': 'unknown',
            'cost': 0.5, 'inputTokens': tokens - 1, 'outputTokens': 1, 'source': {'type': 'ledger_mirror'}})
        log = self.root / 'logs' / (attempt['attemptId'] + '.log')
        log.parent.mkdir(exist_ok=True)
        log.write_text('private attempt ' + str(self.number))
        ledger = {'schema_version': 1, 'kind': 'cycle_usage', 'cycle_id': attempt['attemptId'], 'cycle_number': self.number,
            'record_role': 'harness_attempt', 'logical_cycle_id': cycle_id, 'attempt_id': attempt['attemptId'],
            'project': project, 'started_at': '2026-10-22T01:00:00+00:00', 'ended_at': '2026-10-22T01:01:00+00:00',
            'engine': engine, 'model': 'model-' + engine, 'status': 'completed', 'cost_usd': 0.5,
            'usage': {'input_tokens': tokens - 1, 'output_tokens': 1, 'total_tokens': tokens}}
        with (self.root / 'logs/usage.jsonl').open('a') as target:
            target.write(json.dumps(ledger) + '\n')
        if close:
            evidence = self.harness.bind_evidence(cycle_id, evidence_id or 'evidence-' + str(self.number), 'Immutable version ' + str(self.number))
            ref = {'evidenceId': evidence['evidenceId'], 'sha256': evidence['sha256']}
            self.harness.submit(attempt, 'submission', {'result': 'completed', 'unfinishedItems': [], 'evidenceRefs': [ref]})
            self.harness.finish_attempt(attempt, {'outcome': 'completed', 'exitCode': 0,
                'eventsHealth': {'status': 'partial', 'truncated': True, 'gaps': [{'after': 2}], 'asOf': '2026-10-22T01:01:00+00:00'}},
                writers_stopped=True, observation='owned stopped tree')
            self.harness.close_cycle(cycle_id, 'close', outcome='completed', submission_id='submission',
                verification={'writersStopped': True, 'attemptResults': [attempt['attemptId']], 'evidenceRefs': [ref],
                              'checkedAt': '2026-10-22T01:01:00+00:00', 'submittedVersionUnchanged': True})
            products.update_cycle(self.root, cycle_id, 'completed')
        return cycle_id, attempt

    def register(self):
        candidate = self.catalog.probe({'root': str(self.root)})
        items = self.catalog.commit({'candidateId': candidate['candidateId'], 'candidateHash': candidate['candidateHash']})['items']
        item = next(item for item in items if self.catalog.get_entry(item['entryId'])['productId'] == products.get_identity(self.root, 'projects/one')['id'])
        self.entry, self.source = item['entryId'], item['sourceId']

    def legacy(self, *, status='completed', event_report=False, document=False):
        self.number += 1
        identity = products.reserve_cycle(self.root, 'projects/one', 'legacy-' + str(self.number), self.number, 'claude', 'legacy-model')
        cycle = identity['cycleId']
        products.update_cycle(self.root, cycle, 'completed')
        logs = self.root / 'logs'
        logs.mkdir(exist_ok=True)
        record = {'schema_version': 1, 'kind': 'cycle_usage', 'cycle_id': cycle, 'cycle_number': self.number,
            'project': 'projects/one', 'engine': 'claude', 'model': 'legacy-model', 'status': status,
            'started_at': '2026-10-22T01:00:00+00:00', 'ended_at': '2026-10-22T01:01:00+00:00', 'usage': {'total_tokens': 3}}
        with (logs / 'usage.jsonl').open('a') as target:
            target.write(json.dumps(record) + '\n')
        if event_report:
            from runtime_events import Recorder
            Recorder(self.root, cycle).emit('report', text='Actual interrupted result', source='agent_report')
        if document:
            from runtime_artifacts import base_record, fingerprint, save
            path = self.root / 'projects/one/result.md'
            path.write_text('Bound document version')
            artifact = base_record('projects/one', 'document')
            artifact.update(cycleId=cycle, path='projects/one/result.md', sha256=fingerprint(path))
            save(self.root, artifact)
        return cycle

    def test_old_journal_cannot_publish_newer_core_after_new_cycle_observed(self):
        self.cycle()
        self.register()
        self.read()
        rendezvous, release, result = threading.Barrier(2), threading.Event(), []
        original = self.catalog._snapshot
        def blocked(*args, **kwargs):
            value = original(*args, **kwargs)
            if threading.current_thread().name == 'stale-core':
                rendezvous.wait(5)
                release.wait(5)
            return value
        def old_read():
            try:
                result.append(self.read())
            except CenterError as error:
                result.append(error.code)
        with patch.object(self.catalog, '_snapshot', side_effect=blocked):
            thread = threading.Thread(target=old_read, name='stale-core')
            thread.start()
            try:
                rendezvous.wait(5)
                latest, _ = self.cycle()
                fresh = self.read()
            finally:
                release.set()
                thread.join(5)
        self.assertEqual(result, ['PROJECTION_RETRY'])
        again = self.read()
        self.assertEqual(again['currentCycleId'], latest)
        self.assertEqual(again['snapshotRevision'], fresh['snapshotRevision'])
        with self.store.transaction() as tx:
            before = tx.get('projection_current', self.source)
        self.catalog.record(self.entry, latest, self.source, query=self.query(again))
        with self.store.transaction() as tx:
            self.assertEqual(tx.get('projection_current', self.source), before)

    def test_host_collection_receipt_is_scoped_and_does_not_expose_raw_detail(self):
        cycle_id, attempt = self.cycle(close=False)
        self.harness.finish_attempt(attempt, {'outcome': 'failed', 'exitCode': 78}, writers_stopped=True, observation='stopped')
        self.harness.close_cycle(cycle_id, 'close', outcome='failed', verification={
            'writersStopped': True, 'attemptResults': [attempt['attemptId']], 'evidenceRefs': [], 'checkedAt': '2026-10-23T07:34:14+08:00'})
        products.update_cycle(self.root, cycle_id, 'failed')
        folder = self.root / '.autonomous-company/harness'
        folder.mkdir()
        path = folder / (attempt['attemptId'] + '.finish.json')
        receipt = {'cycleId': cycle_id, 'attemptId': attempt['attemptId'], 'error': 'COLLECTION_UNCONFIRMED: private host detail'}
        self.register()
        before = self.read()
        path.write_text(json.dumps(receipt))
        after = self.read()
        self.assertGreater(after['snapshotRevision'], before['snapshotRevision'])
        self.assertGreater(after['cycles'][0]['partitions']['checks']['revision'], before['cycles'][0]['partitions']['checks']['revision'])
        row = self.read()['cycles'][0]
        self.assertEqual(row['executionIssue']['code'], 'COLLECTION_UNCONFIRMED')
        self.assertNotIn('private host detail', json.dumps(row))
        self.assertEqual(row['partitions']['checks']['status'], 'unavailable')
        receipt['cycleId'] = 'another-cycle'
        path.write_text(json.dumps(receipt))
        self.assertNotIn('executionIssue', self.read()['cycles'][0])

    def test_slow_media_is_independent_and_old_component_cannot_replace_newer_facts(self):
        self.cycle()
        self.register()
        self.read()
        control_revision = self.store.revision
        rendezvous, release, result = threading.Barrier(2), threading.Event(), []
        original = self.catalog._snapshot
        def blocked(*args, **kwargs):
            value, observed = original(*args, **kwargs)
            if kwargs.get('include_media'):
                old = threading.current_thread().name == 'stale-media'
                value['productMedia'] = {'observedVersion': 'old' if old else 'new'}
                if old:
                    rendezvous.wait(5)
                    release.wait(5)
            return value, observed
        def old_read():
            try:
                result.append(self.read(component='media'))
            except CenterError as error:
                result.append(error.code)
        with patch.object(self.catalog, '_snapshot', side_effect=blocked):
            thread = threading.Thread(target=old_read, name='stale-media')
            thread.start()
            try:
                rendezvous.wait(5)
                self.assertEqual(self.read()['currentCycleId'], self.read()['currentCycleId'])
                fresh = self.read(component='media')
            finally:
                release.set()
                thread.join(5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['partitions']['media']['errorCode'], 'STALE_OBSERVATION')
        self.assertEqual(result[0]['partitions']['media']['status'], 'unavailable')
        self.assertIsNone(result[0]['partitions']['media']['revision'])
        with patch('journal_data.media_projection', side_effect=ValueError('optional offline')):
            cached = self.read(component='media')
        self.assertEqual(cached['productMedia'], fresh['productMedia'])
        self.assertEqual(cached['partitions']['media']['revision'], fresh['partitions']['media']['revision'])
        self.assertEqual(self.store.revision, control_revision)

    def test_older_core_observation_with_same_historical_report_still_returns_new_current(self):
        first, _ = self.cycle()
        self.register()
        baseline = self.read()
        latest, _ = self.cycle()
        rendezvous, release, result = threading.Barrier(2), threading.Event(), []
        original = self.catalog._snapshot
        def blocked(*args, **kwargs):
            value = original(*args, **kwargs)
            if threading.current_thread().name == 'valid-core':
                rendezvous.wait(5)
                release.wait(5)
            return value
        def current_read():
            try:
                result.append(self.read())
            except CenterError as error:
                result.append(error.code)
        with patch.object(self.catalog, '_snapshot', side_effect=blocked):
            thread = threading.Thread(target=current_read, name='valid-core')
            thread.start()
            try:
                rendezvous.wait(5)
                historical = self.catalog.record(self.entry, first, self.source, query=self.query(baseline))
            finally:
                release.set()
                thread.join(5)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)
        self.assertEqual(result[0]['currentCycleId'], latest)
        previous = next(row for row in result[0]['cycles'] if row['id'] == first)
        self.assertEqual(previous['partitions']['report']['revision'], historical['partitions']['report']['revision'])
        self.assertIsNone(previous['partitions']['report']['errorCode'])

    def test_conflicting_optional_report_degrades_locally_without_losing_core_or_new_version(self):
        from runtime_events import Recorder
        cycle = self.legacy(status='interrupted', event_report=True)
        self.register()
        core = self.read()
        rendezvous, release, result = threading.Barrier(2), threading.Event(), []
        original = self.catalog._snapshot
        def blocked(*args, **kwargs):
            value = original(*args, **kwargs)
            if threading.current_thread().name == 'stale-report':
                rendezvous.wait(5)
                release.wait(5)
            return value
        def old_read():
            try:
                result.append(self.catalog.record(self.entry, cycle, self.source, query=self.query(core)))
            except CenterError as error:
                result.append(error.code)
        with patch.object(self.catalog, '_snapshot', side_effect=blocked):
            thread = threading.Thread(target=old_read, name='stale-report')
            thread.start()
            try:
                rendezvous.wait(5)
                recorder = Recorder(self.root, cycle)
                recorder.sequence = 1
                recorder.emit('report', text='New confirmed event result', source='agent_report')
                fresh = self.catalog.record(self.entry, cycle, self.source, query=self.query(core))
            finally:
                release.set()
                thread.join(5)
        self.assertEqual(fresh['summary'], 'New confirmed event result')
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)
        stale = result[0]
        self.assertEqual(stale['currentCycleId'], cycle)
        self.assertEqual(stale['snapshotRevision'], core['snapshotRevision'])
        self.assertEqual(stale['partitions']['report']['errorCode'], 'STALE_OBSERVATION')
        self.assertEqual(stale['partitions']['report']['status'], 'unavailable')
        self.assertIsNone(stale['partitions']['report']['revision'])
        self.assertEqual(stale['partitions']['report']['lastConfirmedRevision'], fresh['partitions']['report']['revision'])
        again = self.catalog.record(self.entry, cycle, self.source, query=self.query(core))
        self.assertEqual(again['partitions']['report']['revision'], fresh['partitions']['report']['revision'])

    def test_legacy_event_report_and_document_are_lazy_and_preserve_read_versions(self):
        cycle = self.legacy(status='interrupted', event_report=True, document=True)
        self.register()
        v1 = self.catalog.journal(self.entry)
        self.assertEqual(v1['cycles'][0]['summary'], 'Actual interrupted result')
        compact = self.read()
        self.assertEqual(compact['cycles'][0]['detailStatus'], 'limited')
        self.assertIsNone(compact['cycles'][0]['partitions']['report']['revision'])
        self.assertEqual(compact['cycles'][0]['partitions']['documents']['errorCode'], 'NOT_REQUESTED')
        with patch('observability_data.preview_available', side_effect=AssertionError('optional preview')):
            detail = self.catalog.record(self.entry, cycle, self.source, query=self.query(compact))
        self.assertEqual(detail['summary'], v1['cycles'][0]['summary'])
        self.assertEqual(detail['reportObservedAt'], v1['cycles'][0]['reportObservedAt'])
        self.assertEqual(detail['detailStatus'], 'recorded')
        self.assertEqual(len(detail['artifacts']), 1)
        self.assertEqual(detail['artifacts'][0]['kind'], 'document')
        self.assertIsNotNone(detail['partitions']['documents']['revision'])
        resource = urlsplit(detail['artifacts'][0]['url'])
        query = {key: values[0] for key, values in parse_qs(resource.query).items()}
        content, _ = self.catalog.resource(self.entry, resource.path.rsplit('/', 1)[1], self.source, query=query)
        self.assertEqual(content, b'Bound document version')
        following = self.read()['cycles'][0]
        self.assertIsNone(following['partitions']['report']['revision'])
        again = self.catalog.record(self.entry, cycle, self.source, query=self.query(compact))
        self.assertEqual(again['partitions']['report']['revision'], detail['partitions']['report']['revision'])

    def test_mixed_protocol_timeline_selects_newer_legacy_in_journal_and_catalog(self):
        harness, _ = self.cycle()
        legacy = self.legacy()
        self.register()
        data = self.read()
        self.assertEqual([row['id'] for row in data['cycles']], [legacy, harness])
        self.assertEqual(data['currentCycleId'], legacy)
        self.assertEqual(self.catalog.get_entry(self.entry)['cycleNumber'], 2)
        self.assertEqual(self.catalog.get_entry(self.entry)['latestCycleStatus'], 'completed')
        detail = self.catalog.record(self.entry, harness, self.source, query=self.query(data))
        self.assertEqual(detail['currentCycleId'], legacy)

    def test_catalog_first_observation_remembers_authority_without_detail_read(self):
        self.cycle()
        self.register()
        before = self.catalog.get_entry(self.entry)
        with self.store.transaction() as tx:
            self.assertTrue(tx.get('projection_bindings', self.source)['authorityEpoch'])
        self.harness.path.unlink()
        self.catalog.refresh_source(self.source)
        after = self.catalog.get_entry(self.entry)
        self.assertEqual(after['availability'], 'conflict')
        self.assertEqual(after['latestTitle'], before['latestTitle'])
        with self.store.transaction() as tx:
            self.assertIn('HARNESS_UNAVAILABLE', tx.get('sources', self.source)['warnings'])

    def read(self, **query):
        return self.catalog.journal(self.entry, {'projectionVersion': '2', 'sourceId': self.source, **query})

    def query(self, data):
        return {'projectionVersion': '2', 'sourceId': self.source,
                'sourceBindingVersion': str(data['sourceBindingVersion']), 'projectionEpoch': data['projectionEpoch']}

    def test_core_uses_compact_index_and_does_not_probe_optional_media(self):
        cycle_id, attempt = self.cycle()
        self.register()
        original = HarnessStore.snapshot
        calls = []
        def observed(store, *args, **kwargs):
            calls.append(kwargs.get('compact', False))
            return original(store, *args, **kwargs)
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in self.root.rglob('*') if path.is_file()}
        with patch.object(HarnessStore, 'snapshot', observed), patch('journal_data.media_projection', side_effect=AssertionError('optional probe')):
            data = self.read(limit='1')
        self.assertTrue(all(calls))
        self.assertEqual(data['currentCycleId'], cycle_id)
        self.assertEqual(len(data['cycles']), 1)
        self.assertEqual(data['cycles'][0]['workReportStatus'], 'valid')
        self.assertFalse(data['cycles'][0]['workReport']['final'])
        self.assertTrue(data['cycles'][0]['workReport']['recorded_at'])
        self.assertTrue(data['cycles'][0]['eventsHealth']['truncated'])
        self.assertEqual(data['cycles'][0]['partitions']['events']['gaps'], [{'after': 2}])
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(before, after)

    def test_report_and_late_usage_update_independently_without_current_rollback(self):
        old, old_attempt = self.cycle()
        current, attempt = self.cycle(close=False, report=False)
        self.register()
        first = self.read()
        self.harness.publish_progress(attempt, 'new-report', {'reportRevision': 1, 'title': 'Current attempt',
            'summary': 'Current verified ownership', 'reportedPhase': 'planning'})
        second = self.read()
        self.assertEqual(second['sourceBindingVersion'], first['sourceBindingVersion'])
        self.assertEqual(second['snapshotRevision'], first['snapshotRevision'])
        self.assertGreater(second['cycles'][0]['partitions']['report']['revision'], first['cycles'][0]['partitions']['report']['revision'])
        self.assertEqual(second['cycles'][0]['partitions']['usage']['revision'], first['cycles'][0]['partitions']['usage']['revision'])
        self.harness.record_usage(old, old_attempt['attemptId'], {'callId': 'late', 'coverage': 'unknown', 'cost': 1,
            'inputTokens': 2, 'outputTokens': 3, 'source': {'type': 'late'}})
        third = self.read()
        self.assertEqual(third['currentCycleId'], current)
        self.assertEqual(third['snapshotRevision'], second['snapshotRevision'])
        self.assertEqual(third['cycles'][0]['partitions']['usage']['revision'], second['cycles'][0]['partitions']['usage']['revision'])
        self.assertGreater(third['cycles'][1]['partitions']['usage']['revision'], second['cycles'][1]['partitions']['usage']['revision'])
        self.assertEqual(third['cycles'][1]['partitions']['report']['revision'], second['cycles'][1]['partitions']['report']['revision'])
        usage = self.catalog.usage(self.entry, {'projectionVersion': '2'})
        self.assertEqual(usage['usage']['totalTokens'], 15)
        self.assertEqual(usage['costUsd'], 2)

    def test_late_historical_usage_has_independent_row_version_without_expanding_recent(self):
        created = [self.cycle(tokens=100) for _ in range(22)]
        self.register()
        recent = self.read(limit='20')
        historical = self.read(limit='20', before=recent['nextBefore'])
        self.assertEqual(len(recent['cycles']), 20)
        self.assertEqual(len(historical['cycles']), 2)
        old, attempt = created[0]
        original = next(row for row in historical['cycles'] if row['id'] == old)
        old_usage = original['partitions']['usage']
        self.assertEqual(old_usage['target'], {'cycleId': old, 'attemptId': attempt['attemptId']})
        self.assertEqual(old_usage['freshness'], 'fresh')
        self.assertIsNotNone(old_usage['revision'])
        self.assertIsNotNone(old_usage['asOf'])
        self.assertEqual(historical['partitions']['usage']['errorCode'], 'NOT_REQUESTED')
        self.harness.record_usage(old, attempt['attemptId'], {'callId': 'late-800', 'coverage': 'unknown',
            'cost': 8, 'inputTokens': 799, 'outputTokens': 1, 'source': {'type': 'late'}})
        following = self.read(limit='20')
        self.assertEqual(following['currentCycleId'], recent['currentCycleId'])
        self.assertEqual(following['snapshotRevision'], recent['snapshotRevision'])
        self.assertNotIn(old, {row['id'] for row in following['cycles']})
        self.assertEqual(following['partitions']['usage']['errorCode'], 'NOT_REQUESTED')
        for current, previous in zip(following['cycles'], recent['cycles']):
            self.assertEqual(current['partitions']['usage']['revision'], previous['partitions']['usage']['revision'])
        detail = self.catalog.record(self.entry, old, query=self.query(recent))
        self.assertEqual(detail['usage']['totalTokens'], 900)
        self.assertEqual(detail['costUsd'], 8.5)
        self.assertEqual(detail['costStatus'], 'partial')
        self.assertGreater(detail['partitions']['usage']['revision'], old_usage['revision'])
        self.assertEqual(detail['partitions']['usage']['target'], old_usage['target'])
        self.assertEqual(detail['partitions']['usage']['freshness'], 'fresh')
        self.assertNotEqual(detail['partitions']['usage']['asOf'], old_usage['asOf'])
        self.assertEqual(detail['partitions']['report']['revision'], original['partitions']['report']['revision'])
        self.assertEqual(self.catalog.usage(self.entry, {'projectionVersion': '2'})['usage']['totalTokens'], 3000)
        # A fixed-range history reload observes new facts without changing membership.
        reloaded = self.read(limit='20', before=recent['nextBefore'])
        self.assertEqual([row['id'] for row in reloaded['cycles']], [row['id'] for row in historical['cycles']])
        updated = next(row for row in reloaded['cycles'] if row['id'] == old)
        self.assertEqual(updated['partitions']['usage']['revision'], detail['partitions']['usage']['revision'])
        self.assertEqual(updated['usage']['totalTokens'], 900)

    def test_legacy_row_usage_is_requested_independently_of_global_usage(self):
        cycle = self.legacy()
        self.register()
        recent = self.read()
        row = recent['cycles'][0]
        partition = row['partitions']['usage']
        self.assertEqual(partition['target'], {'cycleId': cycle, 'attemptId': 'legacy:' + cycle})
        self.assertEqual(partition['status'], 'partial')
        self.assertEqual(partition['freshness'], 'fresh')
        self.assertIsNotNone(partition['revision'])
        self.assertIsNone(partition['errorCode'])
        self.assertIsNone(row['costUsd'])
        self.assertEqual(recent['partitions']['usage']['errorCode'], 'NOT_REQUESTED')
        detail = self.catalog.record(self.entry, cycle, query=self.query(recent))
        self.assertEqual(detail['partitions']['usage']['revision'], partition['revision'])
        self.assertEqual(detail['partitions']['usage']['target'], partition['target'])

    def test_usage_is_full_scope_and_mirrors_do_not_double_charge(self):
        self.cycle()
        self.cycle(engine='claude', tokens=9)
        self.cycle(tokens=11)
        self.register()
        self.assertEqual(len(self.read(limit='1')['cycles']), 1)
        usage = self.catalog.usage(self.entry, {'projectionVersion': '2'})
        self.assertEqual(usage['count'], 3)
        self.assertEqual(usage['usage']['totalTokens'], 25)
        self.assertEqual(usage['costUsd'], 1.5)
        self.assertEqual({row['engine']: row['count'] for row in usage['groups']}, {'claude': 1, 'codex': 2})
        ledger = self.root / 'logs/usage.jsonl'
        values = [json.loads(line) for line in ledger.read_text().splitlines()]
        for value in values:
            value['model'] = 'unknown'
        ledger.write_text(''.join(json.dumps(value) + '\n' for value in values))
        isolated = self.catalog.usage(self.entry, {'projectionVersion': '2'})
        self.assertEqual(len(isolated['groups']), 3)
        self.assertTrue(all(row['count'] == 1 and row['model'] is None and row['attemptId'] for row in isolated['groups']))
        self.assertEqual({row['sequenceNumber'] for row in isolated['groups']}, {1, 2, 3})

    def test_fixed_history_survives_new_cycle_and_restart_expires_only_cursor(self):
        oldest, _ = self.cycle()
        middle, _ = self.cycle()
        latest, _ = self.cycle()
        self.register()
        first = self.read(limit='1')
        token = first['nextBefore']
        new, _ = self.cycle()
        self.catalog.refresh_source(self.source)
        page = self.read(limit='1', before=token)
        self.assertEqual([row['id'] for row in page['cycles']], [middle])
        self.assertEqual(page['total'], 3)
        self.assertEqual(self.read()['currentCycleId'], new)
        self.store.close()
        self.store = CenterStore(self.center_path)
        self.addCleanup(self.store.close)
        self.catalog = CenterCatalog(self.store)
        restarted = self.read()
        self.assertEqual(restarted['projectionEpoch'], first['projectionEpoch'])
        with self.assertRaisesRegex(CenterError, 'expired'):
            self.read(before=token)

    def test_resources_bind_attempt_evidence_and_reject_replaced_source(self):
        cycle, attempt = self.cycle()
        self.register()
        data = self.read()
        row = data['cycles'][0]
        query = self.query(data)
        content, mime = self.catalog.resource(self.entry, 'log-' + attempt['attemptId'], self.source, query=query)
        self.assertEqual(content, b'private attempt 1')
        evidence_url = urlsplit(row['evidenceRefs'][0]['url'])
        evidence_query = {key: values[0] for key, values in parse_qs(evidence_url.query).items()}
        content, mime = self.catalog.resource(self.entry, evidence_url.path.rsplit('/', 1)[1], self.source, query=evidence_query)
        self.assertEqual(content, b'Immutable version 1')
        copy = self.base / 'replacement'
        shutil.copytree(self.root, copy)
        candidate = self.catalog.probe({'root': str(copy)})
        with self.store.transaction() as tx:
            source = tx.get('sources', self.source)
        self.catalog.reconnect(self.source, {'candidateId': candidate['candidateId'], 'candidateHash': candidate['candidateHash'],
            'expectedRevision': source['revision']})
        with self.assertRaises(CenterError) as caught:
            self.catalog.resource(self.entry, 'log-' + attempt['attemptId'], self.source, query=query)
        self.assertEqual(caught.exception.code, 'SOURCE_BINDING_CHANGED')
        self.assertGreater(self.read()['sourceBindingVersion'], data['sourceBindingVersion'])

    def test_arbitrary_evidence_id_is_readable_through_bound_http_resource(self):
        from center_server import CenterServer
        self.cycle(evidence_id='中文 成果/版本:一')
        self.register()
        url = self.read()['cycles'][0]['evidenceRefs'][0]['url']
        self.assertRegex(urlsplit(url).path.rsplit('/', 1)[1], r'^evidence-[a-f0-9]{64}$')
        server = CenterServer(('127.0.0.1', 0), self.store, self.catalog, Mock(), ROOT / 'dashboard')
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=5)
            connection.request('GET', url)
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b'Immutable version 1')
            connection.close()
            connection = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=5)
            connection.request('GET', url.replace('evidenceKey=', 'evidenceKey=bad'))
            response = connection.getresponse()
            self.assertEqual(response.status, 404)
            response.read()
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(5)

    def test_attempt_conflict_uses_both_logical_owners_and_degrades_coverage(self):
        cycle, attempt = self.cycle()
        self.register()
        ledger = self.root / 'logs/usage.jsonl'
        owned = json.loads(ledger.read_text())
        foreign = {**owned, 'logical_cycle_id': 'foreign-cycle', 'cost_usd': 99}
        ledger.write_text(json.dumps(foreign) + '\n' + json.dumps(owned) + '\n')
        usage = self.catalog.usage(self.entry, {'projectionVersion': '2'})
        self.assertIn('ledger_conflicting_ids:1', usage['warnings'])
        self.assertEqual(usage['conflicting'], 1)
        self.assertEqual(usage['partitions']['usage']['status'], 'partial')
        self.assertEqual(usage['count'], 1)
        self.assertEqual(usage['costUsd'], .5)

    @unittest.skipUnless(sys.platform == 'linux', 'Actual process identity runs under WSL')
    def test_harness_live_attempt_requires_execution_domain_writer_and_loop_owner(self):
        from center_readonly import ReadOnlyObserver
        from center_runner import harness_run_observation, identity
        loop = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)', str(self.root / 'scripts/core/auto-loop.sh')])
        writer = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        try:
            start = str(identity(loop.pid)['start'])
            cycle, attempt = self.cycle(close=False, ownership={'loopPid': loop.pid, 'loopProcessStart': start})
            products.update_cycle(self.root, cycle, 'dispatching')
            reservation = products.read_state(self.root)['cycles'][cycle]
            context_path = self.root / 'logs' / (cycle + '.context.json')
            context_path.write_text(json.dumps({'version': 1, 'cycleId': cycle, 'project': 'projects/one',
                'recordedAt': '2026-10-22T01:00:00+00:00', 'source': 'runtime_context'}))
            (self.root / '.auto-loop.pid').write_text(str(loop.pid))
            (self.root / '.auto-loop-state').write_text('STATUS=running\nLOOP_COUNT=1\nPRODUCT_CYCLE_ID=' + cycle +
                '\nPRODUCT_ID=' + reservation['identityId'] + '\nENGINE=codex\nMODEL=model-codex\n')
            active = self.root / '.autonomous-company/isolation' / reservation['identityId'] / 'active-run.json'
            active.parent.mkdir(parents=True)
            active.write_text(json.dumps({'pid': writer.pid, 'processStart': str(identity(writer.pid)['start']),
                'cycle': cycle, 'attemptId': attempt['attemptId']}))
            pending = json.loads((self.root / 'logs/usage.jsonl').read_text())
            (self.root / 'logs/usage.jsonl.pending').write_text(json.dumps(pending))
            self.assertEqual(harness_run_observation(self.root)['attemptId'], attempt['attemptId'])
            self.register()
            data = self.read()
            self.assertEqual(data['runtime']['currentCycleId'], cycle)
            self.assertTrue(data['runtime']['active'])
            self.assertTrue(data['cycles'][0]['active'])
            with patch('company_harness._boot', return_value='different-boot'):
                unknown = self.read()
            self.assertFalse(unknown['runtime']['elapsedReliable'])
            self.assertIsNone(unknown['runtime']['elapsedSeconds'])
            writer.terminate()
            writer.wait()
            self.assertIsNone(harness_run_observation(self.root))
            self.catalog.readonly_observer = ReadOnlyObserver()
            stopped = self.read()
            self.assertFalse(stopped['runtime']['active'])
            self.assertFalse(stopped['cycles'][0]['active'])
            self.assertEqual(stopped['cycles'][0]['protocolState'], 'executing')
            self.catalog.refresh_source(self.source)
            entry = self.catalog.get_entry(self.entry)
            self.assertEqual(entry['latestCycleStatus'], 'unknown')
            self.assertEqual(entry['latestProtocolState'], 'executing')
            self.assertFalse(entry['latestCycleActiveConfirmed'])
        finally:
            for child in (writer, loop):
                if child.poll() is None:
                    child.terminate()
                child.wait()

    def test_media_failure_is_local_and_does_not_mutate_core_version(self):
        self.cycle()
        self.register()
        first = self.read()
        with patch('journal_data.media_projection', side_effect=ValueError('optional failed')):
            media = self.read(component='media')
        self.assertNotIn('currentCycleId', media)
        self.assertIn(media['partitions']['media']['status'], {'partial', 'unavailable'})
        self.assertEqual(self.read()['snapshotRevision'], first['snapshotRevision'])

    def test_missing_previously_authoritative_db_is_not_legacy_success(self):
        self.cycle()
        self.register()
        self.read()
        self.harness.path.unlink()
        with self.assertRaises(CenterError) as caught:
            self.read()
        self.assertEqual(caught.exception.code, 'HARNESS_UNAVAILABLE')

    def test_current_attempt_does_not_borrow_previous_attempt_report(self):
        cycle, first = self.cycle(close=False)
        self.harness.finish_attempt(first, {'outcome': 'failed', 'exitCode': 1}, writers_stopped=True, observation='stopped')
        self.harness.begin_attempt(cycle, 'attempt-correction', {'dispatchId': 'owned-next'})
        self.register()
        data = self.read()
        self.assertEqual(data['cycles'][0]['activeAttemptId'], 'attempt-correction')
        self.assertEqual(data['cycles'][0]['workReportStatus'], 'missing')
        self.assertIsNone(data['cycles'][0]['workReport'])
        self.assertEqual(len(data['cycles'][0]['attempts']), 2)

    def test_detail_partitions_keep_cycle_target_and_compact_does_not_erase_events(self):
        cycle, attempt = self.cycle(close=False)
        self.harness.record_event(attempt, 1, {'kind': 'process.exited', 'exitCode': 0})
        self.register()
        recent = self.read()
        detail = self.catalog.record(self.entry, cycle, self.source, query=self.query(recent))
        self.assertEqual(detail['partitions']['report'], recent['cycles'][0]['partitions']['report'])
        self.assertEqual(detail['events'][0]['kind'], 'process.exited')
        version = detail['partitions']['events']['revision']
        following = self.read()
        self.assertIsNone(following['cycles'][0]['partitions']['events']['revision'])
        self.assertEqual(following['cycles'][0]['partitions']['events']['errorCode'], 'NOT_REQUESTED')
        again = self.catalog.record(self.entry, cycle, self.source, query=self.query(recent))
        self.assertEqual(again['partitions']['events']['revision'], version)

    def test_real_observation_asof_advances_without_changing_fact_revision(self):
        self.cycle()
        self.register()
        snapshot = self.catalog._snapshot
        dates = iter(['2026-10-22T01:02:00+00:00', '2026-10-22T01:03:00+00:00'])
        def observed(*args, **kwargs):
            data, _ = snapshot(*args, **kwargs)
            return data, {'observedAt': next(dates)}
        with patch.object(self.catalog, '_snapshot', side_effect=observed):
            first, second = self.read(), self.read()
        self.assertEqual(first['snapshotRevision'], second['snapshotRevision'])
        self.assertNotEqual(first['partitions']['runtime']['asOf'], second['partitions']['runtime']['asOf'])

    def test_legacy_v2_current_display_pointer_and_core_status_are_stable(self):
        self.harness.path.unlink()
        identity = products.reserve_cycle(self.root, 'projects/one', 'old-runtime', 1)
        products.update_cycle(self.root, identity['cycleId'], 'completed')
        path = self.root / 'logs/usage.jsonl'
        path.parent.mkdir(exist_ok=True)
        record = {'schema_version': 1, 'kind': 'cycle_usage', 'cycle_id': identity['cycleId'], 'cycle_number': 1,
            'project': 'projects/one', 'started_at': '2026-10-20T01:00:00+00:00', 'ended_at': '2026-10-20T01:01:00+00:00',
            'status': 'completed', 'usage': {'total_tokens': 3}}
        path.write_text(json.dumps(record) + '\n')
        self.register()
        first = self.read()
        self.assertEqual(first['currentCycleId'], identity['cycleId'])
        self.assertFalse(first['currentCycle']['active'])
        self.assertEqual(first['currentCycle']['protocolState'], 'legacy')
        record['status'] = 'failed'
        path.write_text(json.dumps(record) + '\n')
        second = self.read()
        self.assertEqual(second['sourceBindingVersion'], first['sourceBindingVersion'])
        self.assertEqual(second['projectionEpoch'], first['projectionEpoch'])
        self.assertGreater(second['snapshotRevision'], first['snapshotRevision'])
        self.assertEqual(second['cycles'][0]['status'], 'failed')

    @unittest.skipUnless(sys.platform == 'linux', 'Execution-domain file safety runs under WSL')
    def test_execution_domain_attempt_log_checks_authoritative_owner(self):
        from center_runner import source_query
        _, attempt = self.cycle()
        product = products.get_identity(self.root, 'projects/one')['id']
        result = source_query(self.root, 'log', relative_path='logs/' + attempt['attemptId'] + '.log', expected_product_id=product)
        self.assertEqual(result['content'], 'private attempt 1')
        with self.assertRaisesRegex(ValueError, 'attempt_not_recorded'):
            source_query(self.root, 'log', relative_path='logs/' + attempt['attemptId'] + '.log', expected_product_id='another-product')
        with self.assertRaisesRegex(ValueError, 'attempt_not_recorded'):
            source_query(self.root, 'log', relative_path='logs/attempt-unregistered.log')

    def test_harness_capability_is_explicit_without_changing_existing_roots(self):
        from center_runtime import harness_capability
        folder = self.root / 'scripts/core'
        folder.mkdir(parents=True)
        for name in ('company_harness.py', 'company_harness_runner.py', 'company_harness_bridge.py',
                     'company_harness_client.py', 'company_harness_contract.py', 'company_harness_handoff.py',
                     'company_harness_inputs.py', 'company_harness_loop.sh', 'company_harness_quality.py'):
            (folder / name).write_text('# capability fixture')
        with patch.dict('os.environ', {'CODEX_SANDBOX_MODE': 'danger-full-access'}):
            self.assertTrue(harness_capability(self.root, 'codex')['supported'])
            self.assertEqual(harness_capability(self.root, 'claude')['reason'], 'unsupported_adapter')
        with patch.dict('os.environ', {'CODEX_SANDBOX_MODE': 'read-only'}):
            self.assertEqual(harness_capability(self.root, 'codex')['reason'], 'unsupported_inner_sandbox')
        self.assertFalse((self.root / '.autonomous-company.local').exists())
        sys.path.insert(0, str(ROOT / 'scripts/core'))
        from center_runner import CONTROL_FILES
        for name in ('company_harness.py', 'company_harness_bridge.py', 'company_harness_client.py',
                     'company_harness_contract.py', 'company_harness_handoff.py', 'company_harness_inputs.py',
                     'company_harness_loop.sh', 'company_harness_quality.py', 'company_harness_runner.py'):
            self.assertIn('scripts/core/' + name, CONTROL_FILES)

    def test_center_catalog_updates_from_harness_progress_without_legacy_report(self):
        cycle, attempt = self.cycle(close=False, report=False)
        self.register()
        self.assertIsNone(self.catalog.get_entry(self.entry)['latestTitle'])
        self.harness.publish_progress(attempt, 'visible-progress', {'reportRevision': 1, 'title': 'Actual Harness title',
            'summary': 'Bounded reported progress', 'reportedPhase': 'validating'})
        self.catalog.refresh_source(self.source)
        entry = self.catalog.get_entry(self.entry)
        self.assertEqual(entry['latestTitle'], 'Actual Harness title')
        self.assertEqual(entry['latestCycleStatus'], 'unknown')
        self.assertEqual(entry['latestProtocolState'], 'executing')
        self.assertFalse(entry['latestCycleActiveConfirmed'])
        self.assertEqual(entry['reportedPhase'], 'validating')
        self.assertFalse((self.root / 'logs' / (cycle + '.work.json')).exists())

    def test_resolve_log_target_allows_entry_cycles_and_attempts_and_rejects_foreign_logs(self):
        cycle, attempt = self.cycle()
        (self.root / 'logs/foreign.log').write_text('secret other entry')
        self.register()
        query = self.query(self.read())
        source, _ = self.catalog.projection.resolve_log_target(self.entry, cycle, query)
        self.assertEqual(source['sourceId'], self.source)
        source_att, _ = self.catalog.projection.resolve_log_target(self.entry, attempt['attemptId'], query)
        self.assertEqual(source_att['sourceId'], self.source)
        page = self.catalog.log_page(self.entry, attempt['attemptId'], query)
        self.assertTrue(page['ok'])
        with self.assertRaises(CenterError) as err:
            self.catalog.projection.resolve_log_target(self.entry, 'foreign', query)
        self.assertEqual(err.exception.status, 404)


if __name__ == '__main__':
    unittest.main()
