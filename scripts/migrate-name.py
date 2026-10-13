#!/usr/bin/env python3
"""Stopped-instance v3 namespace migration, with durable resume and rollback."""
from contextlib import ExitStack, contextmanager
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import sys
import uuid

OLD = '.auto-company'
NEW = '.autonomous-company'
IGNORE = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'acceptance', 'Files', 'examples'}
MIGRATING = '.autonomous-company-migration-in-progress.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def atomic(path, data):
    path = Path(path)
    temp = path.with_name(path.name + '.migration.tmp')
    with temp.open('wb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    if path.exists():
        os.chmod(temp, stat.S_IMODE(path.stat().st_mode))
        if os.name == 'nt':
            # copy2 does not copy NTFS security. Preserve the existing DACL
            # before replacing a credential-bearing configuration file.
            import ctypes
            from ctypes import wintypes
            security = ctypes.WinDLL('advapi32', use_last_error=True)
            security.GetFileSecurityW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
            security.SetFileSecurityW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID]
            security.GetSecurityDescriptorControl.argtypes = [wintypes.LPVOID, ctypes.POINTER(wintypes.WORD), ctypes.POINTER(wintypes.DWORD)]
            required = wintypes.DWORD()
            security.GetFileSecurityW(str(path), 4, None, 0, ctypes.byref(required))
            descriptor = ctypes.create_string_buffer(required.value)
            control, revision = wintypes.WORD(), wintypes.DWORD()
            if not security.GetFileSecurityW(str(path), 4, descriptor, required.value, ctypes.byref(required)) or not security.GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision)):
                raise ctypes.WinError(ctypes.get_last_error())
            flags = 4 | (0x80000000 if control.value & 0x1000 else 0x20000000)
            if not security.SetFileSecurityW(str(temp), flags, descriptor):
                raise ctypes.WinError(ctypes.get_last_error())
    os.replace(temp, path)


def transition_matches(observed, before, after):
    """A stopped multi-file center switch may be partway through its journal."""
    if observed is None or before is None or after is None:
        return False
    return all(observed.get(name) in {before.get(name), after.get(name)}
               for name in set(observed) | set(before) | set(after))


def save(path, value):
    atomic(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())


def tree(path):
    path = Path(path)
    if not path.exists():
        return None
    if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
        raise ValueError('Linked migration path: ' + str(path))
    if path.is_file():
        return {'': sha(path.read_bytes())}
    result = {}
    for folder, directories, files in os.walk(path):
        for name in directories + files:
            item = Path(folder) / name
            if item.is_symlink() or getattr(item, 'is_junction', lambda: False)():
                raise ValueError('Linked migration content: ' + str(item))
        for name in files:
            if name == MIGRATING:
                continue
            item = Path(folder) / name
            result[item.relative_to(path).as_posix()] = sha(item.read_bytes())
    return result


def config(raw):
    text = raw.decode('utf-8')
    lines = text.splitlines(keepends=True)
    keys = set()
    output = []
    for line in lines:
        match = re.match(r'([A-Z][A-Z0-9_]*)=', line)
        if match:
            key = ('AUTONOMOUS_COMPANY_' + match[1][len('AUTO_COMPANY_'):]
                   if match[1].startswith('AUTO_COMPANY_') else match[1])
            if key in keys:
                raise ValueError('Conflicting or duplicate environment key: ' + key)
            keys.add(key)
            line = key + line[len(match[1]):]
        output.append(line)
    return ''.join(output).encode('utf-8')


def stopped(root):
    root = Path(root)
    names = ['.auto-loop.pid', '.auto-loop-stop-pending']
    for prefix in (OLD, NEW):
        names += [prefix + '.local.team-active', prefix + '.local.lock', prefix + '.local.language-update',
                  prefix + '/product-state.lock', prefix + '/product-state.transaction.json', prefix + '/project-registry.lock']
    for name in names:
        item = root / name
        if item.exists():
            raise ValueError('Stop/recover the original writer before migration: ' + str(item))


