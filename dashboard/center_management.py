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

    def trash(self):
        with self.store.transaction() as tx:
            settings = tx.get('management', 'trash') or {'retentionDays': 30, 'revision': 1}
            entries = [self.catalog._entry_view(tx, row) for row in tx.list('entries')
                       if row.get('trashed') and not row.get('detached')]
        return {**settings, 'items': sorted(entries, key=lambda row: row.get('trashedAt', ''), reverse=True)}

    def retention(self, body):
        days = body.get('retentionDays')
        if type(days) is not int or not 1 <= days <= 3650:
            raise CenterError('INVALID_RETENTION', 'Retention must be 1 to 3650 days.')
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
            self._expected(body, entry)
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

    def _delete(self, entry_id, body):
        if body.get('confirmPermanent') is not True:
            raise CenterError('CONFIRMATION_REQUIRED', 'Confirm permanent deletion.', 409)
        failure = None
        runtime_ids = []
        with self.catalog._source_refresh_lock, self.store.transaction() as tx:
            entry = tx.get('entries', entry_id)
            if not entry or entry.get('detached'):
                raise CenterError('ENTRY_NOT_FOUND', 'Entry is unavailable.', 404)
            self._expected(body, entry)
            if not entry.get('trashed'):
                raise CenterError('ENTRY_NOT_TRASHED', 'Move the project to the recycle bin before permanently deleting it.', 409)
            try:
                sources = self._idle(tx, entry)
                runtime_ids = [source['runtimeId'] for source in sources if source.get('runtimeId')]
                targets = [(source, self._owned_directory(tx, entry, source)) for source in sources]
                if any(target is None and source.get('runtimeId') and
                       (tx.get('runtimes', source['runtimeId']) or {}).get('managed') for source, target in targets):
                    raise CenterError('MANAGED_SOURCE', 'Release management of the external directory before removing its registration.', 409)
                evidence = []
                for source, target in targets:
                    if target:
                        evidence.append(self._delete_directory(target, source, entry, self._disposal_provenance(tx, entry, source)))
                entry.update(detached=True, deletedAt=now(), deletionEvidence=evidence,
                             deletionScope='managed_files' if evidence else 'center_registration', revision=entry['revision'] + 1)
                entry.pop('trashError', None)
                for source in sources:
                    source.update(detached=True, deletedAt=entry['deletedAt'], revision=source.get('revision', 0) + 1)
                    tx.put('sources', source['sourceId'], source)
                self._event(tx, entry_id, 'delete', deletionScope=entry['deletionScope'], deletionEvidence=evidence)
            except (CenterError, OSError, ValueError) as error:
                failure = error if isinstance(error, CenterError) else CenterError('DELETE_FAILED', 'Directory cleanup failed; the recycle bin record is retained.', 409)
                receipts = [self._delete_receipt(row['runtimeId']) for row in tx.list('sources')
                            if row['entryId'] == entry_id and row.get('runtimeId')]
                entry.update(trashError={'code': failure.code, 'message': failure.message, 'at': now()},
                             partialDeletion=any(row.get('rootMoved') or row.get('cleanupStarted') for row in receipts) or any(
                                 (self.store.data_dir / 'trash-files' / row['runtimeId']).exists() for row in tx.list('sources')
                                 if row['entryId'] == entry_id and row.get('runtimeId')),
                             deletionReceipts=receipts,
                             deletionEvidence=[row['evidence'] for row in receipts if row.get('evidence')], revision=entry['revision'] + 1)
                self._event(tx, entry_id, 'delete_failed', errorCode=failure.code, deletionReceipts=receipts)
            tx.put('entries', entry_id, entry)
        for runtime_id in runtime_ids:
            self._invalidate_runtime(runtime_id)
        if failure:
            raise failure
        return entry

    def sweep_trash(self, force=False):
        if not self._maintenance_lock.acquire(blocking=False):
            return {'items': []}
        try:
            if not force and time.monotonic() - self._last_sweep < 60:
                return {'items': []}
            self._last_sweep = time.monotonic()
            stamp = datetime.now(timezone.utc)
            with self.store.transaction() as tx:
                entries = [row for row in tx.list('entries') if row.get('trashed') and not row.get('detached')
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
