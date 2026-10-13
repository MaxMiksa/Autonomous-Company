#!/usr/bin/env python3
"""Rename only an explicitly owned, stopped and disabled service registration."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET

OLD_TASK = 'AutoCompany-WSL-Start'
NEW_TASK = 'AutonomousCompany-WSL-Start'


def run(*arguments, missing=False):
    result = subprocess.run(list(arguments), capture_output=True, input=b'')
    if result.returncode and not missing:
        raise ValueError('Service command failed: ' + arguments[0])
    return result


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    os.replace(temporary, path)


def systemd_stopped(name, expected_root=None, expected_fragment=None):
    output = run('systemctl', '--user', 'show', name, '-p', 'ActiveState', '-p', 'MainPID', '-p', 'UnitFileState', '-p', 'WorkingDirectory', '-p', 'FragmentPath', '-p', 'DropInPaths', missing=True).stdout.decode()
    values = dict(line.split('=', 1) for line in output.splitlines() if '=' in line)
    if values.get('ActiveState') not in {'inactive', 'failed'} or values.get('MainPID') != '0' or values.get('UnitFileState') not in {'disabled', 'static'}:
        raise ValueError('Original service must be stopped and disabled before migration')
    if values.get('DropInPaths'):
        raise ValueError('Service has custom drop-ins; preserve and explicitly migrate them before registration')
    if expected_root is not None and values.get('WorkingDirectory') != expected_root:
        raise ValueError('Loaded service belongs to a different checkout')
    if expected_fragment is not None and values.get('FragmentPath') != str(expected_fragment):
        raise ValueError('Loaded service uses a different registration file')


def task_stopped(name):
    # The fixed task name is the only value interpolated into this query.
    if name not in {OLD_TASK, NEW_TASK}:
        raise ValueError('Unexpected scheduled task name')
    query = f"$task = Get-ScheduledTask -TaskName '{name}' -ErrorAction Stop; if ($task.State -ne 'Disabled') {{ exit 2 }}"
    run('powershell.exe', '-NoProfile', '-NonInteractive', '-Command', query)


def prepare(kind, old_root, root, manifest):
    old_root, root = str(Path(old_root).resolve()), str(Path(root).resolve())
    backup = manifest.with_suffix('.service-backup')
    if backup.exists():
        raise ValueError('Backup is occupied')
    if kind == 'systemd':
        old = Path.home() / '.config/systemd/user/auto-company.service'
        new = old.with_name('autonomous-company.service')
        systemd_stopped(old.name, old_root, old)
        raw = old.read_bytes()
        text = raw.decode('utf-8')
        working = next((line.split('=', 1)[1] for line in text.splitlines() if line.startswith('WorkingDirectory=')), '')
        if working.replace('%%', '%') != old_root:
            raise ValueError('Service belongs to a different checkout')
        output = []
        environment_names = set()
        for line in text.splitlines(keepends=True):
            if line.startswith(('WorkingDirectory=', 'EnvironmentFile=', 'ExecStart=')):
                line = line.replace(old_root.replace('%', '%%'), root.replace('%', '%%'))
                line = line.replace(old_root, root)
            elif line.startswith('Description='):
                line = line.replace('Auto Company', 'Autonomous Company')
            elif line.startswith('Environment='):
                import re
                line = re.sub(r'(?<=[ "\t])AUTO_COMPANY_(?=[A-Z0-9_]+=)', 'AUTONOMOUS_COMPANY_', line)
                line = line.replace('Environment=AUTO_COMPANY_', 'Environment=AUTONOMOUS_COMPANY_')
                import shlex
                for item in shlex.split(line.split('=', 1)[1]):
                    name = item.split('=', 1)[0]
                    if name.startswith('AUTONOMOUS_COMPANY_'):
                        if name in environment_names:
                            raise ValueError('Conflicting systemd environment names: ' + name)
                        environment_names.add(name)
            output.append(line)
        migrated = ''.join(output).encode()
    elif kind == 'launchd':
        old = Path.home() / 'Library/LaunchAgents/com.autocompany.loop.plist'
        new = old.with_name('com.autonomouscompany.loop.plist')
        if run('launchctl', 'print', f'gui/{os.getuid()}/com.autocompany.loop', missing=True).returncode == 0:
            raise ValueError('Unload and disable the original LaunchAgent before migration')
        raw = old.read_bytes()
        value = plistlib.loads(raw)
        if value.get('WorkingDirectory') != old_root or value.get('Label') != 'com.autocompany.loop':
            raise ValueError('LaunchAgent belongs to a different checkout')
        disabled = run('launchctl', 'print-disabled', f'gui/{os.getuid()}').stdout.decode()
        if '"com.autocompany.loop" => true' not in disabled:
            raise ValueError('Disable the original LaunchAgent before migration')
        value.update(Label='com.autonomouscompany.loop', WorkingDirectory=root)
        for name in ('StandardOutPath', 'StandardErrorPath'):
            original = value.get(name)
            if isinstance(original, str) and original.startswith(old_root + '/'):
                value[name] = root + original[len(old_root):]
        value['ProgramArguments'] = [root + argument[len(old_root):] if argument.startswith(old_root + '/') else argument for argument in value.get('ProgramArguments', [])]
        environment = {}
        for key, val in value.get('EnvironmentVariables', {}).items():
            name = 'AUTONOMOUS_COMPANY_' + key[len('AUTO_COMPANY_'):] if key.startswith('AUTO_COMPANY_') else key
            if name in environment:
                raise ValueError('Conflicting LaunchAgent environment names')
            if key == 'PATH':
                val = ':'.join(root + part[len(old_root):] if part == old_root or part.startswith(old_root + '/') else part for part in val.split(':'))
            elif key.endswith(('_BIN', '_RUNTIME')) or name == 'AUTONOMOUS_COMPANY_ROOT':
                if val == old_root or val.startswith(old_root + '/'):
                    val = root + val[len(old_root):]
            elif old_root in val:
                raise ValueError('Unknown environment path requires explicit migration: ' + key)
            environment[name] = val
        value['EnvironmentVariables'] = environment
        migrated = plistlib.dumps(value)
    else:
        task_stopped(OLD_TASK)
        raw = run('schtasks.exe', '/Query', '/TN', OLD_TASK, '/XML').stdout
        value = ET.fromstring(raw)
        namespace = {'t': 'http://schemas.microsoft.com/windows/2004/02/mit/task'}
        arguments = value.findall('t:Actions/t:Exec/t:Arguments', namespace)
        if len(arguments) != 1 or old_root + '\\scripts\\windows\\start-win.ps1' not in (arguments[0].text or ''):
            raise ValueError('Scheduled task belongs to a different checkout')
        arguments[0].text = arguments[0].text.replace(old_root + '\\scripts\\windows\\start-win.ps1', root + '\\scripts\\windows\\start-win.ps1')
        registration = value.find('t:RegistrationInfo/t:URI', namespace)
        if registration is not None:
            registration.text = '\\' + NEW_TASK
        enabled = value.find('t:Settings/t:Enabled', namespace)
        if enabled is None:
            enabled = ET.SubElement(value.find('t:Settings', namespace), '{' + namespace['t'] + '}Enabled')
        enabled.text = 'false'
        migrated = ET.tostring(value, encoding='utf-16', xml_declaration=True)
        old, new = OLD_TASK, NEW_TASK
        if run('schtasks.exe', '/Query', '/TN', NEW_TASK, missing=True).returncode == 0:
            raise ValueError('New scheduled task is already occupied')
    if kind != 'windows-task' and new.exists():
        raise ValueError('New service path is occupied')
    manifest.parent.mkdir(parents=True, exist_ok=True)
    backup.mkdir()
    if os.name != 'nt':
        backup.chmod(0o700)
    (backup / 'original').write_bytes(raw)
    (backup / 'new').write_bytes(migrated)
    mode = stat.S_IMODE(old.stat().st_mode) if kind != 'windows-task' else 0o600
    (backup / 'original').chmod(mode)
    (backup / 'new').chmod(mode)
    return {'version': 1, 'state': 'prepared', 'kind': kind, 'old': str(old), 'new': str(new), 'oldRoot': old_root, 'root': root, 'backup': str(backup)}


def apply(manifest, value):
    kind = value['kind']
    backup = Path(value['backup'])
    if value['state'] == 'complete':
        if kind != 'windows-task' and Path(value['new']).read_bytes() != (backup / 'new').read_bytes():
            raise ValueError('New service registration changed')
        if kind == 'systemd':
            systemd_stopped(Path(value['new']).name, value['root'], value['new'])
        elif kind == 'windows-task':
            task_stopped(value['new'])
            if run('schtasks.exe', '/Query', '/TN', NEW_TASK, '/XML').stdout != (backup / 'applied-registration').read_bytes():
                raise ValueError('New scheduled task changed')
        return value
    if kind == 'windows-task':
        # XML explicitly disables ONLOGON before registration; never /Run.
        existing = run('schtasks.exe', '/Query', '/TN', NEW_TASK, '/XML', missing=True)
        if existing.returncode == 0:
            if not (backup / 'applied-registration').exists() or existing.stdout != (backup / 'applied-registration').read_bytes():
                raise ValueError('New task appeared or changed; refusing overwrite')
        else:
            task_stopped(OLD_TASK)
            if run('schtasks.exe', '/Query', '/TN', OLD_TASK, '/XML').stdout != (backup / 'original').read_bytes():
                raise ValueError('Original task changed; refusing migration')
            run('schtasks.exe', '/Create', '/TN', NEW_TASK, '/XML', str(backup / 'new'))
            (backup / 'applied-registration').write_bytes(run('schtasks.exe', '/Query', '/TN', NEW_TASK, '/XML').stdout)
        task_stopped(NEW_TASK)
        previous = run('schtasks.exe', '/Query', '/TN', OLD_TASK, '/XML', missing=True)
        if previous.returncode == 0:
            task_stopped(OLD_TASK)
            if previous.stdout != (backup / 'original').read_bytes():
                raise ValueError('Original task changed; refusing deletion')
            run('schtasks.exe', '/Delete', '/TN', OLD_TASK, '/F')
    else:
        old, new = Path(value['old']), Path(value['new'])
        if new.exists() and new.read_bytes() != (backup / 'new').read_bytes():
            raise ValueError('New service changed; refusing migration')
        if kind == 'launchd':
            run('launchctl', 'disable', f'gui/{os.getuid()}/com.autonomouscompany.loop')
        if old.exists():
            if old.read_bytes() != (backup / 'original').read_bytes():
                raise ValueError('Original service changed; refusing migration')
            if kind == 'systemd':
                systemd_stopped(old.name, value['oldRoot'], old)
            os.replace(old, backup / 'original-registration')
        new.write_bytes((backup / 'new').read_bytes())
        shutil.copystat(backup / 'original-registration', new)
        if kind == 'systemd':
            run('systemctl', '--user', 'daemon-reload')
            systemd_stopped(new.name, value['root'], new)
    value['state'] = 'complete'
    save(manifest, value)
    return value


def rollback(manifest, value):
    if value['state'] == 'rolled_back':
        return value
    kind, backup = value['kind'], Path(value['backup'])
    if kind == 'windows-task':
        task_stopped(NEW_TASK)
        if run('schtasks.exe', '/Query', '/TN', NEW_TASK, '/XML').stdout != (backup / 'applied-registration').read_bytes():
            raise ValueError('New scheduled task changed; refusing rollback')
        if run('schtasks.exe', '/Query', '/TN', OLD_TASK, missing=True).returncode == 0:
            raise ValueError('Old scheduled task is occupied; refusing rollback')
        # Original XML was disabled at preflight, and remains disabled.
        run('schtasks.exe', '/Create', '/TN', OLD_TASK, '/XML', str(backup / 'original'))
        run('schtasks.exe', '/Delete', '/TN', NEW_TASK, '/F')
    else:
        old, new = Path(value['old']), Path(value['new'])
        if kind == 'systemd':
            systemd_stopped(new.name)
        elif run('launchctl', 'print', f'gui/{os.getuid()}/com.autonomouscompany.loop', missing=True).returncode == 0:
            raise ValueError('Unload the new LaunchAgent before rollback')
        if old.exists() or new.read_bytes() != (backup / 'new').read_bytes():
            raise ValueError('Service registration changed; refusing rollback')
        os.replace(new, backup / 'rolled-back-registration')
        os.replace(backup / 'original-registration', old)
        if kind == 'systemd':
            run('systemctl', '--user', 'daemon-reload')
            systemd_stopped(old.name)
    value['state'] = 'rolled_back'
    save(manifest, value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'apply', 'rollback'))
    parser.add_argument('--kind', choices=('systemd', 'launchd', 'windows-task'))
    parser.add_argument('--old-root', type=Path)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.manifest.exists():
            value = json.loads(args.manifest.read_text(encoding='utf-8'))
        else:
            if not all((args.kind, args.old_root, args.root)):
                parser.error('--kind, --old-root and --root are required for the initial plan')
            value = prepare(args.kind, args.old_root, args.root, args.manifest)
            save(args.manifest, value)
        if args.action == 'apply':
            value = apply(args.manifest, value)
        elif args.action == 'rollback':
            value = rollback(args.manifest, value)
        print(json.dumps({'ok': True, 'state': value['state'], 'kind': value['kind']}))
    except (ValueError, OSError, ET.ParseError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