def center_stopped(path):
    with center_lock(path):
        database = Path(path) / 'center.sqlite3'
        if database.exists():
            connection = sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)
            try:
                for kind, identity, body in connection.execute('SELECT kind,id,body FROM records'):
                    value = json.loads(body)
                    if kind == 'requests' and value.get('state') in {'starting', 'running', 'stopping', 'attention'} and value.get('dispatchId'):
                        raise ValueError('Reconcile the original dispatch before migration: ' + identity)
                    if kind == 'operations' and value.get('state') in {'preparing', 'running'}:
                        raise ValueError('Recover the original operation before migration: ' + identity)
            finally:
                connection.close()


@contextmanager
def center_lock(path):
    lock = Path(path) / 'center.lock'
    if not lock.exists():
        yield
        return
    with lock.open('a+b') as handle:
        if os.name == 'nt':
            import msvcrt
            if lock.stat().st_size == 0:
                handle.write(b'0')
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == 'nt':
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def namespace_operations(root):
    result = []
    folders = [Path(root)]
    projects = Path(root) / 'projects'
    if projects.is_dir():
        folders += [path for path in projects.iterdir() if path.is_dir()]
    for folder in folders:
        for source in folder.iterdir():
            name = source.name
            if name.startswith(OLD):
                target = source.with_name(NEW + name[len(OLD):])
                if target.exists():
                    raise ValueError('Target is occupied: ' + str(target))
                result.append({'source': str(source), 'target': str(target), 'kind': 'rename'})
    env = Path(root) / '.auto-loop.env'
    if env.is_file() and config(env.read_bytes()) != env.read_bytes():
        result.append({'source': str(env), 'target': str(env), 'kind': 'config'})
    return result


def prepare(roots, data_dir=None, new_data_dir=None):
    operations = []
    for root in roots:
        root = Path(root).resolve(strict=True)
        stopped(root)
        operations += namespace_operations(root)
    if data_dir:
        source, target = Path(data_dir).resolve(strict=True), Path(new_data_dir).resolve()
        if source == target or source in target.parents or target in source.parents:
            raise ValueError('Center source and target must be distinct non-nested paths')
        if target.exists():
            raise ValueError('Center target is occupied: ' + str(target))
        center_stopped(source)
        if any(source == Path(root).resolve() or source in Path(root).resolve().parents for root in roots):
            raise ValueError('Migrate nested runtime roots in a separate manifest before moving the center')
        operations.append({'source': str(source), 'target': str(target), 'kind': 'center'})
    for operation in operations:
        operation['before'] = tree(operation['source'])
    return operations


def transform_item(operation, path):
    path = Path(path)
    name = Path(operation['target']).name
    if operation['kind'] == 'config' or name.startswith(NEW + '.local'):
        if name.endswith('.cycle-backup'):
            value = json.loads(path.read_text(encoding='utf-8'))
            value['data'] = config(bytes.fromhex(value['data'])).hex()
            path.write_text(json.dumps(value), encoding='utf-8')
        elif path.is_file():
            path.write_bytes(config(path.read_bytes()))


def center_transform(path, mappings):
    database = Path(path) / 'center.sqlite3'
    if not database.exists():
        return
    connection = sqlite3.connect(database)
    try:
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Center database failed integrity_check')
        # Only effective absolute path fields change. Historical bodies,
        # identity IDs, receipts, fingerprints and timestamps stay untouched.
        for kind, identity, body in connection.execute('SELECT kind,id,body FROM records').fetchall():
            value = json.loads(body)
            changed = False
            if kind in {'sources', 'runtimes'} and isinstance(value.get('root'), str):
                original = value['root']
                for source, target in mappings:
                    if original == source or original.startswith(source + os.sep):
                        value['root'] = target + original[len(source):]
                changed |= original != value['root']
            if kind == 'controls' and identity == 'queue':
                value.update(dispatchEnabled=False, reason='namespace_migration', revision=value.get('revision', 0) + 1)
                changed = True
            if kind == 'requests' and value.get('startAuthorized'):
                value['startAuthorized'] = False
                changed = True
            if changed:
                connection.execute('UPDATE records SET body=? WHERE kind=? AND id=?',
                                   (json.dumps(value, ensure_ascii=False, sort_keys=True), kind, identity))
        connection.commit()
        connection.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    finally:
        connection.close()


