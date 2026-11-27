"""Catalog organization and reversible removal; imported files remain untouched."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import os
import re
import subprocess
import tempfile
import threading
import time

from center_catalog import now, uid, root_path
from center_store import CenterError

MARKER = '.autonomous-company-center.json'


def linked_path(path):
    if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
        return True
    try:
        return bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400)
    except FileNotFoundError:
        return False


class CenterManagement:
    def __init__(self, store, catalog, runtime):
        self.store, self.catalog, self.runtime = store, catalog, runtime
        self._maintenance_lock = threading.Lock()
        self._active_lock = threading.Lock()
        self._active_deletions = set()
        self._instance_id = uid('mgmt')
        self._last_sweep = 0

    @staticmethod
    def _expected(body, record):
        if body.get('expectedRevision') != record.get('revision'):
            raise CenterError('REVISION_CONFLICT', 'This item changed; reload it.', 409)

    @staticmethod
    def _name(value):
        if not isinstance(value, str) or not value.strip() or len(value) > 80 or any(ord(c) < 32 for c in value):
            raise CenterError('INVALID_NAME', 'Use a name of 1 to 80 characters.')
        return value.strip()

    def _invalidate_runtime(self, runtime_id=None):
        invalidate = getattr(self.runtime, '_invalidate_capability_cache', None)
        if callable(invalidate):
            invalidate(runtime_id)

    def _is_live_deletion(self, entry):
        token = entry.get('deletionInProgress')
        if not token:
            return False
        with self._active_lock:
            return (isinstance(token, dict) and token.get('instanceId') == self._instance_id
                    and entry['entryId'] in self._active_deletions)

    def _finalize_detached(self, tx, entry, *, deletion_scope, evidence, sources=None):
        entry_id = entry['entryId']
        deleted_at = now()
        entry.update(detached=True, deletedAt=deleted_at, deletionEvidence=evidence,
                     deletionScope=deletion_scope, revision=entry['revision'] + 1)
        entry.pop('deletionInProgress', None)
        entry.pop('deletionTargetRoots', None)
        entry.pop('trashError', None)
        if sources is None:
            sources = [row for row in tx.list('sources') if row['entryId'] == entry_id and not row.get('detached')]
        for source in sources:
            source.update(detached=True, deletedAt=deleted_at, revision=source.get('revision', 0) + 1)
            tx.put('sources', source['sourceId'], source)
        self._event(tx, entry_id, 'delete', deletionScope=deletion_scope, deletionEvidence=evidence)
        tx.put('entries', entry_id, entry)

    def _record_delete_failure(self, tx, entry, code, message, *, event_action='delete_failed', bump_revision=True):
        entry_id = entry['entryId']
        receipts = [self._delete_receipt(row['runtimeId']) for row in tx.list('sources')
                    if row['entryId'] == entry_id and row.get('runtimeId')]
        entry.update(trashError={'code': code, 'message': message, 'at': now()},
                     partialDeletion=any(row.get('rootMoved') or row.get('cleanupStarted') for row in receipts) or any(
                         (self.store.data_dir / 'trash-files' / row['runtimeId']).exists() for row in tx.list('sources')
                         if row['entryId'] == entry_id and row.get('runtimeId')),
                     deletionReceipts=receipts,
                     deletionEvidence=[row['evidence'] for row in receipts if row.get('evidence')])
        if bump_revision:
            entry['revision'] += 1
        self._event(tx, entry_id, event_action, errorCode=code, deletionReceipts=receipts)
        tx.put('entries', entry_id, entry)

    def _reconcile_stale_deletion(self, tx, entry, *, bump_revision=True):
        if not entry.get('deletionInProgress') or self._is_live_deletion(entry):
            return False
        entry.pop('deletionInProgress', None)
        entry.pop('deletionTargetRoots', None)
        sources = [row for row in tx.list('sources') if row['entryId'] == entry['entryId'] and not row.get('detached')]
        owned_runtime_ids = []
        for source in sources:
            rid = source.get('runtimeId')
            if not rid:
                continue
            runtime = tx.get('runtimes', rid)
            expected = self.store.data_dir / 'runtimes' / rid
            if runtime and runtime.get('managed') and Path(source['root']) == expected and runtime.get('root') == source['root']:
                owned_runtime_ids.append((rid, expected))
        if owned_runtime_ids:
            receipts = []
            all_deleted = True
            for rid, expected in owned_runtime_ids:
                receipt = self._delete_receipt(rid)
                receipts.append(receipt)
                if (expected.exists() or (self.store.data_dir / 'trash-files' / rid).exists()
                        or receipt.get('state') != 'succeeded' or not receipt.get('filesDeleted')):
                    all_deleted = False
                    break
            if all_deleted:
                evidence = [r['evidence'] for r in receipts if r.get('evidence')]
                self._finalize_detached(tx, entry, deletion_scope='managed_files', evidence=evidence, sources=sources)
                return True
        self._record_delete_failure(
            tx, entry, 'DELETE_INTERRUPTED',
            'Previous deletion was interrupted; retry permanent deletion.',
            event_action='delete_interrupted', bump_revision=bump_revision,
        )
        return False

    def trash(self):
        with self.store.transaction() as tx:
            for row in tx.list('entries'):
                if row.get('trashed') and not row.get('detached') and row.get('deletionInProgress') and not self._is_live_deletion(row):
                    self._reconcile_stale_deletion(tx, row, bump_revision=True)
            settings = tx.get('management', 'trash') or {'retentionDays': 30, 'revision': 1}
            entries = [self.catalog._entry_view(tx, row) for row in tx.list('entries')
                       if row.get('trashed') and not row.get('detached')]
        return {**settings, 'items': sorted(entries, key=lambda row: row.get('trashedAt', ''), reverse=True)}

    def retention(self, body):
        days = body.get('retentionDays')
        if type(days) is not int or not 1 <= days <= 3650:
            raise CenterError('INVALID_RETENTION', 'Retention must be 1 to 3650 days.')
        expected_center = body.get('expectedCenterId')
        if expected_center is not None and not isinstance(expected_center, str):
            raise CenterError('INVALID_REQUEST', 'Center ID must be a string.')
        if expected_center is not None and expected_center != self.store.center_id:
            raise CenterError('REVISION_CONFLICT', 'Center changed; reload it.', 409)
        with self.store.transaction() as tx:
            settings = tx.get('management', 'trash') or {'retentionDays': 30, 'revision': 1}
            self._expected(body, settings)
            settings.update(retentionDays=days, revision=settings['revision'] + 1)
            tx.put('management', 'trash', settings)
            # Apply the new setting to existing items as well as future removals.
            for entry in tx.list('entries'):
                if entry.get('trashed') and not entry.get('detached'):
                    entry.update(expiresAt=(datetime.fromisoformat(entry['trashedAt']) + timedelta(days=days)).isoformat(),
                                 revision=entry['revision'] + 1)
                    tx.put('entries', entry['entryId'], entry)
            return settings

    def _idle(self, tx, entry):
        self.catalog._idle(tx, entry['entryId'])
        sources = [row for row in tx.list('sources') if row['entryId'] == entry['entryId'] and not row.get('detached')]
        for source in sources:
            runtime = tx.get('runtimes', source.get('runtimeId')) if source.get('runtimeId') else None
            if runtime and runtime.get('managed'):
                if runtime.get('centerId') != self.store.center_id or runtime.get('entryId') != entry['entryId'] or runtime.get('sourceId') != source['sourceId']:
                    raise CenterError('OWNER_CONFLICT', 'Source ownership does not match this center.', 409)
                if not self.runtime.adapter.available:
                    raise CenterError('OWNERSHIP_UNCONFIRMED', 'Connect the execution domain to verify that the project has stopped.', 409)
                revision = self._disposal_provenance(tx, entry, source)
                check = (self.runtime.adapter.query('disposal-preflight', root=source['root'], center_id=self.store.center_id,
                                                    expected_framework_revision=revision)
                         if revision else self.runtime.adapter.query('preflight', root=source['root'], center_id=self.store.center_id,
                                                                    allow_protected='1', require_context='0'))
                receipt = self._delete_receipt(source['runtimeId'])
                recovery = ((not Path(source['root']).exists() or receipt.get('cleanupStarted'))
                            and all(receipt.get('marker', {}).get(key) == value for key, value in {
                                'centerId': self.store.center_id, 'runtimeId': source['runtimeId'],
                                'entryId': entry['entryId'], 'sourceId': source['sourceId']}.items()))
                if not check.get('quiescent') and not entry.get('partialDeletion') and not recovery:
                    raise CenterError('ENTRY_BUSY', 'Source ownership or active processes require attention.', 409,
                                      {'reason': check.get('reason')})
        return sources

    def _disposal_provenance(self, tx, entry, source):
        runtime_id = source.get('runtimeId')
        runtime = tx.get('runtimes', runtime_id) if runtime_id else None
        if not runtime or not runtime.get('managed'):
            return None
        expected = self.store.data_dir / 'runtimes' / runtime_id
        if Path(source['root']) != expected or runtime.get('root') != source['root']:
            return None  # External takeovers retain their ordinary release gate.
        if any(runtime.get(key) != value for key, value in {'centerId': self.store.center_id, 'entryId': entry['entryId'],
                                                           'sourceId': source['sourceId'], 'runtimeId': runtime_id}.items()):
            raise CenterError('OWNER_CONFLICT', 'Original runtime ownership cannot be verified.', 409)
        marker_path = expected / MARKER
        marker = None
        if marker_path.exists():
            if linked_path(marker_path) or marker_path.stat().st_size > 65536:
                raise CenterError('OWNER_CONFLICT', 'Original runtime marker cannot be verified.', 409)
            marker = json.loads(marker_path.read_text(encoding='utf-8'))
        else:
            receipt = self._delete_receipt(runtime_id)
            if receipt.get('rootMoved') or receipt.get('cleanupStarted') or receipt.get('filesDeleted'):
                marker = receipt.get('fullMarker')
        if not marker or any(marker.get(key) != value for key, value in {'centerId': self.store.center_id,
                               'entryId': entry['entryId'], 'sourceId': source['sourceId'], 'runtimeId': runtime_id}.items()):
            raise CenterError('OWNER_CONFLICT', 'Original runtime marker cannot be verified.', 409)
        operation = tx.get('operations', marker.get('operationId'))
        revision = runtime.get('frameworkRevision')
        attempt = marker.get('preparationAttempt')
        if (not operation or operation.get('kind') != 'exploration' or not isinstance(revision, str)
                or not re.fullmatch(r'[0-9a-f]{40}', revision) or operation.get('frameworkRevision') != revision
                or attempt != runtime.get('preparationAttempt') or attempt != operation.get('preparationAttempt')
                or attempt is not None and (not isinstance(attempt, str) or not re.fullmatch(r'attempt_[0-9a-f]{32}', attempt))
                or any((operation.get('reserved') or {}).get(key) != value for key, value in {
                    'entryId': entry['entryId'], 'sourceId': source['sourceId'], 'runtimeId': runtime_id}.items())):
            raise CenterError('FRAMEWORK_PROVENANCE_UNVERIFIED', 'The original framework version and creation record cannot be verified.', 409)
        return revision

    def entry_action(self, entry_id, action, body):
        if action == 'delete':
            return self._delete(entry_id, body)
        with self.catalog._source_refresh_lock, self.store.transaction() as tx:
            entry = tx.get('entries', entry_id)
            if not entry or entry.get('detached'):
                raise CenterError('ENTRY_NOT_FOUND', 'Entry is unavailable.', 404)
            if self._is_live_deletion(entry):
                raise CenterError('ACTION_IN_PROGRESS', 'Permanent deletion is already in progress.', 409)
            self._expected(body, entry)
            if entry.get('deletionInProgress'):
                if self._reconcile_stale_deletion(tx, entry, bump_revision=False):
                    raise CenterError('ENTRY_NOT_FOUND', 'Entry is unavailable.', 404)
            if action == 'rename':
                entry['customDisplayName'] = self._name(body.get('displayName'))
            elif action == 'trash':
                if body.get('confirm') is not True:
                    raise CenterError('CONFIRMATION_REQUIRED', 'Confirm moving this project to the recycle bin.', 409)
                self._idle(tx, entry)
                if entry.get('trashed'):
                    raise CenterError('ENTRY_TRASHED', 'Entry is already in the recycle bin.', 409)
                settings = tx.get('management', 'trash') or {'retentionDays': 30}
                stamp = datetime.now(timezone.utc)
                entry.update(trashed=True, trashedAt=stamp.isoformat(), archivedBeforeTrash=entry.get('archived', False),
                             archived=True, expiresAt=(stamp + timedelta(days=settings['retentionDays'])).isoformat())
            elif action == 'restore-trash':
                if not entry.get('trashed'):
                    raise CenterError('ENTRY_NOT_TRASHED', 'Entry is not in the recycle bin.', 409)
                if entry.get('partialDeletion'):
                    raise CenterError('PARTIAL_DELETE', 'File cleanup already began; retained evidence is available but the original directory cannot be restored.', 409)
                entry.update(trashed=False, archived=entry.pop('archivedBeforeTrash', False), restoredAt=now())
                for key in ('trashedAt', 'expiresAt', 'trashError'):
                    entry.pop(key, None)
            else:
                raise CenterError('INVALID_ACTION', 'Unsupported management action.')
            entry['revision'] += 1
            tx.put('entries', entry_id, entry)
            self._event(tx, entry_id, action)
            runtime_id = entry.get('runtimeId')
        self._invalidate_runtime(runtime_id)
        return self.catalog.get_entry(entry_id)

    @staticmethod
    def _event(tx, entry_id, action, **fields):
        event_id = uid('event')
        tx.put('events', event_id, {'eventId': event_id, 'entryId': entry_id, 'action': action,
                                    'actorKind': 'local_operator_intent', 'createdAt': now(), **fields})

    def _owned_directory(self, tx, entry, source):
        runtime_id = source.get('runtimeId')
        runtime = tx.get('runtimes', runtime_id) if runtime_id else None
        if not runtime or not runtime.get('managed'):
            return None
        expected_raw = self.store.data_dir / 'runtimes' / runtime_id
        if Path(source['root']) != expected_raw:
            return None
        for part in (expected_raw, *expected_raw.parents):
            if linked_path(part):
                raise CenterError('UNSAFE_SOURCE', 'Linked managed directories cannot be deleted.', 409)
        expected = expected_raw.resolve()
        expected.relative_to(self.store.data_dir)
        target = root_path(source['root']) if expected_raw.exists() else expected
        if target != expected or runtime.get('root') != source['root']:
            return None  # Taken-over external roots are never owned directories.
        receipt = self._delete_receipt(runtime_id)
        if not expected.exists() and not (self.store.data_dir / 'trash-files' / runtime_id).exists() and (receipt.get('rootMoved') or receipt.get('cleanupStarted') or receipt.get('filesDeleted')):
            marker = receipt.get('fullMarker', {})
            if any(marker.get(key) != value for key, value in {'centerId': self.store.center_id, 'runtimeId': runtime_id,
                                                             'entryId': entry['entryId'], 'sourceId': source['sourceId']}.items()):
                raise CenterError('OWNER_CONFLICT', 'Deletion receipt ownership cannot be verified.', 409)
            return expected
        marker_path = target / MARKER
        if not target.exists() and (entry.get('partialDeletion') or receipt.get('marker', {}).get('runtimeId') == runtime_id):
            marker_path = self.store.data_dir / 'trash-files' / runtime_id / MARKER
            target = marker_path.parent
        if linked_path(marker_path) or marker_path.is_file() and marker_path.stat().st_size > 65536:
            raise CenterError('OWNER_CONFLICT', 'Managed directory marker is unavailable.', 409)
        marker = json.loads(marker_path.read_text(encoding='utf-8')) if marker_path.is_file() else receipt.get('fullMarker', {})
        if any(marker.get(key) != value for key, value in {'centerId': self.store.center_id, 'runtimeId': runtime_id,
                                                           'entryId': entry['entryId'], 'sourceId': source['sourceId']}.items()):
            raise CenterError('OWNER_CONFLICT', 'Managed directory marker has changed.', 409)
        if not marker.get('operationId') or not any(row.get('kind') == 'exploration' and row.get('operationId') == marker['operationId']
                and all((row.get('reserved') or {}).get(key) == marker.get(key) for key in ('runtimeId', 'entryId', 'sourceId')) for row in tx.list('operations')):
            raise CenterError('OWNER_CONFLICT', 'This directory was not created by this center.', 409)
        if any(row.get('sourceId') != source['sourceId'] and not row.get('detached')
               and (row.get('runtimeId') == runtime_id or Path(row.get('root', '')).resolve() == expected) for row in tx.list('sources')):
            raise CenterError('SHARED_RUNTIME', 'Other registered projects still use this directory.', 409)
        # Never recurse through a linked directory during evidence capture or deletion.
        stack = [target]
        while stack:
            folder = stack.pop()
            for child in folder.iterdir():
                if linked_path(child):
                    raise CenterError('UNSAFE_SOURCE', 'Remove linked files before permanently deleting this directory.', 409)
                if child.is_dir():
                    stack.append(child)
        return expected

    def _delete_receipt(self, runtime_id):
        path = self.store.data_dir / 'deletion-receipts' / (runtime_id + '.json')
        for part in (path, *path.parents):
            if linked_path(part):
                raise CenterError('UNSAFE_SOURCE', 'Linked deletion receipts are unsupported.', 409)
        if path.is_file() and not linked_path(path) and path.stat().st_size <= 65536:
            return json.loads(path.read_text(encoding='utf-8'))
        return {}

    def _delete_directory(self, target, source, entry, framework_revision):
        adapter = self.runtime.adapter
        runtime_id = source['runtimeId']
        marker_path = target / MARKER
        if not target.exists():
            marker_path = self.store.data_dir / 'trash-files' / runtime_id / MARKER
        marker = json.loads(marker_path.read_text(encoding='utf-8')) if marker_path.is_file() else self._delete_receipt(runtime_id).get('fullMarker', {})
        manifest = {'dataDir': adapter.path(self.store.data_dir), 'root': adapter.path(target),
                    'expectedFrameworkRevision': framework_revision,
                    'marker': {key: marker[key] for key in ('centerId', 'runtimeId', 'entryId', 'sourceId', 'operationId')}}
        path = self._write_intent(runtime_id, manifest)
        command = ['python3', adapter.path(Path(self.runtime.framework_root) / 'dashboard/center_directory_delete.py'),
                   '--manifest', adapter.path(path)]
        if adapter.domain.get('platform') == 'wsl':
            command = adapter._wsl() + ['--exec', *command]
        try:
            result = json.loads(adapter._execute(command, timeout=180).stdout)
        except Exception as error:
            receipt = self._delete_receipt(runtime_id)
            stage = receipt.get('stage')
            message = ('File cleanup failed while removing this project directory; close programs using it and retry. The error and original evidence are retained.'
                       if receipt.get('errno') in {13, 16} else 'File cleanup could not be confirmed; its receipt and original evidence are retained.')
            raise CenterError('DELETE_FAILED', message, 409,
                              {'stage': stage, 'reason': receipt.get('reason'), 'errno': receipt.get('errno')}) from error
        if result.get('state') != 'succeeded' or not result.get('filesDeleted'):
            raise CenterError('DELETE_FAILED', 'File cleanup could not be confirmed.', 409)
        return str(self.store.data_dir / 'deletion-evidence' / (runtime_id + '.zip'))

    def _write_intent(self, runtime_id, manifest):
        folder = self.store.data_dir / 'deletion-intents'
        path = folder / (runtime_id + '.json')
        def check():
            try:
                path.resolve().relative_to(self.store.data_dir)
            except ValueError as error:
                raise CenterError('UNSAFE_SOURCE', 'Deletion intent must remain inside this center.', 409) from error
            for part in (path, *path.parents):
                if linked_path(part):
                    raise CenterError('UNSAFE_SOURCE', 'Linked deletion intents are unsupported.', 409)
        check()
        folder.mkdir(exist_ok=True)
        check()
        descriptor, name = tempfile.mkstemp(prefix='.intent-', suffix='.tmp', dir=folder)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                json.dump(manifest, stream, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            check()
            os.replace(temporary, path)
            return path
        finally:
            temporary.unlink(missing_ok=True)

    def _idle_db(self, tx, entry):
        self.catalog._idle(tx, entry['entryId'])
        sources = [row for row in tx.list('sources') if row['entryId'] == entry['entryId'] and not row.get('detached')]
        checks = []
        for source in sources:
            runtime = tx.get('runtimes', source.get('runtimeId')) if source.get('runtimeId') else None
            if runtime and runtime.get('managed'):
                if (runtime.get('centerId') != self.store.center_id or runtime.get('entryId') != entry['entryId']
                        or runtime.get('sourceId') != source['sourceId']):
                    raise CenterError('OWNER_CONFLICT', 'Source ownership does not match this center.', 409)
                if not self.runtime.adapter.available:
                    raise CenterError('OWNERSHIP_UNCONFIRMED', 'Connect the execution domain to verify that the project has stopped.', 409)
                checks.append((dict(source), dict(runtime)))
        return sources, checks

    def _verify_idle_io(self, entry, checks, fs_provenance):
        by_source = {item['source']['sourceId']: item.get('frameworkRevision') for item in fs_provenance}
        for source, _runtime in checks:
            revision = by_source.get(source['sourceId'])
            check = (self.runtime.adapter.query('disposal-preflight', root=source['root'], center_id=self.store.center_id,
                                                expected_framework_revision=revision)
                     if revision else self.runtime.adapter.query('preflight', root=source['root'], center_id=self.store.center_id,
                                                                allow_protected='1', require_context='0'))
            receipt = self._delete_receipt(source['runtimeId'])
            recovery = ((not Path(source['root']).exists() or receipt.get('cleanupStarted'))
                        and all(receipt.get('marker', {}).get(key) == value for key, value in {
                            'centerId': self.store.center_id, 'runtimeId': source['runtimeId'],
                            'entryId': entry['entryId'], 'sourceId': source['sourceId']}.items()))
            if not check.get('quiescent') and not entry.get('partialDeletion') and not recovery:
                raise CenterError('ENTRY_BUSY', 'Source ownership or active processes require attention.', 409,
                                  {'reason': check.get('reason')})

    def _owned_directory_db(self, tx, entry, source):
        runtime_id = source.get('runtimeId')
        runtime = tx.get('runtimes', runtime_id) if runtime_id else None
        if not runtime or not runtime.get('managed'):
            return None
        expected_raw = self.store.data_dir / 'runtimes' / runtime_id
        if Path(source['root']) != expected_raw or runtime.get('root') != source['root']:
            return None
        if any(runtime.get(key) != value for key, value in {'centerId': self.store.center_id, 'entryId': entry['entryId'],
                                                           'sourceId': source['sourceId'], 'runtimeId': runtime_id}.items()):
            raise CenterError('OWNER_CONFLICT', 'Original runtime ownership cannot be verified.', 409)
        expected = expected_raw.resolve()
        expected.relative_to(self.store.data_dir)
        if any(row.get('sourceId') != source['sourceId'] and not row.get('detached')
               and (row.get('runtimeId') == runtime_id or Path(row.get('root', '')).resolve() == expected) for row in tx.list('sources')):
            raise CenterError('SHARED_RUNTIME', 'Other registered projects still use this directory.', 409)
        revision = runtime.get('frameworkRevision')
        if not isinstance(revision, str) or not re.fullmatch(r'[0-9a-f]{40}', revision):
            raise CenterError('FRAMEWORK_PROVENANCE_UNVERIFIED', 'The original framework version and creation record cannot be verified.', 409)
        operations = [dict(row) for row in tx.list('operations') if row.get('kind') == 'exploration']
        return {'source': dict(source), 'runtime': dict(runtime), 'expectedRaw': expected_raw,
                'expected': expected, 'frameworkRevision': revision, 'operations': operations}

    def _verify_owned_directory_fs(self, entry, item):
        source, runtime = item['source'], item['runtime']
        runtime_id = source['runtimeId']
        expected_raw, expected = item['expectedRaw'], item['expected']
        for part in (expected_raw, *expected_raw.parents):
            if linked_path(part):
                raise CenterError('UNSAFE_SOURCE', 'Linked managed directories cannot be deleted.', 409)
        target = root_path(source['root']) if expected_raw.exists() else expected
        if target != expected:
            return None
        receipt = self._delete_receipt(runtime_id)
        if not expected.exists() and not (self.store.data_dir / 'trash-files' / runtime_id).exists() and (receipt.get('rootMoved') or receipt.get('cleanupStarted') or receipt.get('filesDeleted')):
            marker = receipt.get('fullMarker', {})
            if any(marker.get(key) != value for key, value in {'centerId': self.store.center_id, 'runtimeId': runtime_id,
                                                             'entryId': entry['entryId'], 'sourceId': source['sourceId']}.items()):
                raise CenterError('OWNER_CONFLICT', 'Deletion receipt ownership cannot be verified.', 409)
            return expected
        marker_path = expected / MARKER
        if not expected.exists() and (entry.get('partialDeletion') or receipt.get('marker', {}).get('runtimeId') == runtime_id):
            marker_path = self.store.data_dir / 'trash-files' / runtime_id / MARKER
            target = marker_path.parent
        if linked_path(marker_path) or marker_path.is_file() and marker_path.stat().st_size > 65536:
            raise CenterError('OWNER_CONFLICT', 'Managed directory marker is unavailable.', 409)
        marker = json.loads(marker_path.read_text(encoding='utf-8')) if marker_path.is_file() else receipt.get('fullMarker', {})
        if any(marker.get(key) != value for key, value in {'centerId': self.store.center_id, 'runtimeId': runtime_id,
                                                           'entryId': entry['entryId'], 'sourceId': source['sourceId']}.items()):
            raise CenterError('OWNER_CONFLICT', 'Managed directory marker has changed.', 409)
        operation = next((row for row in item['operations'] if row.get('operationId') == marker.get('operationId')
                          and all((row.get('reserved') or {}).get(key) == marker.get(key) for key in ('runtimeId', 'entryId', 'sourceId'))), None)
        if not operation:
            raise CenterError('OWNER_CONFLICT', 'This directory was not created by this center.', 409)
        attempt = marker.get('preparationAttempt')
        revision = item['frameworkRevision']
        if (operation.get('frameworkRevision') != revision
                or attempt != runtime.get('preparationAttempt') or attempt != operation.get('preparationAttempt')
                or attempt is not None and (not isinstance(attempt, str) or not re.fullmatch(r'attempt_[0-9a-f]{32}', attempt))):
            raise CenterError('FRAMEWORK_PROVENANCE_UNVERIFIED', 'The original framework version and creation record cannot be verified.', 409)
        stack = [target]
        while stack:
            folder = stack.pop()
            for child in folder.iterdir():
                if linked_path(child):
                    raise CenterError('UNSAFE_SOURCE', 'Remove linked files before permanently deleting this directory.', 409)
                if child.is_dir():
                    stack.append(child)
        return expected

    def _delete(self, entry_id, body):
        if body.get('confirmPermanent') is not True:
            raise CenterError('CONFIRMATION_REQUIRED', 'Confirm permanent deletion.', 409)
        failure = None
        runtime_ids = []
        owned_items = []
        idle_checks = []
        external_managed = False
        reserved = False
        entry_snapshot = None
        with self.catalog._source_refresh_lock, self.store.transaction() as tx:
            entry = tx.get('entries', entry_id)
            if not entry or entry.get('detached'):
                raise CenterError('ENTRY_NOT_FOUND', 'Entry is unavailable.', 404)
            if self._is_live_deletion(entry):
                raise CenterError('ACTION_IN_PROGRESS', 'Permanent deletion is already in progress.', 409)
            self._expected(body, entry)
            if entry.get('deletionInProgress'):
                if self._reconcile_stale_deletion(tx, entry, bump_revision=False):
                    detached_view = dict(entry)
                    runtime_ids = [row['runtimeId'] for row in tx.list('sources') if row['entryId'] == entry_id and row.get('runtimeId')]
                    reserved = False
                    entry_snapshot = detached_view
                elif not entry.get('trashed'):
                    raise CenterError('ENTRY_NOT_TRASHED', 'Move the project to the recycle bin before permanently deleting it.', 409)
            if not entry_snapshot:
                if not entry.get('trashed'):
                    raise CenterError('ENTRY_NOT_TRASHED', 'Move the project to the recycle bin before permanently deleting it.', 409)
                try:
                    sources, idle_checks = self._idle_db(tx, entry)
                    runtime_ids = [source['runtimeId'] for source in sources if source.get('runtimeId')]
                    for source in sources:
                        item = self._owned_directory_db(tx, entry, source)
                        if item is not None:
                            owned_items.append(item)
                        elif source.get('runtimeId') and (tx.get('runtimes', source['runtimeId']) or {}).get('managed'):
                            external_managed = True
                    if owned_items or idle_checks:
                        target_roots = sorted(
                            {str(item['expected']) for item in owned_items}
                            | {str(Path(s['root']).resolve()) for s in sources if s.get('root')}
                        )
                        with self._active_lock:
                            self._active_deletions.add(entry_id)
                        reserved = True
                        entry['deletionInProgress'] = {'startedAt': now(), 'instanceId': self._instance_id}
                        entry['deletionTargetRoots'] = target_roots
                        entry['revision'] += 1
                        tx.put('entries', entry_id, entry)
                        entry_snapshot = dict(entry)
                    elif external_managed:
                        raise CenterError('MANAGED_SOURCE', 'Release management of the external directory before removing its registration.', 409)
                    else:
                        self._finalize_detached(tx, entry, deletion_scope='center_registration', evidence=[], sources=sources)
                        entry_snapshot = dict(entry)
                except (CenterError, OSError, ValueError) as error:
                    failure = error if isinstance(error, CenterError) else CenterError('DELETE_FAILED', 'Directory cleanup failed; the recycle bin record is retained.', 409)
                    self._record_delete_failure(tx, entry, failure.code, failure.message)
        if reserved:
            evidence = []
            try:
                try:
                    for item in owned_items:
                        self._verify_owned_directory_fs(entry_snapshot, item)
                    self._verify_idle_io(entry_snapshot, idle_checks, owned_items)
                    if external_managed:
                        raise CenterError('MANAGED_SOURCE', 'Release management of the external directory before removing its registration.', 409)
                    for item in owned_items:
                        evidence.append(self._delete_directory(item['expected'], item['source'], entry_snapshot, item['frameworkRevision']))
                except (CenterError, OSError, ValueError) as error:
                    failure = error if isinstance(error, CenterError) else CenterError('DELETE_FAILED', 'Directory cleanup failed; the recycle bin record is retained.', 409)
                with self.catalog._source_refresh_lock, self.store.transaction() as tx:
                    entry = tx.get('entries', entry_id)
                    entry.pop('deletionInProgress', None)
                    entry.pop('deletionTargetRoots', None)
                    if failure is None:
                        scope = 'managed_files' if owned_items else 'center_registration'
                        self._finalize_detached(tx, entry, deletion_scope=scope, evidence=evidence)
                        entry_snapshot = dict(entry)
                    else:
                        self._record_delete_failure(tx, entry, failure.code, failure.message)
            finally:
                with self._active_lock:
                    self._active_deletions.discard(entry_id)
        for runtime_id in runtime_ids:
            self._invalidate_runtime(runtime_id)
        if failure:
            raise failure
        return entry_snapshot

    def sweep_trash(self, force=False):
        if not self._maintenance_lock.acquire(blocking=False):
            return {'items': []}
        try:
            if not force and time.monotonic() - self._last_sweep < 60:
                return {'items': []}
            self._last_sweep = time.monotonic()
            stamp = datetime.now(timezone.utc)
            with self.store.transaction() as tx:
                for row in tx.list('entries'):
                    if row.get('trashed') and not row.get('detached') and row.get('deletionInProgress') and not self._is_live_deletion(row):
                        self._reconcile_stale_deletion(tx, row, bump_revision=True)
                entries = [row for row in tx.list('entries') if row.get('trashed') and not row.get('detached')
                           and not row.get('deletionInProgress')
                           and datetime.fromisoformat(row['expiresAt']) <= stamp]
            results = []
            for entry in entries:
                try:
                    self._delete(entry['entryId'], {'expectedRevision': entry['revision'], 'confirmPermanent': True})
                    results.append({'entryId': entry['entryId'], 'ok': True})
                except CenterError as error:
                    results.append({'entryId': entry['entryId'], 'ok': False, 'error': {'code': error.code, 'message': error.message}})
            return {'items': results}
        finally:
            self._maintenance_lock.release()
