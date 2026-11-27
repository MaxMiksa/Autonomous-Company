"""Center registration, transactions and cross-identity read boundaries."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get('AUTONOMOUS_COMPANY_TEST_SOURCE', Path(__file__).resolve().parents[1]))
sys.path[:0] = [str(ROOT / 'dashboard'), str(ROOT / 'scripts/core')]
from center_store import CenterStore, CenterError
from center_catalog import CenterCatalog
import product_identity as products


class CenterCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'run'
        self.root.mkdir()
        self.store = CenterStore(self.base / 'center')
        self.addCleanup(self.store.close)
        self.catalog = CenterCatalog(self.store)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def cycle(self, project='projects/one', attempt='first', tokens=13, created_project=None):
        if project:
            (self.root / project).mkdir(parents=True, exist_ok=True)
        row = products.reserve_cycle(self.root, project, attempt, 1, 'fixture', 'no-model')
        if created_project:
            (self.root / created_project).mkdir(parents=True, exist_ok=True)
            products.register_project(self.root, created_project, row['cycleId'])
        products.update_cycle(self.root, row['cycleId'], 'completed')
        record = {'schema_version': 1, 'kind': 'cycle_usage', 'cycle_id': row['cycleId'], 'cycle_number': 1,
                  'project': project or None, 'started_at': '2026-09-26T01:00:00+00:00', 'ended_at': '2026-09-26T01:01:00+00:00',
                  'status': 'completed', 'usage': {'input_tokens': tokens - 1, 'output_tokens': 1, 'total_tokens': tokens}}
        path = self.root / 'logs/usage.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as output:
            output.write(json.dumps(record) + '\n')
        self.write('logs/' + row['cycleId'] + '.log', (project or 'exploration') + ' private log')
        return row

    def import_root(self, root=None):
        candidate = self.catalog.probe({'root': str(root or self.root)})
        result = self.catalog.commit({'candidateId': candidate['candidateId'], 'candidateHash': candidate['candidateHash'], 'idempotencyKey': candidate['candidateId']})
        return result['items']

    def hashes(self):
        return {str(path.relative_to(self.root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in self.root.rglob('*') if path.is_file()}

    def test_legacy_summary_is_restored_with_record_provenance_and_no_identity_write(self):
        self.write('logs/usage.jsonl', json.dumps({'schema_version': 1, 'kind': 'cycle_usage', 'cycle_id': 'cycle-legacy-1',
                   'cycle_number': 1, 'started_at': '2026-09-18T01:00:00+00:00', 'ended_at': '2026-09-18T01:01:00+00:00',
                   'status': 'completed'}) + '\n')
        self.write('logs/cycle-legacy-1.json', json.dumps({'result': '真实交付摘要\n\n更多工作记录'}))
        before = self.hashes()
        item, = self.import_root()
        entry = self.catalog.get_entry(item['entryId'])
        self.assertEqual(entry['latestTitle'], '真实交付摘要')
        self.assertEqual(entry['latestWork']['provenance'], 'cycle_summary')
        self.assertEqual(entry['latestWork']['cycleId'], 'cycle-legacy-1')
        self.assertEqual(entry['executionSummary']['state'], 'read_only')
        self.assertEqual(entry['latestCycleStatus'], 'completed')
        self.assertEqual(entry['displayName'], 'Autonomous Company')
        self.assertIsNone(entry['productId'])
        self.assertEqual(self.hashes(), before)

    def test_prior_work_does_not_replace_latest_round_facts(self):
        first = self.cycle(attempt='first')
        self.write('logs/' + first['cycleId'] + '.json', json.dumps({'result': 'Earlier meaningful work'}))
        second = self.cycle(attempt='second')
        # Match actual timestamps so ordering is deterministic rather than ID order.
        records = [json.loads(line) for line in (self.root / 'logs/usage.jsonl').read_text().splitlines()]
        records[-1].update(started_at='2026-09-26T02:00:00+00:00', ended_at='2026-09-26T02:01:00+00:00', status='failed')
        self.write('logs/usage.jsonl', '\n'.join(json.dumps(row) for row in records) + '\n')
        self.write('logs/' + second['cycleId'] + '.work.json', '{bad report')
        self.write('logs/' + second['cycleId'] + '.json', json.dumps({'result': 'Invalid report must not become latest work'}))
        item, = self.import_root()
        entry = self.catalog.get_entry(item['entryId'])
        self.assertEqual(entry['latestTitle'], 'Earlier meaningful work')
        self.assertEqual(entry['latestWork']['cycleId'], first['cycleId'])
        self.assertFalse(entry['latestWork']['isLatestCycle'])
        self.assertEqual(entry['latestCycleStatus'], 'failed')

    def test_product_without_product_rounds_includes_linked_exploration_sequence(self):
        row = self.cycle(project=None, created_project='projects/new')
        self.write('logs/' + row['cycleId'] + '.json', json.dumps({'result': 'Exploration produced the registered product'}))
        items = self.import_root()
        entry = next(self.catalog.get_entry(item['entryId']) for item in items if self.catalog.get_entry(item['entryId'])['kind'] == 'product')
        self.assertEqual(entry['latestWork']['scope'], 'exploration')
        self.assertEqual(entry['latestWork']['cycleId'], row['cycleId'])
        self.assertTrue(entry['latestWork']['isLatestCycle'])
        self.assertEqual(entry['cycleNumber'], 1)
        self.assertEqual(entry['latestCycleStatus'], 'completed')

    def test_log_tail_discards_partial_json_event_and_keeps_complete_unicode_lines(self):
        row = self.cycle()
        final = json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': '核验完成'}}, ensure_ascii=False) + '\n'
        self.write('logs/' + row['cycleId'] + '.log', '前' * (128 * 1024) + '\n' + final)
        item, = self.import_root()
        content, mime = self.catalog.resource(item['entryId'], 'log-' + row['cycleId'])
        self.assertEqual(content.decode('utf-8').splitlines(), final.splitlines())
        self.assertEqual(mime, 'text/plain; charset=utf-8')

    def test_managed_log_uses_authorized_domain_and_never_falls_back(self):
        row = self.cycle()
        item, = self.import_root()
        with self.store.transaction() as tx:
            source = tx.get('sources', item['sourceId'])
            source['runtimeId'] = 'runtime-test'
            tx.put('sources', source['sourceId'], source)
            tx.put('runtimes', 'runtime-test', {'managed': True})
        calls = []
        def query(source, action, **kwargs):
            calls.append((source['sourceId'], action, kwargs))
            return {'ok': True, 'content': '域内日志\n', 'totalBytes': 13}
        self.catalog.execution_query = query
        content, _ = self.catalog.resource(item['entryId'], 'log-' + row['cycleId'])
        self.assertEqual(content.decode('utf-8'), '域内日志\n')
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][2]['path'], 'logs/' + row['cycleId'] + '.log')
        self.assertEqual(calls[1][2]['limit'], 128 * 1024)
        self.catalog.execution_query = lambda *args, **kwargs: {'ok': False}
        with self.assertRaises(CenterError) as raised:
            self.catalog.resource(item['entryId'], 'log-' + row['cycleId'])
        self.assertEqual(raised.exception.code, 'CONTEXT_UNAVAILABLE')
        with self.assertRaises(CenterError):
            self.catalog.resource(item['entryId'], 'log-cycle-unrelated')
        with self.store.transaction() as tx:
            tx.put('runtimes', 'runtime-test', {'managed': False})
        content, _ = self.catalog.resource(item['entryId'], 'log-' + row['cycleId'])
        self.assertEqual(content.decode('utf-8'), 'projects/one private log')

    def test_import_candidate_invalidated_by_environment_or_mapping_change(self):
        self.cycle()
        binding = {'root': str(self.root), 'executionRoot': '/custom/run',
                   'executionDomain': {'platform': 'wsl', 'distribution': 'Chosen', 'user': 'operator'}, 'environmentRevision': 1}
        self.catalog.path_resolver = lambda value: dict(binding)
        candidate = self.catalog.probe({'root': '/custom/run'})
        body = {'candidateId': candidate['candidateId'], 'candidateHash': candidate['candidateHash']}
        for change in ({'environmentRevision': 2}, {'executionRoot': '/changed/run'},
                       {'executionDomain': {'platform': 'wsl', 'distribution': 'Other', 'user': 'operator'}}):
            with self.subTest(change=change):
                self.catalog.path_resolver = lambda value: {**binding, **change}
                with self.assertRaises(CenterError) as raised:
                    self.catalog.commit(body)
                self.assertEqual(raised.exception.code, 'SOURCE_CHANGED')
        self.catalog.path_resolver = lambda value: dict(binding)
        self.assertEqual(len(self.catalog.commit(body)['items']), 1)

    def test_exploration_direction_date_and_short_identity_are_searchable(self):
        self.cycle(project=None)
        item, = self.import_root()
        with self.store.transaction() as tx:
            entry = tx.get('entries', item['entryId'])
            entry.update(direction='  Local\n invoice tracking  ', createdAt='2026-10-18T00:00:00Z')
            tx.put('entries', entry['entryId'], entry)
        result = self.catalog.get_entry(item['entryId'])
        self.assertEqual(result['displayName'], 'Local invoice tracking')
        self.assertEqual(result['directionSummary'], 'Local invoice tracking')
        for query in ('invoice', '2026-10-18', result['shortId']):
            self.assertEqual(self.catalog.list_entries({'filter': 'all', 'q': query})['total'], 1)
        with self.store.transaction() as tx:
            entry.pop('direction')
            tx.put('entries', entry['entryId'], entry)
            tx.put('operations', 'original', {'result': {'entryId': entry['entryId']},
                                            'input': {'direction': 'Original direction'}})
        self.assertEqual(self.catalog.get_entry(item['entryId'])['directionSummary'], 'Original direction')

    def test_managed_snapshot_uses_domain_configuration_only_for_matching_identity(self):
        cycle = self.cycle()
        item, = self.import_root()
        with self.store.transaction() as tx:
            source = tx.get('sources', item['sourceId'])
            source['runtimeId'] = 'runtime-test'
            tx.put('sources', source['sourceId'], source)
            tx.put('runtimes', 'runtime-test', {'managed': True})
        status = {'ok': True, 'timestamp': '2026-10-18T00:00:00Z', 'executionDomain': {'platform': 'posix'},
                  'stateFile': {'PRODUCT_ID': cycle['productId']},
                  'parsed': {'loop': {'state': 'idle', 'processState': 'running', 'pid': 123}}}
        self.catalog.managed_observer = lambda row: {'managed': True, 'status': status,
                                                    'config': {'effort': 'xhigh', 'productLanguage': 'zh-CN'}}
        result = self.catalog.journal(item['entryId'])
        self.assertEqual(result['runtime']['reasoning'], 'xhigh')
        self.assertEqual(result['runtime']['state'], 'idle')
        self.assertFalse(result['readOnly'])
        status['stateFile']['PRODUCT_ID'] = 'foreign'
        result = self.catalog.journal(item['entryId'])
        self.assertEqual(result['runtime']['reasoning'], 'unknown')
        self.assertEqual(result['runtime']['state'], 'unknown')
        self.catalog.managed_observer = lambda row: {}
        result = self.catalog.journal(item['entryId'])
        self.assertTrue(result['readOnly'])
        self.assertEqual(result['runtime']['state'], 'unknown')

    def test_released_source_with_runtime_id_keeps_readonly_refresh_journal_and_log(self):
        from center_runtime import CenterRuntime
        cycle = self.cycle()
        item, = self.import_root()
        with self.store.transaction() as tx:
            source = tx.get('sources', item['sourceId'])
            source['runtimeId'] = 'released-runtime'
            tx.put('sources', source['sourceId'], source)
            tx.put('runtimes', 'released-runtime', {'managed': True})
        self.catalog.managed_observer = lambda row: {}
        self.assertEqual(self.catalog.refresh_source(item['sourceId'])['availability'], 'available')
        with self.store.transaction() as tx:
            runtime = tx.get('runtimes', 'released-runtime')
            runtime['managed'] = False
            tx.put('runtimes', 'released-runtime', runtime)
        runtime = CenterRuntime.__new__(CenterRuntime)
        runtime.store = self.store
        runtime.domain = {'platform': 'posix'}
        self.catalog.managed_observer = runtime.observe_source
        self.catalog.execution_query = runtime.execution_query
        before = self.hashes()
        status = {'ok': True, 'timestamp': '2026-10-18T00:00:00Z', 'executionDomain': {'platform': 'posix'},
                  'stateFile': {}, 'parsed': {'loop': {'state': 'stopped', 'processState': 'stopped', 'pid': None}}}
        with patch.object(self.catalog.readonly_observer, 'status', return_value=status) as observed:
            refreshed = self.catalog.refresh_source(item['sourceId'])
            self.assertEqual(refreshed['availability'], 'available')
            self.assertEqual(refreshed['runtimeId'], 'released-runtime')
            journal = self.catalog.journal(item['entryId'])
            self.assertTrue(journal['readOnly'])
            self.assertEqual(journal['readonlyObservation']['state'], 'ended')
            content, _ = self.catalog.resource(item['entryId'], 'log-' + cycle['cycleId'])
            self.assertEqual(content.decode('utf-8'), 'projects/one private log')
            self.assertEqual(observed.call_count, 3)
        self.assertEqual(self.hashes(), before)

    def test_managed_observation_failure_never_uses_readonly_host_observation(self):
        from center_runtime import CenterRuntime
        self.cycle()
        item, = self.import_root()
        with self.store.transaction() as tx:
            source = tx.get('sources', item['sourceId'])
            source['runtimeId'] = 'managed-runtime'
            tx.put('sources', source['sourceId'], source)
            tx.put('runtimes', 'managed-runtime', {'managed': True, 'executionDomain': {'platform': 'foreign'}})
        runtime = CenterRuntime.__new__(CenterRuntime)
        runtime.store = self.store
        runtime.domain = {'platform': 'posix'}
        self.catalog.managed_observer = runtime.observe_source
        with patch.object(self.catalog.readonly_observer, 'status', side_effect=AssertionError('host fallback')):
            with self.assertRaises(CenterError) as raised:
                self.catalog.journal(item['entryId'])
            self.assertEqual(raised.exception.code, 'READ_ONLY_SOURCE')
            self.assertEqual(self.catalog.refresh_source(item['sourceId'])['availability'], 'conflict')

    def test_observation_freshness_does_not_change_source_revision_or_catalog_cursor(self):
        self.cycle()
        self.cycle('projects/two', 'second')
        items = self.import_root()
        item = items[0]
        before = self.catalog.get_entry(item['entryId'])['sourceRevision']
        with patch('center_catalog.scoped_observation', return_value={'state': 'ended', 'observedAt': '2026-10-03T00:00:00+00:00'}):
            self.catalog.refresh_source(item['sourceId'])
            page = self.catalog.list_entries({'limit': 1})
        with patch('center_catalog.scoped_observation', return_value={'state': 'ended', 'observedAt': '2026-10-03T00:00:05+00:00'}):
            self.catalog.refresh_source(item['sourceId'])
            second = self.catalog.list_entries({'limit': 1, 'cursor': page['nextCursor']})
        self.assertEqual(len(second['items']), 1)
        self.assertEqual(self.catalog.get_entry(item['entryId'])['sourceRevision'], before)

    def test_transactions_rollback_and_read_revision(self):
        revision = self.store.revision
        with self.store.transaction() as tx:
            self.assertEqual(tx.list('entries'), [])
        self.assertEqual(self.store.revision, revision)
        with self.assertRaises(RuntimeError):
            with self.store.transaction() as tx:
                tx.put('entries', 'x', {'entryId': 'x'})
                raise RuntimeError('fail')
        with self.store.transaction() as tx:
            self.assertIsNone(tx.get('entries', 'x'))
        self.assertEqual(self.store.revision, revision)

    def test_second_owner_rejected(self):
        with self.assertRaises(CenterError) as context:
            CenterStore(self.base / 'center')
        self.assertEqual(context.exception.code, 'CENTER_BUSY')

    def test_store_identity_persists(self):
        identity = self.store.center_id
        self.store.close()
        self.store = CenterStore(self.base / 'center')
        self.addCleanup(self.store.close)
        self.assertEqual(self.store.center_id, identity)

    def test_import_and_read_never_mutate_source(self):
        self.cycle()
        self.write('memories/consensus.md', '# Other global report\n## Current Phase\nWrong phase')
        before = self.hashes()
        item, = self.import_root()
        self.catalog.journal(item['entryId'])
        self.catalog.usage(item['entryId'])
        self.assertEqual(self.hashes(), before)

    def test_multi_product_logs_usage_consensus_isolated(self):
        one = self.cycle(tokens=13)
        two = self.cycle('projects/two', 'second', 90)
        self.write('.autonomous-company.local', 'ACTIVE_PROJECT=projects/two\n')
        self.write('memories/consensus.md', '# Other global report\n## Current Phase\nWrong phase')
        entries = self.import_root()
        item = next(item for item in entries if self.catalog.get_entry(item['entryId'])['productId'] == one['productId'])
        snapshot = self.catalog.journal(item['entryId'])
        self.assertEqual([row['id'] for row in snapshot['cycles']], [one['cycleId']])
        self.assertEqual(snapshot['consensus']['raw'], '')
        self.assertEqual(self.catalog.usage(item['entryId'])['usage']['totalTokens'], 13)
        with self.assertRaises(CenterError):
            self.catalog.resource(item['entryId'], 'log-' + two['cycleId'])
        content, mime = self.catalog.resource(item['entryId'], 'log-' + one['cycleId'])
        self.assertIn(b'projects/one', content)

    def test_duplicate_import_is_idempotent(self):
        self.cycle()
        first, = self.import_root()
        second, = self.import_root()
        self.assertEqual(first['entryId'], second['entryId'])
        self.assertEqual(first['sourceId'], second['sourceId'])
        self.assertTrue(second['duplicate'])
        self.assertEqual(self.catalog.list_entries()['total'], 1)

    def test_source_change_between_probe_commit_rejected(self):
        self.cycle()
        candidate = self.catalog.probe({'root': str(self.root)})
        self.cycle('projects/two', 'second')
        with self.assertRaises(CenterError) as context:
            self.catalog.commit(candidate)
        self.assertEqual(context.exception.code, 'SOURCE_CHANGED')

    def test_inherited_examples_are_not_products(self):
        self.write('projects/example/README.md', '# bundled example')
        with self.assertRaises(CenterError) as context:
            self.catalog.probe({'root': str(self.root)})
        self.assertEqual(context.exception.code, 'NO_RECORDED_PRODUCTS')

    def test_relocated_identity_keeps_history(self):
        original = self.cycle()
        item, = self.import_root()
        (self.root / 'projects/one').rename(self.root / 'projects/moved')
        products.relocate_identity(self.root, original['productId'], 'projects/moved')
        snapshot = self.catalog.journal(item['entryId'])
        self.assertEqual(snapshot['project']['id'], 'projects/moved')
        self.assertEqual(snapshot['cycles'][0]['stableProductId'], original['productId'])

    def test_reused_path_never_exposes_replacement_metadata(self):
        original = self.cycle()
        item, = self.import_root()
        (self.root / 'projects/one/.autonomous-company/identity.json').unlink()
        replacement = products.register_project(self.root, 'projects/one')
        self.assertNotEqual(replacement['id'], original['productId'])
        self.write('projects/one/.autonomous-company/project.json', json.dumps({'displayName': 'wrong replacement'}))
        snapshot = self.catalog.journal(item['entryId'])
        self.assertEqual(snapshot['project']['status'], 'historical')
        self.assertNotEqual(snapshot['project']['displayName'], 'wrong replacement')
        self.assertIsNone(snapshot['productMedia'])

    def test_missing_and_corrupt_source_isolated_from_catalog(self):
        self.cycle()
        item, = self.import_root()
        self.write('.autonomous-company/product-state.json', '{broken')
        self.catalog.refresh_source(item['sourceId'])
        self.assertEqual(self.catalog.list_entries()['items'][0]['availability'], 'conflict')
        self.assertEqual(self.catalog.list_entries()['total'], 1)

    def test_backup_is_same_entry_with_distinct_readonly_source(self):
        self.cycle()
        one, = self.import_root()
        backup = self.base / 'backup'
        shutil.copytree(self.root, backup)
        two, = self.import_root(backup)
        self.assertEqual(one['entryId'], two['entryId'])
        self.assertNotEqual(one['sourceId'], two['sourceId'])
        entry = self.catalog.get_entry(one['entryId'])
        self.assertEqual(len(entry['sources']), 2)
        self.assertFalse(entry['capabilities']['execute'])
        sources = {row['sourceId']: row for row in entry['sources']}
        self.assertEqual(sources[one['sourceId']]['displayName'], self.root.name)
        self.assertEqual(sources[two['sourceId']]['rootName'], backup.name)
        self.assertEqual(sources[two['sourceId']]['displayPath'], str(backup.resolve()))
        self.assertTrue(sources[two['sourceId']]['lastVerifiedAt'])
        self.assertNotIn('root', sources[one['sourceId']])
        self.assertNotIn('displayPath', self.catalog.list_entries()['items'][0])

    def test_cursor_expires_when_catalog_changes(self):
        self.cycle()
        self.cycle('projects/two', 'second')
        entries = self.import_root()
        page = self.catalog.list_entries({'limit': 1})
        self.assertIsNotNone(page['nextCursor'])
        self.catalog.entry_action(entries[0]['entryId'], 'archive', {'expectedRevision': 1})
        with self.assertRaises(CenterError) as context:
            self.catalog.list_entries({'cursor': page['nextCursor'], 'limit': 1})
        self.assertEqual(context.exception.code, 'CURSOR_EXPIRED')

    def test_archive_open_request_and_stale_revision_rejected(self):
        self.cycle()
        item, = self.import_root()
        with self.store.transaction() as tx:
            tx.put('requests', 'request', {'entryId': item['entryId'], 'state': 'queued'})
        with self.assertRaises(CenterError):
            self.catalog.entry_action(item['entryId'], 'archive', {'expectedRevision': 1})
        with self.assertRaises(CenterError):
            self.catalog.entry_action(item['entryId'], 'restore', {'expectedRevision': 999})

    def test_detach_tombstone_preserves_source(self):
        self.cycle()
        item, = self.import_root()
        before = self.hashes()
        self.catalog.entry_action(item['entryId'], 'detach', {'expectedRevision': 1})
        self.assertEqual(self.catalog.list_entries()['total'], 0)
        with self.store.transaction() as tx:
            self.assertTrue(tx.get('entries', item['entryId'])['detached'])
        self.assertEqual(self.hashes(), before)

    def test_reconnect_same_identity_and_reject_wrong_identity(self):
        self.cycle()
        item, = self.import_root()
        backup = self.base / 'moved'
        shutil.copytree(self.root, backup)
        candidate = self.catalog.probe({'root': str(backup)})
        body = {**candidate, 'expectedRevision': 1, 'idempotencyKey': 'relocate'}
        source = self.catalog.reconnect(item['sourceId'], body)
        self.assertEqual(self.catalog.reconnect(item['sourceId'], body), source)
        self.assertEqual(source['root'], str(backup.resolve()))
        self.assertEqual(self.catalog.journal(item['entryId'])['sourceId'], item['sourceId'])

    def test_explicit_foreign_source_id_rejected(self):
        self.cycle()
        self.cycle('projects/two', 'second')
        one, two = self.import_root()
        with self.assertRaises(CenterError):
            self.catalog.journal(one['entryId'], {'sourceId': two['sourceId']})

    def test_stat_refresh_skips_unchanged_and_marks_missing(self):
        self.cycle()
        item, = self.import_root()
        self.assertEqual(self.catalog.refresh_changed_sources()['refreshed'], 1)
        self.assertEqual(self.catalog.refresh_changed_sources()['refreshed'], 0)
        self.root.rename(self.base / 'removed')
        self.assertEqual(self.catalog.refresh_changed_sources()['refreshed'], 1)
        self.assertEqual(self.catalog.get_entry(item['entryId'])['availability'], 'missing')

    def test_sqlite_backup_includes_committed_wal(self):
        with self.store.transaction() as tx:
            tx.put('entries', 'saved', {'entryId': 'saved'})
        backup = self.store.backup()
        with sqlite3.connect(backup) as connection:
            self.assertIsNotNone(connection.execute("SELECT body FROM records WHERE id='saved'").fetchone())
        connection.close()
        with self.assertRaises(CenterError):
            self.store.backup(backup)

    def test_unknown_schema_does_not_change_journal_mode(self):
        self.store.close()
        path = self.base / 'center/center.sqlite3'
        with sqlite3.connect(str(path)) as connection:
            connection.execute("UPDATE metadata SET value='999' WHERE key='schemaVersion'")
            connection.commit()
            connection.execute('PRAGMA journal_mode=DELETE')
        connection.close()
        before = path.read_bytes()
        with self.assertRaises(CenterError):
            CenterStore(self.base / 'center')
        self.assertEqual(path.read_bytes(), before)

    def test_conflicting_backup_stays_candidate(self):
        row = self.cycle()
        self.import_root()
        backup = self.base / 'conflicting'
        shutil.copytree(self.root, backup)
        path = backup / '.autonomous-company/product-state.json'
        state = json.loads(path.read_text())
        state['cycles'][row['cycleId']]['state'] = 'failed'
        path.write_text(json.dumps(state))
        candidate = self.catalog.probe({'root': str(backup)})
        with self.assertRaises(CenterError) as context:
            self.catalog.commit(candidate)
        self.assertEqual(context.exception.code, 'SOURCE_CONFLICT')
        with self.store.transaction() as tx:
            self.assertEqual(len(tx.list('sources')), 1)
            self.assertIsNotNone(tx.get('candidates', candidate['candidateId']))

    def test_conflicting_usage_is_unknown_not_summed(self):
        row = self.cycle()
        path = self.root / 'logs/usage.jsonl'
        record = json.loads(path.read_text())
        record['usage']['total_tokens'] = 200
        with path.open('a') as output:
            output.write(json.dumps(record) + '\n')
        item, = self.import_root()
        usage = self.catalog.usage(item['entryId'])
        self.assertIsNone(usage['usage']['totalTokens'])
        self.assertEqual(usage['conflicting'], 1)
        self.assertEqual(usage['unknown'], 1)

    def test_managed_exploration_transition_preserves_entry(self):
        entry = {'entryId': 'entry', 'kind': 'exploration', 'productId': None, 'explorationId': None,
                 'preferredSourceId': 'source', 'revision': 1, 'archived': False, 'detached': False}
        source = {'sourceId': 'source', 'entryId': 'entry', 'runtimeId': 'runtime', 'root': str(self.root),
                  'kind': 'exploration', 'productId': None, 'explorationId': None, 'revision': 1, 'sourceRevision': 1}
        with self.store.transaction() as tx:
            tx.put('entries', 'entry', entry)
            tx.put('sources', 'source', source)
        self.assertEqual(self.catalog.refresh_source('source')['availability'], 'available')
        row = products.reserve_cycle(self.root, '', 'first', 1, 'fixture', 'no-model')
        self.catalog.refresh_source('source')
        (self.root / 'projects/created').mkdir(parents=True)
        product = products.register_project(self.root, 'projects/created', row['cycleId'])
        self.catalog.refresh_source('source')
        result = self.catalog.get_entry('entry')
        self.assertEqual(result['kind'], 'product')
        self.assertEqual(result['productId'], product['id'])
        self.assertEqual(result['entryId'], 'entry')

    def test_linked_exploration_separate_from_default_product_list(self):
        row = products.reserve_cycle(self.root, '', 'first', 1, 'fixture', 'no-model')
        (self.root / 'projects/created').mkdir(parents=True)
        products.register_project(self.root, 'projects/created', row['cycleId'])
        self.import_root()
        self.assertEqual(self.catalog.list_entries()['total'], 1)
        self.assertEqual(self.catalog.list_entries({'filter': 'exploration'})['total'], 1)
        exploration = self.catalog.list_entries({'filter': 'exploration'})['items'][0]
        self.assertEqual(exploration['availability'], 'available')
        self.assertEqual(self.catalog.journal(exploration['entryId'])['cycles'][0]['projectStatus'], 'current')

    def managed_discovery(self, completed_before_discovery=False):
        entry = {'entryId': 'entry-managed', 'kind': 'exploration', 'productId': None, 'explorationId': None,
                 'preferredSourceId': 'source-managed', 'revision': 1, 'archived': False, 'detached': False}
        source = {'sourceId': 'source-managed', 'entryId': entry['entryId'], 'runtimeId': 'runtime-managed', 'root': str(self.root),
                  'kind': 'exploration', 'productId': None, 'explorationId': None, 'revision': 1, 'sourceRevision': 1}
        with self.store.transaction() as tx:
            tx.put('entries', entry['entryId'], entry)
            tx.put('sources', source['sourceId'], source)
        row = products.reserve_cycle(self.root, '', 'discovery-first', 1, 'fixture', 'no-model')
        products.update_cycle(self.root, row['cycleId'], 'dispatching')
        anchor = self.catalog.refresh_source(source['sourceId'])
        self.write('projects/created/README.md', '# Created product\n')
        self.write('projects/registry.tsv', 'name\tpath\tlifecycle\tcreated_at_utc\ncreated\tprojects/created\tlocal\t2026-10-06\n')
        product = products.register_project(self.root, 'projects/created', row['cycleId'])
        if completed_before_discovery:
            products.update_cycle(self.root, row['cycleId'], 'completed')
        child_id, = self.catalog._discover_products(anchor)
        with self.store.transaction() as tx:
            child = tx.get('sources', child_id)
        return source['sourceId'], child, row, product

    def test_managed_exploration_refreshes_completed_cycle_beside_exact_discovered_product(self):
        anchor_id, child, row, product = self.managed_discovery()
        old = self.catalog.get_entry('entry-managed')
        self.assertEqual(old['latestCycleStatus'], 'startup_unconfirmed')
        with self.store.transaction() as tx:
            tx.put('sources', child['sourceId'], {**child, 'discoveredFromSourceId': 'source-unrelated'})
        self.assertEqual(self.catalog.refresh_source(anchor_id)['availability'], 'conflict')
        products.update_cycle(self.root, row['cycleId'], 'completed')
        self.assertEqual(self.catalog.journal('entry-managed')['cycles'][0]['status'], 'completed')
        self.assertEqual(self.catalog.get_entry('entry-managed')['latestCycleStatus'], 'startup_unconfirmed')
        with self.store.transaction() as tx:
            tx.put('sources', child['sourceId'], child)
        before = self.hashes()
        self.catalog.refresh_source(anchor_id)
        self.catalog.refresh_source(child['sourceId'])
        exploration = self.catalog.get_entry('entry-managed')
        discovered = self.catalog.get_entry(child['entryId'])
        self.assertEqual(exploration['kind'], 'exploration')
        self.assertIsNone(exploration['productId'])
        self.assertEqual(exploration['explorationId'], row['explorationId'])
        self.assertEqual(exploration['runtimeId'], 'runtime-managed')
        self.assertEqual(exploration['sourceId'], anchor_id)
        self.assertEqual(exploration['availability'], 'available')
        self.assertNotIn('SOURCE_CONFLICT', exploration['warnings'])
        self.assertEqual(exploration['latestCycleStatus'], 'completed')
        self.assertEqual(exploration['cycleNumber'], 1)
        self.assertEqual(discovered['productId'], product['id'])
        self.assertEqual(discovered['latestCycleStatus'], 'completed')
        self.assertIsNone(discovered['runtimeId'])
        self.assertFalse(discovered['capabilities']['execute'])
        self.assertEqual(self.catalog.list_entries({'filter': 'all'})['total'], 2)
        self.assertEqual(self.hashes(), before)

    def test_completed_before_discovery_keeps_both_original_scopes(self):
        anchor_id, child, row, product = self.managed_discovery(completed_before_discovery=True)
        before = self.hashes()
        self.assertEqual(self.catalog.refresh_source(anchor_id)['availability'], 'available')
        self.catalog.refresh_source(child['sourceId'])
        exploration = self.catalog.get_entry('entry-managed')
        self.assertEqual(exploration['kind'], 'exploration')
        self.assertEqual(exploration['latestCycleStatus'], 'completed')
        self.assertEqual(self.catalog.get_entry(child['entryId'])['productId'], product['id'])
        self.assertEqual(self.hashes(), before)

    def test_unrelated_discovery_and_duplicate_or_tombstoned_products_stay_conflicted(self):
        anchor_id, child, row, product = self.managed_discovery()
        before = self.hashes()
        with self.store.transaction() as tx:
            entry = tx.get('entries', child['entryId'])
        for change in ({'root': str(self.base / 'foreign-root')}, {'project': 'projects/foreign'},
                       {'explorationId': 'f' * 32}, {'discoveredFromSourceId': 'source-foreign'},
                       {'productId': 'f' * 32}, {'runtimeId': 'runtime-foreign'}, {'detached': True}):
            with self.subTest(change=change):
                with self.store.transaction() as tx:
                    tx.put('sources', child['sourceId'], {**child, **change})
                self.assertEqual(self.catalog.refresh_source(anchor_id)['availability'], 'conflict')
        with self.store.transaction() as tx:
            tx.put('sources', child['sourceId'], child)
        for change in ({'explorationId': 'f' * 32},):
            with self.subTest(entry_change=change):
                with self.store.transaction() as tx:
                    tx.put('entries', entry['entryId'], {**entry, **change})
                self.assertEqual(self.catalog.refresh_source(anchor_id)['availability'], 'conflict')
        with self.store.transaction() as tx:
            tx.put('entries', entry['entryId'], entry)
            tx.put('entries', 'duplicate-product', {**entry, 'entryId': 'duplicate-product'})
        self.assertEqual(self.catalog.refresh_source(anchor_id)['availability'], 'conflict')
        self.assertEqual(self.catalog.get_entry('entry-managed')['kind'], 'exploration')
        self.assertEqual(self.hashes(), before)

    def test_detached_discovery_remains_inactive_and_preserves_existing_promotion(self):
        anchor_id, child, row, product = self.managed_discovery()
        with self.store.transaction() as tx:
            detached = {**tx.get('entries', child['entryId']), 'detached': True}
            detached_source = {**child, 'detached': True}
            tx.put('entries', child['entryId'], detached)
            tx.put('sources', child['sourceId'], detached_source)
        before = self.hashes()
        self.assertEqual(self.catalog.refresh_source(anchor_id)['availability'], 'available')
        managed = self.catalog.get_entry('entry-managed')
        self.assertEqual(managed['kind'], 'product')
        self.assertEqual(managed['productId'], product['id'])
        self.assertEqual(managed['runtimeId'], 'runtime-managed')
        self.assertEqual(self.catalog.list_entries({'filter': 'all'})['total'], 1)
        with self.assertRaises(CenterError) as context:
            self.catalog.get_entry(child['entryId'])
        self.assertEqual(context.exception.code, 'ENTRY_NOT_FOUND')
        with self.store.transaction() as tx:
            self.assertEqual(tx.get('entries', child['entryId']), detached)
            self.assertEqual(tx.get('sources', child['sourceId']), detached_source)
        self.assertEqual(self.hashes(), before)

    def test_discovered_product_without_original_ledger_link_stays_conflicted(self):
        anchor_id, child, row, product = self.managed_discovery()
        with products.transaction(self.root) as state:
            state['cycles'][row['cycleId']].pop('createdProductIds')
        before = self.hashes()
        self.assertEqual(self.catalog.refresh_source(anchor_id)['availability'], 'conflict')
        self.assertEqual(self.catalog.get_entry('entry-managed')['kind'], 'exploration')
        self.assertEqual(self.hashes(), before)

    def test_cycle_cursor_bound_to_history_snapshot(self):
        self.cycle(attempt='first')
        self.cycle(attempt='second')
        item, = self.import_root()
        page = self.catalog.journal(item['entryId'], {'limit': 1})
        next_page = self.catalog.journal(item['entryId'], {'before': page['nextBefore'], 'limit': 1})
        self.assertNotEqual(page['cycles'][0]['id'], next_page['cycles'][0]['id'])
        self.cycle(attempt='third')
        with self.assertRaises(CenterError) as context:
            self.catalog.journal(item['entryId'], {'before': page['nextBefore']})
        self.assertEqual(context.exception.code, 'CURSOR_EXPIRED')

    def test_default_journal_includes_linked_exploration_and_preserves_original_records(self):
        explorations = [self.cycle('', 'explore-' + str(index),
                                  created_project='projects/created' if index == 2 else None)
                        for index in range(3)]
        product_cycles = [self.cycle('projects/created', 'product-' + str(index)) for index in range(2)]
        ledger = self.root / 'logs/usage.jsonl'
        records = [json.loads(line) for line in ledger.read_text().splitlines()]
        for index, record in enumerate(records):
            record['started_at'] = f'2026-09-26T01:{index:02d}:00+00:00'
        ledger.write_text(''.join(json.dumps(record) + '\n' for record in records))
        before = self.hashes()
        items = self.import_root()
        item = next(row for row in items if self.catalog.get_entry(row['entryId'])['kind'] == 'product')
        first = self.catalog.journal(item['entryId'], {'limit': 2})
        self.assertTrue(first['project']['createdAt'])
        self.assertNotEqual(first['project']['createdAt'], self.catalog.get_entry(item['entryId'])['createdAt'])
        second = self.catalog.journal(item['entryId'], {'limit': 2, 'before': first['nextBefore']})
        third = self.catalog.journal(item['entryId'], {'limit': 2, 'before': second['nextBefore']})
        rows = first['cycles'] + second['cycles'] + third['cycles']
        self.assertEqual([row['id'] for row in rows], [row['cycleId'] for row in reversed(explorations + product_cycles)])
        self.assertEqual([row['sequenceNumber'] for row in rows], [5, 4, 3, 2, 1])
        self.assertEqual(self.catalog.get_entry(item['entryId'])['cycleNumber'], 5)
        self.assertEqual(self.catalog.get_entry(item['entryId'])['latestCycleStatus'], 'completed')
        self.assertEqual([row['number'] for row in rows], [2, 1, 3, 2, 1])
        self.assertEqual(first['total'], 5)
        self.assertIsNone(third['nextBefore'])
        selected = self.catalog.journal(item['entryId'], {'section': 'exploration', 'limit': 100})
        self.assertEqual([row['id'] for row in selected['cycles']], [row['cycleId'] for row in reversed(explorations)])
        self.assertEqual(selected['total'], 3)
        with self.assertRaises(CenterError) as context:
            self.catalog.journal(item['entryId'], {'section': 'exploration', 'before': first['nextBefore']})
        self.assertEqual(context.exception.code, 'CURSOR_EXPIRED')
        self.assertEqual(self.hashes(), before)

    def test_cycle_cursor_rejects_a_revised_source_with_unchanged_history(self):
        self.cycle(attempt='first')
        self.cycle(attempt='second')
        item, = self.import_root()
        first = self.catalog.journal(item['entryId'], {'limit': 1})
        with self.store.transaction() as tx:
            source = tx.get('sources', item['sourceId'])
            source['sourceRevision'] += 1
            tx.put('sources', item['sourceId'], source)
        with self.assertRaises(CenterError) as context:
            self.catalog.journal(item['entryId'], {'before': first['nextBefore']})
        self.assertEqual(context.exception.code, 'CURSOR_EXPIRED')

    def old_cycle(self):
        for index in range(32):
            self.cycle(attempt='history-' + str(index))
        item, = self.import_root()
        row = self.catalog.journal(item['entryId'], {'limit': 100})['cycles'][-1]
        self.assertEqual(row['detailStatus'], 'limited')
        return item, row

    def work_report(self, cycle_id, project='projects/one'):
        value = {'version': 2, 'cycle_id': cycle_id, 'project': project,
                 'recorded_at': '2026-09-26T01:01:00+00:00', 'source': 'model_report',
                 'final': True, 'phase': 'review', 'title': 'Recorded historical work',
                 'summary': 'Synthetic historical report', 'blocker': ''}
        self.write('logs/' + cycle_id + '.work.json', json.dumps(value))
        return value

    def test_old_record_hydrates_verified_details_and_scoped_links_after_relocation(self):
        from runtime_artifacts import base_record, save
        item, old = self.old_cycle()
        report = self.work_report(old['id'])
        event = {'version': 1, 'cycleId': old['id'], 'sequence': 1, 'kind': 'report',
                 'observedAt': '2026-09-26T01:01:00+00:00', 'text': 'Historical event', 'source': 'agent_report'}
        self.write('logs/' + old['id'] + '.events.jsonl', json.dumps(event) + '\n')
        records = []
        for kind in ('document', 'check'):
            path = 'projects/one/' + kind + '.txt'
            target = self.write(path, 'Recorded ' + kind)
            record = base_record('projects/one', kind, self.root)
            record.update(cycleId=old['id'], path=path, sha256=hashlib.sha256(target.read_bytes()).hexdigest())
            if kind == 'check':
                record.update(state='completed', exitCode=0, reportStatus='fresh',
                              tests={'tests': 2, 'failures': 0, 'errors': 0, 'skipped': 0})
            save(self.root, record)
            records.append(record)
        preview = self.preview(cycle_id=old['id'])
        (self.root / 'projects/one').rename(self.root / 'projects/moved')
        products.relocate_identity(self.root, old['stableProductId'], 'projects/moved')
        before = self.hashes()
        with patch('observability_data.preview_available', return_value=True):
            detail = self.catalog.record(item['entryId'], old['id'], item['sourceId'])
            self.assertEqual(detail['detailStatus'], 'recorded')
            self.assertEqual(detail['workReport'], report)
            self.assertEqual(detail['workReportStatus'], 'valid')
            self.assertEqual(detail['projectId'], 'projects/one')
            self.assertEqual(detail['projectStatus'], 'current')
            self.assertEqual(detail['events'][0]['text'], 'Historical event')
            self.assertEqual(detail['latestCheck']['tests']['tests'], 2)
            self.assertEqual(detail['checks'][0]['url'], detail['latestCheck']['url'])
            base = '/api/center/v1/entries/' + item['entryId'] + '/resources/'
            suffix = '?sourceId=' + item['sourceId']
            self.assertEqual(detail['logUrl'], base + 'log-' + old['id'] + suffix)
            self.assertEqual(detail['sourceId'], item['sourceId'])
            artifacts = {artifact['id']: artifact for artifact in detail['artifacts']}
            for record in records:
                artifact = artifacts[record['id']]
                self.assertEqual(artifact['url'], base + 'artifact-' + record['id'] + suffix)
                self.assertTrue(artifact['path'].startswith('projects/moved/'))
                content, _ = self.catalog.resource(item['entryId'], 'artifact-' + record['id'], item['sourceId'])
                self.assertIn(b'Recorded', content)
            self.assertEqual(artifacts[preview['id']]['url'], preview['url'])
        self.assertEqual(self.hashes(), before)

    def test_old_record_rejects_wrong_project_report_like_recent_record(self):
        item, old = self.old_cycle()
        recent = self.catalog.journal(item['entryId'])['cycles'][0]
        for row in (old, recent):
            self.work_report(row['id'], 'projects/other')
            detail = self.catalog.record(item['entryId'], row['id'])
            self.assertIsNone(detail['workReport'])
            self.assertEqual(detail['workReportStatus'], 'identity_mismatch')
            self.assertEqual(detail['detailStatus'], 'recorded')

    def test_old_record_rejects_foreign_cycle_and_missing_source_identity(self):
        item, old = self.old_cycle()
        foreign = self.cycle('projects/other', 'foreign')
        with self.assertRaises(CenterError) as context:
            self.catalog.record(item['entryId'], foreign['cycleId'])
        self.assertEqual(context.exception.code, 'RECORD_NOT_FOUND')
        (self.root / '.autonomous-company/product-state.json').unlink()
        with self.assertRaises(CenterError) as context:
            self.catalog.record(item['entryId'], old['id'])
        self.assertEqual(context.exception.code, 'SOURCE_CONFLICT')

    def preview(self, project='projects/one', cycle_id=None, url='http://127.0.0.1:12345/'):
        from runtime_artifacts import base_record, save
        record = base_record(project, 'preview', self.root)
        record.update(cycleId=cycle_id, state='running', lifetime='cycle' if cycle_id else 'operator',
                      url=url, token='a' * 32)
        save(self.root, record)
        return record

    def test_operator_preview_is_product_bound_and_keeps_verified_url(self):
        one = self.cycle()
        two = self.cycle('projects/two', 'second')
        record = self.preview()
        with patch('observability_data.preview_available', return_value=True):
            items = self.import_root()
            item = next(item for item in items if self.catalog.get_entry(item['entryId'])['productId'] == one['productId'])
            other = next(item for item in items if self.catalog.get_entry(item['entryId'])['productId'] == two['productId'])
            before = self.hashes()
            snapshot = self.catalog.journal(item['entryId'], {'sourceId': item['sourceId']})
            preview, = snapshot['artifacts']
            self.assertEqual(preview['associationStatus'], 'product')
            self.assertEqual(preview['productId'], one['productId'])
            self.assertIsNone(preview['cycleId'])
            self.assertTrue(preview['available'])
            self.assertEqual(preview['url'], record['url'])
            self.assertEqual(self.catalog.journal(other['entryId'])['artifacts'], [])
            self.assertEqual(self.hashes(), before)
        with patch('observability_data.preview_available', return_value=False):
            preview, = self.catalog.journal(item['entryId'])['artifacts']
            self.assertFalse(preview['available'])
            self.assertNotIn('url', preview)

    def test_cycle_preview_never_becomes_center_document_resource(self):
        row = self.cycle()
        record = self.preview(cycle_id=row['cycleId'])
        # Even an extraneous file path cannot turn a preview into a document.
        self.write('projects/one/app.html', '<script>application()</script>')
        from runtime_artifacts import save
        record['path'] = 'projects/one/app.html'
        save(self.root, record)
        with patch('observability_data.preview_available', return_value=True):
            item, = self.import_root()
            snapshot = self.catalog.journal(item['entryId'])
            preview, = snapshot['artifacts']
            self.assertEqual(preview['associationStatus'], 'bound')
            self.assertEqual(preview['url'], record['url'])
            self.assertEqual(snapshot['cycles'][0]['artifacts'][0]['url'], record['url'])
            with self.assertRaises(CenterError) as context:
                self.catalog.resource(item['entryId'], 'artifact-' + record['id'], item['sourceId'])
            self.assertEqual(context.exception.code, 'RESOURCE_NOT_FOUND')

    def test_operator_preview_requires_current_identity_marker(self):
        row = self.cycle()
        self.preview()
        with patch('observability_data.preview_available', return_value=True):
            item, = self.import_root()
        (self.root / 'projects/one/.autonomous-company/identity.json').unlink()
        replacement = products.register_project(self.root, 'projects/one')
        self.assertNotEqual(replacement['id'], row['productId'])
        with patch('observability_data.preview_available', return_value=True) as health:
            self.assertEqual(self.catalog.journal(item['entryId'])['artifacts'], [])
            health.assert_not_called()

    def test_operator_preview_uses_explicit_source_without_fallback(self):
        self.cycle()
        self.preview()
        with patch('observability_data.preview_available', return_value=True):
            original, = self.import_root()
            backup = self.base / 'backup'
            shutil.copytree(self.root, backup)
            record_file, = (backup / 'logs/artifacts').glob('*.json')
            record = json.loads(record_file.read_text())
            record['url'] = 'http://127.0.0.1:23456/'
            record_file.write_text(json.dumps(record))
            copy, = self.import_root(backup)
            self.assertEqual(copy['entryId'], original['entryId'])
            original_preview, = self.catalog.journal(original['entryId'], {'sourceId': original['sourceId']})['artifacts']
            copy_preview, = self.catalog.journal(original['entryId'], {'sourceId': copy['sourceId']})['artifacts']
            self.assertEqual(original_preview['url'], 'http://127.0.0.1:12345/')
            self.assertEqual(copy_preview['url'], 'http://127.0.0.1:23456/')

    def test_missing_product_directory_keeps_identity_history(self):
        row = self.cycle()
        item, = self.import_root()
        (self.root / 'projects/one').rename(self.root / 'projects/gone')
        data = self.catalog.journal(item['entryId'])
        self.assertEqual(data['cycles'][0]['stableProductId'], row['productId'])
        self.assertEqual(data['project']['status'], 'historical')

    def test_usage_period_does_not_silently_return_all(self):
        self.cycle()
        item, = self.import_root()
        usage = self.catalog.usage(item['entryId'], {'period': 'day', 'date': '2025-01-01'})
        self.assertIsNone(usage['usage']['totalTokens'])
        self.assertEqual(usage['recorded'], 0)
        with self.assertRaises(CenterError):
            self.catalog.usage(item['entryId'], {'period': 'month'})

    def test_runtime_terminal_vocabulary_allows_archive(self):
        self.cycle()
        item, = self.import_root()
        with self.store.transaction() as tx:
            for state in ('ended', 'canceled'):
                tx.put('requests', state, {'entryId': item['entryId'], 'state': state})
        archived = self.catalog.entry_action(item['entryId'], 'archive', {'expectedRevision': 1})
        self.assertTrue(archived['archived'])

    def test_uncertain_binding_cannot_be_hidden_by_detach(self):
        self.cycle()
        item, = self.import_root()
        with self.store.transaction() as tx:
            tx.put('operations', 'uncertain', {'entryId': item['entryId'], 'kind': 'takeover', 'state': 'attention'})
        with self.assertRaises(CenterError) as context:
            self.catalog.entry_action(item['entryId'], 'detach', {'expectedRevision': 1})
        self.assertEqual(context.exception.code, 'ENTRY_BUSY')

    def test_preparing_entry_null_metadata_is_searchable_and_sortable(self):
        with self.store.transaction() as tx:
            tx.put('entries', 'preparing', {'entryId': 'preparing', 'kind': 'exploration', 'displayName': None,
                                          'description': None, 'revision': 1, 'preferredSourceId': None})
        self.assertEqual(self.catalog.list_entries({'filter': 'all', 'sort': 'name'})['total'], 1)
        self.assertEqual(self.catalog.list_entries({'filter': 'all', 'q': 'example'})['total'], 0)

    def test_source_only_reference_is_explicit_readonly_and_content_verified(self):
        self.write('README.md', '# Reference only\n')
        before = self.hashes()
        with self.assertRaises(CenterError):
            self.catalog.probe({'root': str(self.root)})
        candidate = self.catalog.probe({'root': str(self.root), 'kindHint': 'reference'})
        item, = self.catalog.commit({**candidate, 'idempotencyKey': 'reference-import'})['items']
        self.assertEqual(self.catalog.list_entries()['total'], 0)
        reference = self.catalog.list_entries({'filter': 'reference'})['items'][0]
        self.assertEqual(reference['displayName'], self.root.name)
        self.assertIsNone(reference['productId'])
        self.assertFalse(reference['capabilities']['execute'])
        self.assertEqual(self.catalog.resource(item['entryId'], 'reference-readme')[0], (self.root / 'README.md').read_bytes())
        self.assertEqual(self.hashes(), before)
        self.write('README.md', '# Changed reference\n')
        with self.assertRaises(CenterError) as context:
            self.catalog.resource(item['entryId'], 'reference-readme')
        self.assertEqual(context.exception.code, 'SOURCE_CHANGED')

    def test_registered_root_discovers_new_product_without_merging_history(self):
        original = self.cycle()
        old_item, = self.import_root()
        self.catalog.refresh_changed_sources()
        new_product = self.cycle('projects/two', 'new-product', 91)
        before = self.hashes()
        self.catalog.refresh_changed_sources()
        entries = self.catalog.list_entries()['items']
        self.assertEqual(len(entries), 2)
        discovered = next(row for row in entries if row['productId'] == new_product['productId'])
        self.assertIsNone(discovered['runtimeId'])
        self.assertFalse(discovered['capabilities']['execute'])
        self.assertEqual(self.catalog.usage(old_item['entryId'])['usage']['totalTokens'], 13)
        self.assertEqual(self.catalog.usage(discovered['entryId'])['usage']['totalTokens'], 91)
        self.assertEqual(self.hashes(), before)
        self.catalog.entry_action(discovered['entryId'], 'detach', {'expectedRevision': discovered['revision']})
        self.cycle(attempt='trigger-another-refresh')
        self.catalog.refresh_changed_sources()
        self.assertEqual(self.catalog.list_entries()['total'], 1)

    def test_discovery_waits_for_committed_identity_and_matching_marker(self):
        self.cycle()
        self.import_root()
        self.catalog.refresh_changed_sources()
        self.write('projects/metadata-only/.autonomous-company-project.json', '{"displayName":"not a product"}')
        self.catalog.refresh_changed_sources()
        self.assertEqual(self.catalog.list_entries()['total'], 1)
        new_product = self.cycle('projects/two', 'second')
        pending = self.write('.autonomous-company/product-state.transaction.json', '{"synthetic":"pending"}')
        self.catalog.refresh_changed_sources()
        self.assertEqual(self.catalog.list_entries()['total'], 1)
        pending.unlink()
        marker = self.root / 'projects/two/.autonomous-company/identity.json'
        marker.unlink()
        self.catalog.refresh_changed_sources()
        self.assertEqual(self.catalog.list_entries()['total'], 1)
        marker.write_text(json.dumps({'schemaVersion': 1, 'id': new_product['productId']}))
        self.write('.autonomous-company/product-state.lock/fixture', 'busy')
        self.catalog.refresh_changed_sources()
        self.assertEqual(self.catalog.list_entries()['total'], 1)
        (self.root / '.autonomous-company/product-state.lock/fixture').unlink()
        (self.root / '.autonomous-company/product-state.lock').rmdir()
        self.catalog.refresh_changed_sources()
        self.assertEqual(self.catalog.list_entries()['total'], 2)

    def test_language_period_is_not_a_stable_product_identity(self):
        from localization import start_product, next_product
        row = products.reserve_cycle(self.root, '', 'explore', 1, 'fixture', 'no-model')
        (self.root / 'projects/created').mkdir(parents=True)
        product = products.register_project(self.root, 'projects/created', row['cycleId'])
        products.update_cycle(self.root, row['cycleId'], 'completed')
        self.write('.autonomous-company.local', 'AUTONOMOUS_COMPANY_LANGUAGE=en\n')
        original_language = start_product(self.root)
        ledger = (self.root / '.autonomous-company/product-state.json').read_bytes()
        marker = (self.root / 'projects/created/.autonomous-company/identity.json').read_bytes()
        settings = (self.root / '.autonomous-company.local').read_text().replace('AUTONOMOUS_COMPANY_LANGUAGE=en', 'AUTONOMOUS_COMPANY_LANGUAGE=zh-CN')
        self.write('.autonomous-company.local', settings)
        next_language = next_product(self.root, 'NEXT')
        self.assertNotEqual(original_language['productId'], next_language['productId'])
        self.assertEqual(next_language['language'], 'zh-CN')
        self.assertEqual((self.root / '.autonomous-company/product-state.json').read_bytes(), ledger)
        self.assertEqual((self.root / 'projects/created/.autonomous-company/identity.json').read_bytes(), marker)
        self.import_root()
        item = next(item for item in self.catalog.list_entries()['items'] if item['productId'] == product['id'])
        before = self.hashes()
        language = self.catalog.journal(item['entryId'])['languageState']
        self.assertIsNone(language['productLanguage'])
        self.assertEqual(language['productLanguageStatus'], 'unknown')
        self.assertEqual(self.hashes(), before)

    def test_actual_language_evidence_is_scoped_and_survives_root_period_change(self):
        one = self.cycle()
        two = self.cycle('projects/two', 'second')
        at = '2026-09-26T01:00:00+00:00'
        def context(row, project, language):
            return {'version': 1, 'cycleId': row['cycleId'], 'project': project, 'source': 'runtime_context', 'recordedAt': at,
                    'languageEvidence': {'schemaVersion': 1, 'productId': row['productId'], 'cycleId': row['cycleId'],
                                         'language': language, 'languagePeriodId': 'a' * 32, 'recordedAt': at}}
        self.write('logs/' + one['cycleId'] + '.context.json', json.dumps(context(one, 'projects/one', 'en')))
        self.write('logs/' + two['cycleId'] + '.context.json', json.dumps(context(two, 'projects/two', 'zh-CN')))
        self.write('.autonomous-company.local', 'AUTONOMOUS_COMPANY_LANGUAGE=zh-CN\nAUTONOMOUS_COMPANY_PRODUCT_LANGUAGE=zh-CN\nAUTONOMOUS_COMPANY_PRODUCT_STATUS=active\n')
        self.import_root()
        items = self.catalog.list_entries()['items']
        item = next(item for item in items if item['productId'] == one['productId'])
        self.assertEqual(item['productLanguage'], 'en')
        before = self.hashes()
        snapshot = self.catalog.journal(item['entryId'])
        self.assertEqual(snapshot['languageState']['productLanguage'], 'en')
        self.assertEqual(snapshot['languageState']['productLanguageStatus'], 'recorded')
        self.assertEqual(snapshot['cycles'][0]['projectIdentity']['status'], 'recorded')
        self.assertEqual(self.hashes(), before)
        newer = self.cycle(attempt='newer')
        foreign = context(newer, 'projects/one', 'zh-CN')
        foreign['languageEvidence']['productId'] = two['productId']
        self.write('logs/' + newer['cycleId'] + '.context.json', json.dumps(foreign))
        self.assertEqual(self.catalog.journal(item['entryId'])['languageState']['productLanguage'], 'en')
        (self.root / 'projects/one').rename(self.root / 'projects/moved')
        products.relocate_identity(self.root, one['productId'], 'projects/moved')
        self.assertEqual(self.catalog.journal(item['entryId'])['languageState']['productLanguage'], 'en')

    def test_catalog_thumbnail_is_verified_cached_scoped_and_invalidated(self):
        from product_media import capture_product
        from test_product_media import MediaFixture
        one = self.cycle()
        two = self.cycle('projects/two', 'second')
        self.write('projects/one/index.html', '<!doctype html><title>Thumbnail fixture</title>')
        with patch('product_media.run_worker', side_effect=MediaFixture().unit_worker):
            capture_product(self.root, 'projects/one', one['cycleId'])
        before = self.hashes()
        self.import_root()
        with patch('center_catalog.JournalSource.snapshot', side_effect=AssertionError('list must use cache')):
            entries = self.catalog.list_entries()['items']
        item = next(row for row in entries if row['productId'] == one['productId'])
        other = next(row for row in entries if row['productId'] == two['productId'])
        self.assertIn('/resources/' + item['thumbnailResourceId'], item['thumbnailUrl'])
        self.assertIsNone(other['thumbnailUrl'])
        self.assertTrue(self.catalog.resource(item['entryId'], item['thumbnailResourceId'], item['sourceId'])[0].startswith(b'\x89PNG'))
        with self.assertRaises(CenterError):
            self.catalog.resource(other['entryId'], item['thumbnailResourceId'], item['sourceId'])
        self.assertEqual(self.hashes(), before)
        self.catalog.refresh_changed_sources()
        self.write('logs/product-media/' + one['productId'] + '/' + item['thumbnailResourceId'][6:], 'changed')
        self.catalog.refresh_changed_sources()
        self.assertIsNone(self.catalog.get_entry(item['entryId'])['thumbnailUrl'])

    def test_catalog_icon_is_verified_cached_and_source_scoped(self):
        from unittest.mock import patch
        one = self.cycle()
        two = self.cycle('projects/two', 'second')
        raw = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="24" fill="#123456"/></svg>'
        digest = hashlib.sha256(raw).hexdigest()
        folder = 'logs/product-media/' + one['productId'] + '/'
        self.write(folder + digest + '.svg', raw.decode())
        self.write(folder + 'media.json', json.dumps({'version': 1, 'productId': one['productId'], 'icon': {'name': digest + '.svg', 'sha256': digest}}))
        self.import_root()
        with patch('center_catalog.JournalSource.snapshot', side_effect=AssertionError('list must use cache')):
            entries = self.catalog.list_entries()['items']
        item = next(item for item in entries if item['productId'] == one['productId'])
        other = next(item for item in entries if item['productId'] == two['productId'])
        self.assertEqual(item['iconUrl'], '/api/center/v1/entries/' + item['entryId'] + '/resources/media-' + digest + '.svg?sourceId=' + item['sourceId'])
        self.assertIsNone(other['iconUrl'])
        self.assertEqual(self.catalog.resource(item['entryId'], 'media-' + digest + '.svg', item['sourceId'])[0], raw)
        with self.assertRaises(CenterError):
            self.catalog.resource(other['entryId'], 'media-' + digest + '.svg', item['sourceId'])
        self.catalog.refresh_changed_sources()
        self.write(folder + digest + '.svg', 'changed')
        self.catalog.refresh_changed_sources()
        self.assertIsNone(self.catalog.get_entry(item['entryId'])['iconUrl'])

    def catalog_snapshot(self):
        with self.store.transaction() as tx:
            records = {kind: tx.list(kind) for kind in ('entries', 'sources', 'candidates', 'events', 'operations', 'requests', 'runtimes', 'idempotency')}
        return self.store.revision, records, self.hashes()

    def test_entry_actions_reject_noninteger_revisions_without_mutation(self):
        self.cycle()
        item, = self.import_root()
        for action in ('archive', 'restore', 'detach', 'source-selection'):
            for value in (True, 1.0, False, '1', [], {}, 1e100, -1, 2**100):
                before = self.catalog_snapshot()
                with self.assertRaises(CenterError) as error:
                    self.catalog.entry_action(item['entryId'], action, {'expectedRevision': value, 'sourceId': item['sourceId']})
                self.assertEqual((error.exception.code, error.exception.status), ('INVALID_REQUEST', 400), (action, value))
                self.assertEqual(self.catalog_snapshot(), before, (action, value))

    def test_entry_revision_conflicts_and_valid_integers_keep_existing_contract(self):
        self.cycle()
        item, = self.import_root()
        for body in ({}, {'expectedRevision': None}, {'expectedRevision': 0}, {'expectedRevision': 2}):
            before = self.catalog_snapshot()
            with self.assertRaises(CenterError) as error:
                self.catalog.entry_action(item['entryId'], 'archive', body)
            self.assertEqual(error.exception.code, 'REVISION_CONFLICT', body)
            self.assertEqual(self.catalog_snapshot(), before)
        archived = self.catalog.entry_action(item['entryId'], 'archive', {'expectedRevision': 1})
        self.assertTrue(archived['archived'])
        self.assertEqual(archived['revision'], 2)
        before = self.catalog_snapshot()
        with self.assertRaises(CenterError) as error:
            self.catalog.entry_action(item['entryId'], 'restore', {'expectedRevision': 1})
        self.assertEqual(error.exception.code, 'REVISION_CONFLICT')
        self.assertEqual(self.catalog_snapshot(), before)
        restored = self.catalog.entry_action(item['entryId'], 'restore', {'expectedRevision': 2})
        self.assertFalse(restored['archived'])
        self.assertEqual(restored['revision'], 3)
        selected = self.catalog.entry_action(item['entryId'], 'source-selection', {'expectedRevision': 3, 'sourceId': item['sourceId']})
        self.assertEqual(selected['preferredSourceId'], item['sourceId'])
        self.assertEqual(selected['revision'], 4)
        detached = self.catalog.entry_action(item['entryId'], 'detach', {'expectedRevision': 4})
        self.assertTrue(detached['detached'])
        self.assertEqual(detached['revision'], 5)

    def test_reconnect_rejects_noninteger_revisions_without_catalog_or_audit_writes(self):
        self.cycle()
        item, = self.import_root()
        backup = self.base / 'moved'
        shutil.copytree(self.root, backup)
        candidate = self.catalog.probe({'root': str(backup)})
        base_body = {'candidateId': candidate['candidateId'], 'candidateHash': candidate['candidateHash'], 'idempotencyKey': 'revision-guard'}
        for value in (True, 1.0, False, '1', [], {}, 1e100, -1, 2**100):
            before = self.catalog_snapshot()
            with self.assertRaises(CenterError) as error:
                self.catalog.reconnect(item['sourceId'], {**base_body, 'expectedRevision': value})
            self.assertEqual((error.exception.code, error.exception.status), ('INVALID_REQUEST', 400), value)
            self.assertEqual(self.catalog_snapshot(), before, value)
        # Rejected input did not reserve the key; correcting it can succeed.
        result = self.catalog.reconnect(item['sourceId'], {**base_body, 'expectedRevision': 1})
        self.assertEqual(result['root'], str(backup.resolve()))

    def test_reconnect_required_revision_and_idempotent_replay_order_are_preserved(self):
        self.cycle()
        item, = self.import_root()
        backup = self.base / 'moved'
        shutil.copytree(self.root, backup)
        candidate = self.catalog.probe({'root': str(backup)})
        base_body = {'candidateId': candidate['candidateId'], 'candidateHash': candidate['candidateHash'], 'idempotencyKey': 'reconnect-replay'}
        for revision in ({}, {'expectedRevision': None}, {'expectedRevision': 0}, {'expectedRevision': 2}):
            before = self.catalog_snapshot()
            with self.assertRaises(CenterError) as error:
                self.catalog.reconnect(item['sourceId'], {**base_body, **revision})
            self.assertEqual(error.exception.code, 'REVISION_CONFLICT', revision)
            self.assertEqual(self.catalog_snapshot(), before)
        body = {**base_body, 'expectedRevision': 1}
        result = self.catalog.reconnect(item['sourceId'], body)
        before = self.catalog_snapshot()
        self.assertEqual(self.catalog.reconnect(item['sourceId'], body), result)
        self.assertEqual(self.catalog_snapshot(), before, 'valid replay must return before checking the now-stale revision')
        for value in (2, True):
            with self.assertRaises(CenterError) as error:
                self.catalog.reconnect(item['sourceId'], {**body, 'expectedRevision': value})
            self.assertEqual(error.exception.code, 'IDEMPOTENCY_CONFLICT', 'existing key/body mismatch keeps its earlier priority')
            self.assertEqual(self.catalog_snapshot(), before)

    def test_import_probe_kind_hint_rejects_wrong_shapes_without_writes(self):
        self.cycle()
        before = (self.store.revision, self.store._connection.execute('SELECT kind, id, body FROM records ORDER BY kind, id').fetchall(), self.hashes())
        for hint in ({}, [], True, 1.0, 'unsupported'):
            with self.assertRaises(CenterError) as error:
                self.catalog.probe({'root': str(self.root), 'kindHint': hint})
            self.assertEqual((error.exception.code, error.exception.status), ('INVALID_INPUT', 400), hint)
            self.assertEqual((self.store.revision, self.store._connection.execute('SELECT kind, id, body FROM records ORDER BY kind, id').fetchall(), self.hashes()), before)
        for hint in (None, 'reference'):
            self.assertTrue(self.catalog.probe({'root': str(self.root), 'kindHint': hint})['items'])

    def test_import_commit_rejects_enum_and_selection_shapes_without_writes(self):
        self.cycle()
        candidate = self.catalog.probe({'root': str(self.root)})
        identity = candidate['items'][0]['itemId']
        body = {'candidateId': candidate['candidateId'], 'candidateHash': candidate['candidateHash'], 'idempotencyKey': 'shape-retry'}
        before = (self.store.revision, self.store._connection.execute('SELECT kind, id, body FROM records ORDER BY kind, id').fetchall(), self.hashes())
        invalid = [('mode', value) for value in ({}, [], None, True, 1.0, 'unsupported')]
        invalid += [('itemIds', value) for value in ([{}], [[]], [identity, {}], [None], [True], [1], [], None, identity, ['unknown'])]
        for field, value in invalid:
            with self.assertRaises(CenterError) as error:
                self.catalog.commit({**body, field: value})
            self.assertEqual((error.exception.code, error.exception.status), ('INVALID_INPUT', 400), (field, value))
            self.assertEqual((self.store.revision, self.store._connection.execute('SELECT kind, id, body FROM records ORDER BY kind, id').fetchall(), self.hashes()), before)
        self.assertEqual(len(self.catalog.commit(body)['items']), 1, 'invalid requests did not consume the idempotency key')

    def test_import_valid_modes_selection_and_replays_keep_existing_contract(self):
        self.cycle()
        self.cycle('projects/two', 'second')
        candidate = self.catalog.probe({'root': str(self.root)})
        base = {'candidateId': candidate['candidateId'], 'candidateHash': candidate['candidateHash']}
        for index, mode in enumerate(({}, {'mode': 'readonly'}, {'mode': 'read_only'}, {'mode': 'reference'})):
            body = {**base, **mode, 'idempotencyKey': 'valid-mode-' + str(index)}
            result = self.catalog.commit(body)
            self.assertEqual(len(result['items']), 2, 'omitted selection keeps every inspected item')
            revision = self.store.revision
            self.assertEqual(self.catalog.commit(body), result)
            self.assertEqual(self.store.revision, revision)
        identity = candidate['items'][0]['itemId']
        result = self.catalog.commit({**base, 'idempotencyKey': 'valid-subset', 'itemIds': [identity, identity]})
        self.assertEqual(len(result['items']), 1, 'duplicate valid selections retain existing one-item behavior')


    def test_catalog_id_shapes_do_not_fall_back_or_bind_sqlite_parameters(self):
        self.cycle()
        item, = self.import_root()
        candidate = self.catalog.probe({'root': str(self.root)})
        body = {'candidateHash': candidate['candidateHash'], 'idempotencyKey': 'catalog-id-shapes', 'expectedRevision': 1}
        snapshot = lambda: (self.store.revision, self.store._connection.execute('SELECT kind, id, body FROM records ORDER BY kind, id').fetchall(), self.hashes())
        before = snapshot()
        for value in ({}, [], ['other'], True, False, 0, 1.0):
            for call in (lambda: self.catalog.resolve_source(value),
                         lambda: self.catalog.resolve_source(item['entryId'], value),
                         lambda: self.catalog.commit({**body, 'candidateId': value}),
                         lambda: self.catalog.reconnect(item['sourceId'], {**body, 'candidateId': value}),
                         lambda: self.catalog.entry_action(item['entryId'], 'source-selection', {'expectedRevision': 1, 'sourceId': value})):
                with self.assertRaises(CenterError) as error:
                    call()
                self.assertEqual((error.exception.code, error.exception.status), ('INVALID_INPUT', 400), value)
                self.assertEqual(snapshot(), before)

    def test_catalog_id_defaults_and_unknown_strings_keep_existing_rules(self):
        self.cycle()
        item, = self.import_root()
        for source_id in (None, '', item['sourceId']):
            self.assertEqual(self.catalog.resolve_source(item['entryId'], source_id)[1]['sourceId'], item['sourceId'])
        for identity in (None, '', 'unknown'):
            with self.assertRaises(CenterError) as error:
                self.catalog.resolve_source(identity)
            self.assertEqual(error.exception.code, 'ENTRY_NOT_FOUND')
            with self.assertRaises(CenterError) as error:
                self.catalog.commit({'candidateId': identity})
            self.assertEqual(error.exception.code, 'CANDIDATE_INVALID')
            with self.assertRaises(CenterError) as error:
                self.catalog.entry_action(item['entryId'], 'source-selection', {'expectedRevision': 1, 'sourceId': identity})
            self.assertEqual(error.exception.code, 'SOURCE_NOT_FOUND')
        with self.assertRaises(CenterError) as error:
            self.catalog.resolve_source(item['entryId'], 'unknown')
        self.assertEqual(error.exception.code, 'SOURCE_NOT_FOUND')
        selected = self.catalog.entry_action(item['entryId'], 'source-selection', {'expectedRevision': 1, 'sourceId': item['sourceId']})
        self.assertEqual(selected['preferredSourceId'], item['sourceId'])

    def test_idle_blocks_reserved_entry_operations_and_log_page_enforces_revision_and_domain(self):
        row = self.cycle()
        item, = self.import_root()
        with self.store.transaction() as tx:
            tx.put('operations', 'op-reserved', {'operationId': 'op-reserved', 'kind': 'exploration', 'state': 'preparing', 'reserved': {'entryId': item['entryId']}})
            with self.assertRaises(CenterError) as error:
                self.catalog._idle(tx, item['entryId'])
            self.assertEqual(error.exception.code, 'ENTRY_BUSY')

        first = self.catalog.log_page(item['entryId'], row['cycleId'], {'offset': 0, 'limit': 5})
        second = self.catalog.log_page(item['entryId'], row['cycleId'], {'offset': first['nextOffset'], 'limit': 128 * 1024, 'revision': first['revision']})
        self.assertTrue(second['eof'])
        self.assertEqual(first['bytesBase64'] and second['totalBytes'], len('projects/one private log'.encode('utf-8')))
        import base64
        decoded = base64.b64decode(first['bytesBase64']) + base64.b64decode(second['bytesBase64'])
        self.assertEqual(decoded.decode('utf-8'), 'projects/one private log')
        with self.assertRaises(CenterError) as changed:
            self.catalog.log_page(item['entryId'], row['cycleId'], {'offset': 0, 'limit': 5, 'revision': '0:0'})
        self.assertEqual(changed.exception.code, 'LOG_CHANGED')

        # Managed source uses execution_query and checks revision conflict consistently
        with self.store.transaction() as tx:
            src = tx.get('sources', item['sourceId'])
            src['runtimeId'] = 'runtime-log-test'
            tx.put('sources', item['sourceId'], src)
            tx.put('runtimes', 'runtime-log-test', {'runtimeId': 'runtime-log-test', 'managed': True})
        self.catalog.execution_query = lambda sid, q, **kw: {
            'ok': True, 'offset': 0, 'nextOffset': 4, 'totalBytes': 4, 'eof': True,
            'revision': '4:1', 'bytesBase64': base64.b64encode(b'test').decode('ascii'),
        }
        managed = self.catalog.log_page(item['entryId'], row['cycleId'], {'offset': 0, 'limit': 1024})
        self.assertEqual(managed['totalBytes'], 4)
        with self.assertRaises(CenterError) as conflict:
            self.catalog.log_page(item['entryId'], row['cycleId'], {'offset': 0, 'limit': 1024, 'revision': '9:9'})
        self.assertEqual(conflict.exception.code, 'LOG_CHANGED')



if __name__ == '__main__':
    unittest.main()