def apply(manifest_path, roots=(), data_dir=None, new_data_dir=None):
    manifest_path = Path(manifest_path).resolve()
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest['state'] == 'rolled_back':
            raise ValueError('Rolled-back migration requires a new manifest')
        if manifest['state'] == 'complete':
            verify(manifest)
            markers(manifest, remove=True)
            return manifest
    else:
        operations = prepare(roots, data_dir, new_data_dir)
        backup = manifest_path.with_suffix('.backup')
        if any(Path(row['source']).is_dir() and (backup == Path(row['source']) or Path(row['source']) in backup.parents) for row in operations):
            raise ValueError('Manifest/backup must be outside moved instance data')
        if backup.exists():
            raise ValueError('Backup target is occupied: ' + str(backup))
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        backup.mkdir()
        if os.name != 'nt':
            backup.chmod(0o700)
        manifest = {'version': 1, 'migrationId': uuid.uuid4().hex, 'state': 'backing_up', 'roots': [str(Path(x).resolve()) for x in roots],
                    'operations': operations, 'backup': str(backup)}
        save(manifest_path, manifest)
        for index, operation in enumerate(operations):
            source = Path(operation['source'])
            destination = backup / str(index)
            if source.is_dir():
                shutil.copytree(source, destination, copy_function=shutil.copy2)
            else:
                shutil.copy2(source, destination)
            if tree(destination) != operation['before']:
                raise ValueError('Source changed while backing up')
            operation['backup'] = str(destination)
        manifest['state'] = 'prepared'
        save(manifest_path, manifest)
    if manifest['state'] == 'backing_up':
        raise ValueError('Backup was interrupted before mutation; preserve it and use a new manifest')
    for root in manifest['roots']:
        stopped(root)
    markers(manifest)
    for operation in manifest['operations']:
        source, target = Path(operation['source']), Path(operation['target'])
        if operation.get('done'):
            if tree(target) != operation['after']:
                raise ValueError('Migrated state changed; refusing resume')
            continue
        # Preparing a transformed copy makes the expected after-state durable
        # before any rename. On interruption, old OR expected-new is accepted.
        if 'after' not in operation:
            staged = Path(operation['backup']).with_name(Path(operation['backup']).name + '-prepared')
            if staged.exists():
                # The previous preparation never changed the instance. Reuse
                # only a complete byte-identical copy; otherwise stop safely.
                if tree(staged) != operation['before']:
                    raise ValueError('Interrupted preparation needs explicit backup recovery: ' + str(staged))
            elif Path(operation['backup']).is_dir():
                shutil.copytree(operation['backup'], staged)
            else:
                shutil.copy2(operation['backup'], staged)
            transform_item(operation, staged)
            if operation['kind'] == 'center':
                center_transform(staged, [(operation['source'], operation['target'])])
            operation['after'] = tree(staged)
            operation['staged'] = str(staged)
            save(manifest_path, manifest)
        moved = source != target and not source.exists() and transition_matches(tree(target), operation['before'], operation['after'])
        if moved and tree(target) == operation['after']:
            operation['done'] = True
            save(manifest_path, manifest)
            continue
        if not moved and tree(source) != operation['before']:
            # Config replacement may have completed just before interruption.
            if source == target and tree(target) == operation['after']:
                operation['done'] = True
                save(manifest_path, manifest)
                continue
            raise ValueError('Migration source changed; refusing overwrite')
        if not moved and source != target and target.exists():
            raise ValueError('Target became occupied; refusing overwrite')
        target.parent.mkdir(parents=True, exist_ok=True)
        if source != target and not moved:
            os.replace(source, target)
        staged = Path(operation['staged'])
        if staged.is_file():
            atomic(target, staged.read_bytes())
        elif operation['kind'] == 'center':
            # All writers are stopped and the consistent prepared database was
            # checkpointed; replace database + sidecars as one journaled step.
            for file in ('center.sqlite3', 'center.sqlite3-wal', 'center.sqlite3-shm'):
                original = target / file
                prepared = staged / file
                if prepared.exists():
                    atomic(original, prepared.read_bytes())
                elif original.exists():
                    original.unlink()
        operation['done'] = True
        save(manifest_path, manifest)
    manifest['state'] = 'complete'
    save(manifest_path, manifest)
    verify(manifest)
    markers(manifest, remove=True)
    return manifest


