"""Management boundaries: rename, recycle bin, disposal provenance and retained evidence."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(os.environ.get('AUTONOMOUS_COMPANY_TEST_SOURCE', Path(__file__).resolve().parents[1]))
_git_rev = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True)
FRAMEWORK_REVISION = _git_rev.stdout.strip() if _git_rev.returncode == 0 and len(_git_rev.stdout.strip()) == 40 else 'a' * 40
sys.path[:0] = [str(ROOT / 'dashboard'), str(ROOT / 'scripts/core')]
from center_store import CenterStore, CenterError  # noqa: E402
from center_catalog import CenterCatalog  # noqa: E402
from center_management import CenterManagement  # noqa: E402


class ManagementTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.store = CenterStore(self.base / 'center')
        self.addCleanup(self.store.close)
        self.catalog = CenterCatalog(self.store)
        self.invalidated = []
        self.adapter = SimpleNamespace(available=True, domain={}, query=lambda *args, **kwargs: {'quiescent': True})
        self.runtime = SimpleNamespace(
            adapter=self.adapter,
            framework_root=ROOT,
            _invalidate_capability_cache=lambda runtime_id=None: self.invalidated.append(runtime_id),
        )
        self.management = CenterManagement(self.store, self.catalog, self.runtime)

    def entry(self, entry_id='entry-abcdefgh', managed=False):
        runtime_id, source_id = 'runtime-abcdefgh', 'source-abcdefgh'
        root = self.store.data_dir / 'runtimes' / runtime_id if managed else self.base / entry_id
        root.mkdir(parents=True, exist_ok=True)
        (root / 'README.md').write_text('original external files', encoding='utf-8')
        entry = dict(entryId=entry_id, kind='exploration', preferredSourceId=source_id, revision=1, archived=False,
                     detached=False, displayName='Autonomous Company', description='', createdAt='2026-10-05T10:00:00+00:00')
        source = dict(sourceId=source_id, entryId=entry_id, root=str(root), revision=1, sourceRevision=1,
                      availability='available', capabilities={'execute': managed}, runtimeId=runtime_id if managed else None)
        with self.store.transaction() as tx:
            tx.put('entries', entry_id, entry)
            tx.put('sources', source_id, source)
            tx.put('operations', 'operation-abcdefgh', dict(
                operationId='operation-abcdefgh', kind='exploration', state='succeeded',
                createdAt=entry['createdAt'], input={'direction': 'Traceable research workspace'},
                frameworkRevision=FRAMEWORK_REVISION, reserved={'entryId': entry_id, 'runtimeId': runtime_id, 'sourceId': source_id},
            ))
            if managed:
                runtime = dict(runtimeId=runtime_id, entryId=entry_id, sourceId=source_id, centerId=self.store.center_id,
                               root=str(root), managed=True, frameworkRevision=FRAMEWORK_REVISION)
                tx.put('runtimes', runtime_id, runtime)
        if managed:
            (root / '.autonomous-company-center.json').write_text(
                json.dumps({**runtime, 'protocolVersion': 2, 'operationId': 'operation-abcdefgh'}),
                encoding='utf-8',
            )
        return entry, source

    def test_rename_overrides_display_name_and_checks_revision(self):
        entry, _ = self.entry()
        renamed = self.management.entry_action(entry['entryId'], 'rename', {'expectedRevision': 1, 'displayName': 'Curated Product'})
        self.assertEqual(renamed['displayName'], 'Curated Product')
        self.assertEqual(renamed['revision'], 2)
        with self.assertRaises(CenterError) as conflict:
            self.management.entry_action(entry['entryId'], 'rename', {'expectedRevision': 1, 'displayName': 'Stale'})
        self.assertEqual(conflict.exception.code, 'REVISION_CONFLICT')

    def test_trash_retention_restore_keeps_identity_without_request(self):
        entry, _ = self.entry()
        removed = self.management.entry_action(entry['entryId'], 'trash', {'expectedRevision': 1, 'confirm': True})
        self.assertEqual(self.catalog.list_entries({'filter': 'all'})['total'], 0)
        self.assertEqual(self.catalog.list_entries({'filter': 'trash'})['items'][0]['entryId'], entry['entryId'])
        self.assertEqual(self.management.trash()['items'][0]['entryId'], entry['entryId'])
        self.management.retention({'expectedRevision': 1, 'retentionDays': 14})
        with self.store.transaction() as tx:
            removed = tx.get('entries', entry['entryId'])
        duration = datetime.fromisoformat(removed['expiresAt']) - datetime.fromisoformat(removed['trashedAt'])
        self.assertEqual(duration, timedelta(days=14))
        restored = self.management.entry_action(entry['entryId'], 'restore-trash', {'expectedRevision': removed['revision']})
        self.assertFalse(restored['archived'])
        self.assertEqual(restored['entryId'], entry['entryId'])
        with self.store.transaction() as tx:
            self.assertEqual(tx.list('requests'), [])

    def test_expired_external_registration_removed_files_and_history_preserved(self):
        entry, source = self.entry()
        removed = self.management.entry_action(entry['entryId'], 'trash', {'expectedRevision': 1, 'confirm': True})
        with self.store.transaction() as tx:
            row = tx.get('entries', entry['entryId'])
            row['expiresAt'] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            tx.put('entries', entry['entryId'], row)
        self.assertTrue(self.management.sweep_trash(force=True)['items'][0]['ok'])
        self.assertEqual((Path(source['root']) / 'README.md').read_text(encoding='utf-8'), 'original external files')
        with self.store.transaction() as tx:
            detached = tx.get('entries', entry['entryId'])
            self.assertTrue(detached['detached'])
            self.assertTrue(tx.list('operations'))
            self.assertEqual(detached['deletionScope'], 'center_registration')

    def test_active_request_or_preparation_prevents_trash(self):
        entry, source = self.entry()
        with self.store.transaction() as tx:
            tx.put('requests', 'request-test', {'entryId': entry['entryId'], 'state': 'queued'})
        with self.assertRaisesRegex(CenterError, 'open request'):
            self.management.entry_action(entry['entryId'], 'trash', {'expectedRevision': 1, 'confirm': True})
        self.assertTrue(Path(source['root']).is_dir())
        with self.store.transaction() as tx:
            tx.delete('requests', 'request-test')
            tx.put('operations', 'op-prep', {'operationId': 'op-prep', 'kind': 'exploration', 'state': 'preparing', 'reserved': {'entryId': entry['entryId']}})
        with self.assertRaisesRegex(CenterError, 'active operation'):
            self.management.entry_action(entry['entryId'], 'trash', {'expectedRevision': 1, 'confirm': True})

    def test_existing_partial_source_error_remains_in_trash_after_delete_failure(self):
        entry, _ = self.entry(managed=True)
        removed = self.management.entry_action(entry['entryId'], 'trash', {'expectedRevision': 1, 'confirm': True})
        with patch.object(self.management, '_delete_directory', side_effect=CenterError('DELETE_FAILED', 'retained failure', 409)):
            with self.assertRaises(CenterError):
                self.management.entry_action(entry['entryId'], 'delete', {'expectedRevision': removed['revision'], 'confirmPermanent': True})
        with self.store.transaction() as tx:
            retained = tx.get('entries', entry['entryId'])
            self.assertFalse(retained['detached'])
            self.assertTrue(retained['trashed'])
            self.assertEqual(retained['trashError']['code'], 'DELETE_FAILED')

    def test_managed_source_alias_or_wrong_marker_cannot_delete_files(self):
        entry, source = self.entry(managed=True)
        marker = Path(source['root']) / '.autonomous-company-center.json'
        data = json.loads(marker.read_text(encoding='utf-8'))
        data['sourceId'] = 'source-wrong'
        marker.write_text(json.dumps(data), encoding='utf-8')
        with self.store.transaction() as tx:
            with self.assertRaises(CenterError) as error:
                self.management._owned_directory(tx, entry, source)
            self.assertEqual(error.exception.code, 'OWNER_CONFLICT')

    def test_disposal_framework_revision_comes_from_creation_record_not_request_body(self):
        entry, _ = self.entry(managed=True)
        with patch.object(self.runtime.adapter, 'query', return_value={'quiescent': True}) as query:
            self.management.entry_action(entry['entryId'], 'trash', {
                'expectedRevision': 1, 'confirm': True, 'expectedFrameworkRevision': 'f' * 40,
            })
            self.assertEqual(query.call_args.args[0], 'disposal-preflight')
            self.assertEqual(query.call_args.kwargs['expected_framework_revision'], FRAMEWORK_REVISION)

    def test_unmatched_creation_framework_record_blocks_disposal(self):
        entry, _ = self.entry(managed=True)
        with self.store.transaction() as tx:
            operation = tx.get('operations', 'operation-abcdefgh')
            operation['frameworkRevision'] = 'f' * 40
            tx.put('operations', 'operation-abcdefgh', operation)
        with self.assertRaises(CenterError) as error:
            self.management.entry_action(entry['entryId'], 'trash', {'expectedRevision': 1, 'confirm': True})
        self.assertEqual(error.exception.code, 'FRAMEWORK_PROVENANCE_UNVERIFIED')

    def test_owned_root_or_ancestor_link_never_grants_delete_ownership(self):
        entry, source = self.entry(managed=True)
        target = Path(source['root'])
        original = self.base / 'preserved-original'
        for ancestor in (False, True):
            with self.subTest(ancestor=ancestor):
                linked = target.parent if ancestor else target
                linked.rename(original)
                if os.name == 'nt':
                    quoted_link, quoted_original = str(linked).replace("'", "''"), str(original).replace("'", "''")
                    subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                                    f"New-Item -ItemType Junction -Path '{quoted_link}' -Target '{quoted_original}' | Out-Null"],
                                   check=True, capture_output=True)
                else:
                    linked.symlink_to(original, target_is_directory=True)
                try:
                    with self.store.transaction() as tx:
                        with self.assertRaises(CenterError) as error:
                            self.management._owned_directory(tx, entry, source)
                    self.assertEqual(error.exception.code, 'UNSAFE_SOURCE')
                    preserved = original / target.name if ancestor else original
                    self.assertEqual((preserved / 'README.md').read_text(encoding='utf-8'), 'original external files')
                finally:
                    linked.rmdir() if os.name == 'nt' else linked.unlink()
                    original.rename(linked)

    def test_shared_canonical_path_alias_blocks_directory_disposal(self):
        entry, source = self.entry(managed=True)
        with self.store.transaction() as tx:
            other = {**source, 'sourceId': 'source-other', 'entryId': 'entry-other', 'runtimeId': None,
                     'root': str(Path(source['root']) / '..' / Path(source['root']).name)}
            tx.put('sources', other['sourceId'], other)
            with self.assertRaises(CenterError) as error:
                self.management._owned_directory(tx, entry, source)
            self.assertEqual(error.exception.code, 'SHARED_RUNTIME')
        self.assertTrue(Path(source['root']).exists())

    def test_partial_file_deletion_cannot_be_restored_as_intact_project(self):
        entry, _ = self.entry()
        with self.store.transaction() as tx:
            entry.update(trashed=True, partialDeletion=True)
            tx.put('entries', entry['entryId'], entry)
        with self.assertRaises(CenterError) as error:
            self.management.entry_action(entry['entryId'], 'restore-trash', {'expectedRevision': 1})
        self.assertEqual(error.exception.code, 'PARTIAL_DELETE')


@unittest.skipUnless(sys.platform == 'linux', 'POSIX runtime locks require Linux/WSL')
class DeleteLockTests(unittest.TestCase):
    def test_receipt_and_intent_writes_never_follow_preexisting_links(self):
        import center_directory_delete as deletion
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / 'center'
            data.mkdir()
            outside = Path(temporary) / 'outside.json'
            outside.write_text('untouched', encoding='utf-8')
            receipt = data / 'receipt.json'
            receipt.with_name(receipt.name + '.' + str(os.getpid()) + '.tmp').symlink_to(outside)
            deletion.atomic_json(receipt, {'state': 'safe'})
            self.assertEqual(outside.read_text(encoding='utf-8'), 'untouched')
            receipt.unlink()
            receipt.symlink_to(outside)
            with self.assertRaises(ValueError):
                deletion.atomic_json(receipt, {'state': 'unsafe'})
            store = CenterStore(data / 'records')
            try:
                manager = CenterManagement(store, None, None)
                folder = store.data_dir / 'deletion-intents'
                folder.mkdir()
                path = folder / 'runtime-abcdefgh.json'
                path.symlink_to(outside)
                with self.assertRaises(CenterError):
                    manager._write_intent('runtime-abcdefgh', {'unsafe': True})
                self.assertEqual(outside.read_text(encoding='utf-8'), 'untouched')
                path.unlink()
                folder.rmdir()
                folder.symlink_to(outside.parent, target_is_directory=True)
                with self.assertRaises(CenterError):
                    manager._write_intent('runtime-abcdefgh', {'unsafe': True})
                folder.unlink()
                saved = manager._write_intent('runtime-abcdefgh', {'safe': True})
                self.assertEqual(json.loads(saved.read_text(encoding='utf-8')), {'safe': True})
            finally:
                store.close()

    def test_delete_uses_original_execution_lock_preserves_evidence_and_receipt(self):
        import center_directory_delete as deletion
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary)
            marker = dict(centerId='center-abcdefgh', entryId='entry-abcdefgh', sourceId='source-abcdefgh',
                          runtimeId='runtime-abcdefgh', operationId='operation-abcdefgh', protocolVersion=2)
            root = data / 'runtimes' / marker['runtimeId']
            root.mkdir(parents=True)
            (root / '.autonomous-company-center.json').write_text(json.dumps(marker), encoding='utf-8')
            (root / 'logs').mkdir()
            (root / 'logs/failure.log').write_text('original error evidence', encoding='utf-8')
            manifest = {'dataDir': str(data), 'root': str(root),
                        'marker': {key: marker[key] for key in marker if key != 'protocolVersion'},
                        'expectedFrameworkRevision': FRAMEWORK_REVISION}
            with patch.object(deletion, 'disposal_preflight', return_value={'quiescent': True}), \
                 patch.object(deletion, 'disposal_provenance', return_value={'frameworkRevision': FRAMEWORK_REVISION, 'marker': marker}), \
                 patch.dict(os.environ, {'XDG_STATE_HOME': str(data / 'owners')}):
                with deletion.execution_lock(marker):
                    with self.assertRaises(BlockingIOError):
                        deletion.delete_runtime(manifest)
                self.assertTrue(root.is_dir())
                result = deletion.delete_runtime(manifest)
                self.assertEqual(deletion.delete_runtime(manifest), result)
            self.assertTrue(result['filesDeleted'])
            self.assertFalse(root.exists())
            import zipfile
            with zipfile.ZipFile(result['evidence']) as evidence:
                self.assertEqual(evidence.read('logs/failure.log'), b'original error evidence')


class DeleteConcurrencyTests(ManagementTests):
    def test_delete_releases_mutex_and_rejects_concurrent_actions_while_in_progress(self):
        import threading
        entry, source = self.entry(managed=True)
        root = Path(source['root'])
        (root / '.autonomous-company-center.json').write_text(json.dumps({
            'centerId': self.store.center_id, 'entryId': entry['entryId'], 'sourceId': source['sourceId'],
            'runtimeId': source['runtimeId'], 'operationId': 'operation-abcdefgh', 'protocolVersion': 2,
        }), encoding='utf-8')
        trashed = self.management.entry_action(entry['entryId'], 'trash', {'confirm': True, 'expectedRevision': entry['revision']})
        entered, release = threading.Event(), threading.Event()
        evidence_zip = str(self.store.data_dir / 'deletion-evidence' / (source['runtimeId'] + '.zip'))

        def slow_delete_dir(target, src, ent, fw_rev):
            entered.set()
            release.wait(timeout=5)
            return evidence_zip

        results = []

        def run_delete():
            results.append(self.management.entry_action(
                entry['entryId'], 'delete',
                {'confirmPermanent': True, 'expectedRevision': trashed['revision']}
            ))

        with patch.object(self.management, '_delete_directory', side_effect=slow_delete_dir):
            worker = threading.Thread(target=run_delete)
            worker.start()
            self.assertTrue(entered.wait(timeout=5))
            # While _delete_directory runs without holding the store lock, unrelated store reads succeed
            # and concurrent actions / sweep_trash on the deleting entry are safely blocked.
            with self.assertRaises(CenterError) as err:
                self.management.entry_action(entry['entryId'], 'delete', {'confirmPermanent': True, 'expectedRevision': trashed['revision'] + 1})
            self.assertEqual(err.exception.code, 'ACTION_IN_PROGRESS')
            with self.store.transaction() as tx:
                self.assertTrue(tx.get('entries', entry['entryId']).get('deletionInProgress'))
            release.set()
            worker.join(timeout=5)
        self.assertTrue(results and results[0]['detached'])

    def test_delete_failure_clears_in_progress_and_records_delete_failed(self):
        entry, source = self.entry(managed=True)
        root = Path(source['root'])
        (root / '.autonomous-company-center.json').write_text(json.dumps({
            'centerId': self.store.center_id, 'entryId': entry['entryId'], 'sourceId': source['sourceId'],
            'runtimeId': source['runtimeId'], 'operationId': 'operation-abcdefgh', 'protocolVersion': 2,
        }), encoding='utf-8')
        trashed = self.management.entry_action(entry['entryId'], 'trash', {'confirm': True, 'expectedRevision': entry['revision']})
        with patch.object(self.management, '_delete_directory', side_effect=CenterError('DELETE_FAILED', 'boom', 409)):
            with self.assertRaises(CenterError) as err:
                self.management.entry_action(entry['entryId'], 'delete', {'confirmPermanent': True, 'expectedRevision': trashed['revision']})
        self.assertEqual(err.exception.code, 'DELETE_FAILED')
        with self.store.transaction() as tx:
            saved = tx.get('entries', entry['entryId'])
            self.assertNotIn('deletionInProgress', saved)
            self.assertFalse(saved.get('detached'))
            self.assertEqual(saved['trashError']['code'], 'DELETE_FAILED')

    def test_stale_deletion_recovers_after_restart_for_manual_sweep_and_already_deleted_receipt(self):
        entry, source = self.entry(managed=True)
        root = Path(source['root'])
        marker = {
            'centerId': self.store.center_id, 'entryId': entry['entryId'], 'sourceId': source['sourceId'],
            'runtimeId': source['runtimeId'], 'operationId': 'operation-abcdefgh', 'protocolVersion': 2,
        }
        (root / '.autonomous-company-center.json').write_text(json.dumps(marker), encoding='utf-8')
        trashed = self.management.entry_action(entry['entryId'], 'trash', {'confirm': True, 'expectedRevision': entry['revision']})
        # Simulate crashed prior process leaving stale deletionInProgress.
        with self.store.transaction() as tx:
            row = tx.get('entries', entry['entryId'])
            row['deletionInProgress'] = {'startedAt': '2026-10-05T10:00:00+00:00', 'instanceId': 'crashed-proc'}
            row['expiresAt'] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            tx.put('entries', entry['entryId'], row)
        restarted = CenterManagement(self.store, self.catalog, self.runtime)
        listing = restarted.trash()
        self.assertEqual(listing['items'][0]['trashError']['code'], 'DELETE_INTERRUPTED')
        self.assertNotIn('deletionInProgress', listing['items'][0])
        evidence_zip = str(self.store.data_dir / 'deletion-evidence' / (source['runtimeId'] + '.zip'))
        with patch.object(restarted, '_delete_directory', return_value=evidence_zip):
            swept = restarted.sweep_trash(force=True)
            self.assertTrue(swept['items'][0]['ok'])

        # If disk deletion had already written succeeded receipt and removed dir before crash, trash() finalizes detach.
        entry2_id = 'entry-receiptdone'
        rid2, sid2 = 'runtime-receiptdone', 'source-receiptdone'
        root2 = self.store.data_dir / 'runtimes' / rid2
        root2.mkdir(parents=True, exist_ok=True)
        (root2 / '.autonomous-company-center.json').write_text(json.dumps({
            'centerId': self.store.center_id, 'entryId': entry2_id, 'sourceId': sid2,
            'runtimeId': rid2, 'operationId': 'op-receiptdone', 'protocolVersion': 2,
        }), encoding='utf-8')
        with self.store.transaction() as tx:
            tx.put('entries', entry2_id, dict(entryId=entry2_id, kind='exploration', preferredSourceId=sid2,
                                              revision=1, trashed=True, trashedAt='2026-10-05T10:00:00+00:00',
                                              archived=True, detached=False,
                                              deletionInProgress={'startedAt': '2026-10-05T10:00:00+00:00', 'instanceId': 'dead'}))
            tx.put('sources', sid2, dict(sourceId=sid2, entryId=entry2_id, runtimeId=rid2, root=str(root2), revision=1))
            tx.put('runtimes', rid2, dict(runtimeId=rid2, entryId=entry2_id, sourceId=sid2, centerId=self.store.center_id,
                                          root=str(root2), managed=True, frameworkRevision=FRAMEWORK_REVISION))
        import shutil
        shutil.rmtree(root2)
        receipts_dir = self.store.data_dir / 'deletion-receipts'
        receipts_dir.mkdir(exist_ok=True)
        (receipts_dir / f'{rid2}.json').write_text(json.dumps({
            'state': 'succeeded', 'filesDeleted': True, 'evidence': str(self.store.data_dir / 'deletion-evidence' / f'{rid2}.zip'),
        }), encoding='utf-8')
        restarted2 = CenterManagement(self.store, self.catalog, self.runtime)
        self.assertEqual([item['entryId'] for item in restarted2.trash()['items']], [])
        with self.store.transaction() as tx:
            self.assertTrue(tx.get('entries', entry2_id)['detached'])

    def test_in_flight_delete_blocks_discovery_and_commit_and_runs_preflight_lock_free(self):
        import threading
        entry, source = self.entry(managed=True)
        root = Path(source['root'])
        (root / 'projects/p1/.git').mkdir(parents=True)
        (root / 'projects/p1/README.md').write_text('# Demo\n', encoding='utf-8')
        from product_identity import register_project
        register_project(root, 'projects/p1')
        (root / '.autonomous-company-center.json').write_text(json.dumps({
            'centerId': self.store.center_id, 'entryId': entry['entryId'], 'sourceId': source['sourceId'],
            'runtimeId': source['runtimeId'], 'operationId': 'operation-abcdefgh', 'protocolVersion': 2,
        }), encoding='utf-8')
        trashed = self.management.entry_action(entry['entryId'], 'trash', {'confirm': True, 'expectedRevision': entry['revision']})
        preflight_entered, preflight_release = threading.Event(), threading.Event()
        evidence_zip = str(self.store.data_dir / 'deletion-evidence' / (source['runtimeId'] + '.zip'))

        def slow_preflight(*args, **kwargs):
            preflight_entered.set()
            preflight_release.wait(timeout=5)
            return {'quiescent': True}

        candidate = self.catalog.probe({'root': str(root)})
        anchor = {**source, 'root': str(root)}
        with patch.object(self.runtime.adapter, 'query', side_effect=slow_preflight), \
             patch.object(self.management, '_delete_directory', return_value=evidence_zip):
            worker = threading.Thread(target=lambda: self.management.entry_action(
                entry['entryId'], 'delete', {'confirmPermanent': True, 'expectedRevision': trashed['revision']}
            ))
            worker.start()
            self.assertTrue(preflight_entered.wait(timeout=5))
            # While slow adapter preflight runs lock-free, DB transactions succeed and registration/discovery block.
            self.assertEqual(self.catalog._discover_products(anchor), [])
            with self.assertRaises(CenterError) as err:
                self.catalog.commit({'candidateId': candidate['candidateId'], 'candidateHash': candidate['candidateHash']})
            self.assertEqual(err.exception.code, 'ACTION_IN_PROGRESS')
            preflight_release.set()
            worker.join(timeout=5)

    def test_retention_rejects_mismatched_center_id(self):
        with self.assertRaises(CenterError) as err:
            self.management.retention({'retentionDays': 7, 'expectedRevision': 1, 'expectedCenterId': 'wrong-center'})
        self.assertEqual(err.exception.code, 'REVISION_CONFLICT')


if __name__ == '__main__':
    unittest.main()
