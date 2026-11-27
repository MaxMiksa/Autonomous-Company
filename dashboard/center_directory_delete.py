"""Delete one center-created runtime while holding its original POSIX owner locks."""
from pathlib import Path
import argparse
import json
import os
import shutil
import signal
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/core'))
from center_runner import MARKER, execution_lock, lock_file, owner_dir, disposal_preflight, disposal_provenance, read_json, token


def no_links(path, recursive=True):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('unsafe_delete_path')
    if recursive and path.exists():
        for folder, directories, files in os.walk(path, followlinks=False):
            for name in directories + files:
                item = Path(folder) / name
                if item.is_symlink() or not (item.is_dir() or item.is_file()):
                    raise ValueError('unsafe_delete_path')


def atomic_json(path, value):
    """Private random temporary inode; never opens a predictable .tmp target."""
    path = Path(path)
    no_links(path, recursive=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    no_links(path.parent, recursive=False)
    descriptor, name = tempfile.mkstemp(prefix='.receipt-', suffix='.tmp', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        no_links(path, recursive=False)
        os.replace(temporary, path)
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        temporary.unlink(missing_ok=True)


def delete_runtime(manifest):
    expected = manifest['marker']
    framework_revision = manifest.get('expectedFrameworkRevision')
    for name in ('centerId', 'runtimeId', 'entryId', 'sourceId', 'operationId'):
        token(expected[name])
    data = Path(manifest['dataDir'])
    root = Path(manifest['root'])
    no_links(data, recursive=False)
    if root != data / 'runtimes' / expected['runtimeId'] or root.resolve().parent != (data / 'runtimes').resolve():
        raise ValueError('delete_outside_center')
    cleanup = data / 'trash-files' / expected['runtimeId']
    receipt = data / 'deletion-receipts' / (expected['runtimeId'] + '.json')
    evidence = data / 'deletion-evidence' / (expected['runtimeId'] + '.zip')
    for destination in (cleanup, receipt, evidence):
        no_links(destination, recursive=False)
        destination.resolve().relative_to(data.resolve())
    for folder in (cleanup.parent, receipt.parent, evidence.parent):
        folder.mkdir(parents=True, exist_ok=True)
        no_links(folder, recursive=False)
    previous = read_json(receipt) if receipt.exists() else {}
    if previous.get('expectedFrameworkRevision') and previous['expectedFrameworkRevision'] != framework_revision:
        raise ValueError('delete_framework_provenance_changed')
    if not root.exists() and not cleanup.exists() and (previous.get('rootMoved') or previous.get('cleanupStarted') or previous.get('filesDeleted')):
        if previous.get('marker') == expected and previous.get('root') == str(root) and evidence.is_file():
            with zipfile.ZipFile(evidence) as archive:
                original = archive.getinfo(MARKER)
                if original.file_size > 65536:
                    raise ValueError('delete_evidence_invalid')
                original_marker = json.loads(archive.read(original))
                if any(original_marker.get(key) != value for key, value in expected.items()):
                    raise ValueError('delete_evidence_mismatch')
            previous.update(state='succeeded', filesDeleted=True)
            atomic_json(receipt, previous)
            return previous
        raise ValueError('delete_receipt_mismatch')
    if root.exists() and cleanup.exists():
        raise ValueError('ambiguous_cleanup_path')
    moved = not root.exists() and cleanup.exists()
    current = cleanup if moved else root
    no_links(current)
    marker_path = current / MARKER
    recovering = (previous.get('marker') == expected and previous.get('root') == str(root)
                  and (previous.get('rootMoved') or previous.get('cleanupStarted')) and evidence.is_file())
    marker = read_json(marker_path) if marker_path.exists() else previous.get('fullMarker', {}) if recovering else {}
    if any(marker.get(key) != value for key, value in expected.items()):
        raise ValueError('delete_owner_changed')
    if moved and not recovering:
        raise ValueError('delete_receipt_missing')
    if recovering:
        with zipfile.ZipFile(evidence) as archive:
            original = archive.getinfo(MARKER)
            if original.file_size > 65536 or json.loads(archive.read(original)) != marker:
                raise ValueError('delete_evidence_mismatch')
    if not moved and not recovering:
        checked = disposal_preflight(root, expected['centerId'], framework_revision)
        if not checked.get('quiescent'):
            raise ValueError(checked.get('reason') or 'delete_not_quiescent')
    state = {'marker': expected, 'fullMarker': marker, 'root': str(root), 'cleanupPath': str(cleanup), 'rootMoved': moved,
             'expectedFrameworkRevision': framework_revision,
             'cleanupStarted': bool(previous.get('cleanupStarted')), 'state': 'preparing', 'evidence': str(evidence),
             'stage': 'ownership'}
    atomic_json(receipt, state)
    descriptor = None
    try:
        with execution_lock(marker):
            descriptor = lock_file(current / '.auto-loop.pid')
            owner_path = owner_dir(marker) / 'owner.json'
            if owner_path.exists():
                owner = read_json(owner_path)
                if owner.get('state') != 'terminal' or not owner.get('cleanupConfirmed'):
                    raise ValueError('delete_owner_unconfirmed')
            no_links(current)
            if marker_path.exists() and read_json(marker_path) != marker:
                raise ValueError('delete_owner_changed')
            if not moved and not recovering:
                checked = disposal_provenance(root, expected['centerId'], framework_revision)
                if checked.get('frameworkRevision') != framework_revision or checked.get('marker') != marker:
                    raise ValueError('delete_framework_provenance_changed')
            if not moved and not state['cleanupStarted']:
                state.update(state='deleting', stage='preserve_evidence', pid=os.getpid())
                atomic_json(receipt, state)
                no_links(evidence, recursive=False)
                evidence_descriptor, name = tempfile.mkstemp(prefix='.evidence-', suffix='.tmp', dir=evidence.parent)
                temporary = Path(name)
                try:
                    with os.fdopen(evidence_descriptor, 'w+b') as stream:
                        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                            for name in ('.autonomous-company', 'logs', 'memories', MARKER, '.auto-loop-state',
                                         '.autonomous-company.local', 'projects/registry.tsv', 'Human Overrides.md'):
                                item = root / name
                                files = [item] if item.is_file() else item.rglob('*') if item.is_dir() else []
                                for child in files:
                                    if child.is_file():
                                        archive.write(child, child.relative_to(root).as_posix())
                            for child in root.glob('projects/*/.autonomous-company/identity.json'):
                                archive.write(child, child.relative_to(root).as_posix())
                        stream.flush()
                        os.fsync(stream.fileno())
                    no_links(evidence, recursive=False)
                    os.replace(temporary, evidence)
                finally:
                    temporary.unlink(missing_ok=True)
            if not moved:
                # DrvFS cannot rename a directory containing an open flock.
                # Keep the original loop inode locked until its code is gone;
                # the original execution slot stays locked through root removal.
                state.update(cleanupStarted=True, state='deleting', stage='remove_contents')
                atomic_json(receipt, state)
                for child in current.iterdir():
                    if child.name in {'.auto-loop.pid', MARKER}:
                        continue
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                state['stage'] = 'remove_root'
                atomic_json(receipt, state)
                os.close(descriptor)
                descriptor = None
                (current / MARKER).unlink(missing_ok=True)
                (current / '.auto-loop.pid').unlink(missing_ok=True)
                current.rmdir()
            else:
                state['stage'] = 'remove_legacy_cleanup'
                # Previously staged receipts remain supported. No executable
                # root exists at its registered location during this cleanup.
                os.close(descriptor)
                descriptor = None
                shutil.rmtree(cleanup)
            state.update(state='succeeded', filesDeleted=True)
            atomic_json(receipt, state)
    except Exception as error:
        state.update(state='failed', reason=str(error) if isinstance(error, ValueError) else 'delete_timeout' if isinstance(error, TimeoutError) else 'delete_io_failed',
                     errorType=type(error).__name__, errno=getattr(error, 'errno', None))
        atomic_json(receipt, state)
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    arguments = parser.parse_args()
    try:
        def deadline(_signum, _frame):
            raise TimeoutError('delete_timeout')
        signal.signal(signal.SIGALRM, deadline)
        signal.alarm(150)
        result = delete_runtime(read_json(Path(arguments.manifest)))
        signal.alarm(0)
        print(json.dumps(result))
        return 0
    except Exception:
        print(json.dumps({'error': 'DELETE_FAILED'}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