def markers(manifest, remove=False):
    folders = [Path(root) for root in manifest['roots']]
    for operation in manifest['operations']:
        if operation['kind'] == 'center':
            folders.append(Path(operation['target'] if Path(operation['target']).exists() else operation['source']))
    for folder in folders:
        path = folder / MIGRATING
        if path.exists():
            value = json.loads(path.read_text(encoding='utf-8'))
            if value != {'migrationId': manifest['migrationId']}:
                raise ValueError('Another migration owns this instance')
            if remove:
                path.unlink()
        elif not remove:
            save(path, {'migrationId': manifest['migrationId']})


def verify(manifest):
    for operation in manifest['operations']:
        if tree(operation['target']) != operation['after']:
            raise ValueError('Migration validation failed: ' + operation['target'])
        if operation['source'] != operation['target'] and Path(operation['source']).exists():
            raise ValueError('Old namespace is still present')
    return True


def rollback(manifest_path):
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['state'] == 'rolled_back':
        return manifest
    if manifest['state'] == 'backing_up':
        raise ValueError('Backup was interrupted; original instance was not changed')
    for root in manifest['roots']:
        stopped(root)
    for operation in manifest['operations']:
        if operation['kind'] == 'center':
            center_stopped(operation['target'] if Path(operation['target']).exists() else operation['source'])
    markers(manifest)
    for operation in manifest['operations']:
        path = Path(operation['target'])
        observed = tree(path)
        if observed not in (operation.get('after'), operation['before'], None) and not transition_matches(observed, operation['before'], operation.get('after')):
            raise ValueError('New content exists; preserve it before rollback: ' + str(path))
        if tree(operation['backup']) != operation['before']:
            raise ValueError('Backup validation failed')
        if operation['source'] != operation['target'] and Path(operation['source']).exists() and tree(operation['source']) != operation['before']:
            raise ValueError('Original state changed; refusing rollback')
    for operation in reversed(manifest['operations']):
        source, target = Path(operation['source']), Path(operation['target'])
        if source != target and target.exists():
            if source.exists():
                raise ValueError('Rollback source occupied; refusing overwrite')
            os.replace(target, source)
        if source.is_file():
            atomic(source, Path(operation['backup']).read_bytes())
        elif operation['kind'] == 'center':
            for file in ('center.sqlite3', 'center.sqlite3-wal', 'center.sqlite3-shm'):
                original, backup = source / file, Path(operation['backup']) / file
                if backup.exists():
                    atomic(original, backup.read_bytes())
                elif original.exists():
                    original.unlink()
        if tree(source) != operation['before']:
            raise ValueError('Rollback validation failed')
    manifest['state'] = 'rolled_back'
    save(manifest_path, manifest)
    markers(manifest, remove=True)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'apply', 'verify', 'rollback'))
    parser.add_argument('--root', type=Path, action='append', default=[])
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--new-data-dir', type=Path)
    parser.add_argument('--manifest', type=Path)
    args = parser.parse_args()
    if bool(args.data_dir) != bool(args.new_data_dir):
        parser.error('--data-dir and --new-data-dir are required together')
    if args.action != 'plan' and not args.manifest:
        parser.error('--manifest is required')
    try:
        with ExitStack() as stack:
            manifest = json.loads(args.manifest.read_text(encoding='utf-8')) if args.manifest and args.manifest.exists() else None
            centers = [Path(row['target'] if Path(row['target']).exists() else row['source']) for row in manifest['operations'] if row['kind'] == 'center'] if manifest else ([args.data_dir] if args.data_dir else [])
            for root in (manifest['roots'] if manifest else args.root):
                stopped(root)
            # Validate that an old/new center has no owner, and release the
            # native file handle before moving its containing directory.
            for center in centers:
                center_stopped(center)
            if args.action == 'plan':
                result = prepare(args.root, args.data_dir, args.new_data_dir)
            elif args.action == 'apply':
                result = apply(args.manifest, args.root, args.data_dir, args.new_data_dir)
            elif args.action == 'rollback':
                result = rollback(args.manifest)
            else:
                result = verify(json.loads(args.manifest.read_text(encoding='utf-8')))
        print(json.dumps({'ok': True, 'result': result}, ensure_ascii=False))
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
