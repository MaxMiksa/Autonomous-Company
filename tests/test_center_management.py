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

    def test_live_deletion_child_after_restart_preserves_in_progress_and_blocks_restore(self):
        entry, source = self.entry(managed=True)
        root = Path(source['root'])
        (root / '.autonomous-company-center.json').write_text(json.dumps({
            'centerId': self.store.center_id, 'entryId': entry['entryId'], 'sourceId': source['sourceId'],
            'runtimeId': source['runtimeId'], 'operationId': 'operation-abcdefgh', 'protocolVersion': 2,
        }), encoding='utf-8')
        trashed = self.management.entry_action(entry['entryId'], 'trash', {'confirm': True, 'expectedRevision': entry['revision']})
        with self.store.transaction() as tx:
            row = tx.get('entries', entry['entryId'])
            row['deletionInProgress'] = {'startedAt': '2026-10-05T10:00:00+00:00', 'instanceId': 'crashed-proc'}
            tx.put('entries', entry['entryId'], row)
        with patch.object(self.runtime.adapter, 'query', return_value={'quiescent': False}):
            restarted = CenterManagement(self.store, self.catalog, self.runtime)
            listing = restarted.trash()
            self.assertIn('deletionInProgress', listing['items'][0])
            self.assertNotIn('trashError', listing['items'][0])
            with self.assertRaises(CenterError) as err:
                restarted.entry_action(entry['entryId'], 'restore-trash', {'expectedRevision': trashed['revision']})
            self.assertEqual(err.exception.code, 'ACTION_IN_PROGRESS')

    def test_subtree_commit_post_scan_removal_and_merge_into_deleting_rejected(self):
        import shutil
        from product_identity import register_project

        # 1. Subtree commit under a deleting parent root must reject with ACTION_IN_PROGRESS.
        entry, source = self.entry(managed=True)
        parent_root = Path(source['root'])
        sub_root = parent_root / 'nested-copy'
        (sub_root / 'projects/p2/.git').mkdir(parents=True)
        (sub_root / 'projects/p2/README.md').write_text('# Sub\n', encoding='utf-8')
        register_project(sub_root, 'projects/p2')
        sub_cand = self.catalog.probe({'root': str(sub_root)})
        self.management.entry_action(entry['entryId'], 'trash', {'confirm': True, 'expectedRevision': entry['revision']})
        with self.store.transaction() as tx:
            row = tx.get('entries', entry['entryId'])
            row['deletionInProgress'] = {'startedAt': '2026-10-05T10:00:00+00:00', 'instanceId': 'deleting-parent'}
            tx.put('entries', entry['entryId'], row)
        with self.assertRaises(CenterError) as sub_err:
            self.catalog.commit({'candidateId': sub_cand['candidateId'], 'candidateHash': sub_cand['candidateHash']})
        self.assertEqual(sub_err.exception.code, 'ACTION_IN_PROGRESS')

        # 2. Commit after scanned directory is removed must reject with SOURCE_MISSING (preflight) or SOURCE_CHANGED (TOCTOU inside tx).
        vanished = self.base / 'vanished-ws'
        (vanished / 'projects/p3/.git').mkdir(parents=True)
        (vanished / 'projects/p3/README.md').write_text('# Vanished\n', encoding='utf-8')
        register_project(vanished, 'projects/p3')
        vanished_cand = self.catalog.probe({'root': str(vanished)})
        shutil.rmtree(vanished)
        with self.assertRaises(CenterError) as gone_err:
            self.catalog.commit({'candidateId': vanished_cand['candidateId'], 'candidateHash': vanished_cand['candidateHash']})
        self.assertEqual(gone_err.exception.code, 'SOURCE_MISSING')

        toctou = self.base / 'toctou-ws'
        (toctou / 'projects/p3t/.git').mkdir(parents=True)
        (toctou / 'projects/p3t/README.md').write_text('# TOCTOU\n', encoding='utf-8')
        register_project(toctou, 'projects/p3t')
        toctou_cand = self.catalog.probe({'root': str(toctou)})
        orig_candidate = self.catalog._candidate
        def delete_after_candidate(body):
            cand = orig_candidate(body)
            shutil.rmtree(toctou)
            return cand
        with patch.object(self.catalog, '_candidate', side_effect=delete_after_candidate):
            with self.assertRaises(CenterError) as toctou_err:
                self.catalog.commit({'candidateId': toctou_cand['candidateId'], 'candidateHash': toctou_cand['candidateHash']})
        self.assertEqual(toctou_err.exception.code, 'SOURCE_CHANGED')

        # 3. Merging an external copy into a deleting entry must reject with ACTION_IN_PROGRESS.
        orig_ws = self.base / 'orig-merge'
        (orig_ws / 'projects/pm/.git').mkdir(parents=True)
        (orig_ws / 'projects/pm/README.md').write_text('# Merge\n', encoding='utf-8')
        register_project(orig_ws, 'projects/pm')
        orig_cand = self.catalog.probe({'root': str(orig_ws)})
        orig_entry_id = self.catalog.commit({'candidateId': orig_cand['candidateId'], 'candidateHash': orig_cand['candidateHash']})['items'][0]['entryId']
        ext_copy = self.base / 'ext-merge'
        shutil.copytree(orig_ws, ext_copy)
        ext_cand = self.catalog.probe({'root': str(ext_copy)})
        with self.store.transaction() as tx:
            row = tx.get('entries', orig_entry_id)
            row['deletionInProgress'] = {'startedAt': '2026-10-05T10:00:00+00:00', 'instanceId': 'deleting-target'}
            tx.put('entries', orig_entry_id, row)
        with self.assertRaises(CenterError) as merge_err:
            self.catalog.commit({'candidateId': ext_cand['candidateId'], 'candidateHash': ext_cand['candidateHash']})
        self.assertEqual(merge_err.exception.code, 'ACTION_IN_PROGRESS')

    def test_delete_timeout_expired_clears_in_progress_and_records_delete_failed(self):
        import subprocess
        entry, source = self.entry(managed=True)
        root = Path(source['root'])
        (root / '.autonomous-company-center.json').write_text(json.dumps({
            'centerId': self.store.center_id, 'entryId': entry['entryId'], 'sourceId': source['sourceId'],
            'runtimeId': source['runtimeId'], 'operationId': 'operation-abcdefgh', 'protocolVersion': 2,
        }), encoding='utf-8')
        trashed = self.management.entry_action(entry['entryId'], 'trash', {'confirm': True, 'expectedRevision': entry['revision']})
        with patch.object(self.management, '_delete_directory', side_effect=subprocess.TimeoutExpired(['helper'], 30)):
            with self.assertRaises(CenterError) as err:
                self.management.entry_action(entry['entryId'], 'delete', {'confirmPermanent': True, 'expectedRevision': trashed['revision']})
        self.assertEqual(err.exception.code, 'DELETE_FAILED')
        with self.store.transaction() as tx:
            saved = tx.get('entries', entry['entryId'])
            self.assertNotIn('deletionInProgress', saved)
            self.assertFalse(saved.get('detached'))
            self.assertEqual(saved['trashError']['code'], 'DELETE_FAILED')

    def test_live_prelock_helper_receipt_preserves_deletion_in_progress_and_missing_dir_cleanup_recovers(self):
        import zipfile
        import center_directory_delete as cdd
        entry, source = self.entry(managed=True)
        root = Path(source['root'])
        rid = source['runtimeId']
        marker = {
            'centerId': self.store.center_id, 'entryId': entry['entryId'], 'sourceId': source['sourceId'],
            'runtimeId': rid, 'operationId': 'operation-abcdefgh', 'protocolVersion': 2,
        }
        (root / '.autonomous-company-center.json').write_text(json.dumps(marker), encoding='utf-8')
        trashed = self.management.entry_action(entry['entryId'], 'trash', {'confirm': True, 'expectedRevision': entry['revision']})
        receipt_path = self.store.data_dir / 'deletion-receipts' / f'{rid}.json'
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        with self.store.transaction() as tx:
            row = tx.get('entries', entry['entryId'])
            row['deletionInProgress'] = {'startedAt': '2026-10-05T10:00:00+00:00', 'instanceId': 'crashed-proc'}
            tx.put('entries', entry['entryId'], row)

        # 1. Pre-lock preparing receipt with live PID preserves deletionInProgress even if preflight returns quiescent.
        receipt_path.write_text(json.dumps({
            'marker': {k: marker[k] for k in ('centerId', 'runtimeId', 'entryId', 'sourceId', 'operationId')},
            'state': 'preparing', 'stage': 'preflight', 'pid': os.getpid(), 'processStart': cdd._process_start(os.getpid()),
        }), encoding='utf-8')
        restarted = CenterManagement(self.store, self.catalog, self.runtime)
        with patch.object(self.runtime.adapter, 'query', return_value={'quiescent': True}):
            listing = restarted.trash()
        self.assertIn('deletionInProgress', listing['items'][0])

        # 2. Missing dir after cleanupStarted with dead helper recovers to DELETE_INTERRUPTED and retries cleanly.
        evidence_path = self.store.data_dir / 'deletion-evidence' / f'{rid}.zip'
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(evidence_path, 'w') as zf:
            zf.writestr('.autonomous-company-center.json', json.dumps(marker))
        import shutil
        shutil.rmtree(root)
        receipt_path.write_text(json.dumps({
            'marker': {k: marker[k] for k in ('centerId', 'runtimeId', 'entryId', 'sourceId', 'operationId')},
            'fullMarker': marker, 'root': str(root), 'cleanupStarted': True, 'state': 'deleting',
            'stage': 'remove_root', 'pid': 99999999, 'processStart': 'dead-start', 'evidence': str(evidence_path),
        }), encoding='utf-8')
        listing2 = restarted.trash()
        self.assertNotIn('deletionInProgress', listing2['items'][0])
        self.assertEqual(listing2['items'][0]['trashError']['code'], 'DELETE_INTERRUPTED')
        with patch.object(self.management, '_delete_directory', return_value=str(evidence_path)):
            with patch.object(restarted, '_delete_directory', return_value=str(evidence_path)):
                result = restarted.entry_action(entry['entryId'], 'delete', {
                    'confirmPermanent': True, 'expectedRevision': listing2['items'][0]['revision'],
                })
        self.assertTrue(result['detached'])

    def test_registered_subdirectory_blocks_parent_deletion_with_shared_runtime(self):
        entry, source = self.entry(managed=True)
        parent_root = Path(source['root'])
        sub_dir = parent_root / 'nested-registered'
        sub_dir.mkdir(parents=True, exist_ok=True)
        with self.store.transaction() as tx:
            tx.put('sources', 'source-child-sub', {
                'sourceId': 'source-child-sub', 'entryId': 'entry-other-sub', 'root': str(sub_dir),
                'revision': 1, 'sourceRevision': 1, 'availability': 'available', 'detached': False,
            })
        trashed = self.management.entry_action(entry['entryId'], 'trash', {'confirm': True, 'expectedRevision': entry['revision']})
        with self.assertRaises(CenterError) as err:
            self.management.entry_action(entry['entryId'], 'delete', {'confirmPermanent': True, 'expectedRevision': trashed['revision']})
        self.assertEqual(err.exception.code, 'SHARED_RUNTIME')
        self.assertTrue(parent_root.is_dir())

    def test_historical_removed_product_imports_and_reconnect_during_deletion_rejected(self):
        import shutil
        from product_identity import register_project

        # Historical removed product dir absent at probe time still commits cleanly.
        hist_ws = self.base / 'hist-ws'
        (hist_ws / 'projects/removed-prod/.git').mkdir(parents=True)
        (hist_ws / 'projects/removed-prod/README.md').write_text('# Old\n', encoding='utf-8')
        register_project(hist_ws, 'projects/removed-prod')
        shutil.rmtree(hist_ws / 'projects/removed-prod')
        cand = self.catalog.probe({'root': str(hist_ws)})
        self.assertEqual(cand['items'][0].get('projectDirPresent'), False)
        committed = self.catalog.commit({'candidateId': cand['candidateId'], 'candidateHash': cand['candidateHash']})
        self.assertEqual(len(committed['items']), 1)

        # reconnect during deletionInProgress must be rejected with ACTION_IN_PROGRESS.
        reloc_ws = self.base / 'reloc-ws'
        (reloc_ws / 'projects/pm/.git').mkdir(parents=True)
        (reloc_ws / 'projects/pm/README.md').write_text('# Reloc\n', encoding='utf-8')
        register_project(reloc_ws, 'projects/pm')
        rcand = self.catalog.probe({'root': str(reloc_ws)})
        rcommit = self.catalog.commit({'candidateId': rcand['candidateId'], 'candidateHash': rcand['candidateHash']})['items'][0]
        reloc_copy = self.base / 'reloc-copy'
        shutil.copytree(reloc_ws, reloc_copy)
        rcopy_cand = self.catalog.probe({'root': str(reloc_copy)})
        with self.store.transaction() as tx:
            row = tx.get('entries', rcommit['entryId'])
            row['deletionInProgress'] = {'startedAt': '2026-10-05T10:00:00+00:00', 'instanceId': 'del-proc'}
            tx.put('entries', rcommit['entryId'], row)
        with self.assertRaises(CenterError) as rec_err:
            self.catalog.reconnect(rcommit['sourceId'], {
                'candidateId': rcopy_cand['candidateId'],
                'candidateHash': rcopy_cand['candidateHash'],
                'expectedRevision': 1,
            })
        self.assertEqual(rec_err.exception.code, 'ACTION_IN_PROGRESS')

    def test_retry_delete_after_succeeded_receipt_is_idempotent(self):
        import shutil
        entry, source = self.entry(managed=True)
        rid = source['runtimeId']
        root = Path(source['root'])
        trashed = self.management.entry_action(entry['entryId'], 'trash', {'confirm': True, 'expectedRevision': entry['revision']})
        evidence_path = self.store.data_dir / 'deletion-evidence' / f'{rid}.zip'
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_bytes(b'PK\x05\x06' + b'\x00' * 18)
        shutil.rmtree(root)
        receipt_path = self.store.data_dir / 'deletion-receipts' / f'{rid}.json'
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps({
            'state': 'succeeded', 'filesDeleted': True, 'evidence': str(evidence_path),
        }), encoding='utf-8')
        with self.store.transaction() as tx:
            row = tx.get('entries', entry['entryId'])
            row['deletionInProgress'] = {'startedAt': '2026-10-05T10:00:00+00:00', 'instanceId': 'crashed-proc'}
            tx.put('entries', entry['entryId'], row)
        restarted = CenterManagement(self.store, self.catalog, self.runtime)
        retried = restarted.entry_action(entry['entryId'], 'delete', {
            'confirmPermanent': True, 'expectedRevision': trashed['revision'],
        })
        self.assertTrue(retried['detached'])


if __name__ == '__main__':
    unittest.main()
