"""Service definition ownership/recovery; managers are explicit doubles."""
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('service_migration', ROOT / 'scripts/migrate-service-name.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


@unittest.skipIf(os.name == 'nt', 'POSIX service definition contracts run under WSL/macOS')
class ServiceMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.old_root = self.home / 'original-runtime'
        self.root = self.home / 'new-runtime'
        self.old_root.mkdir()
        self.root.mkdir()
        self.manifest = self.home / 'service.json'
        self.calls = []
        self.home_patch = mock.patch.object(Path, 'home', return_value=self.home)
        self.home_patch.start()
        self.addCleanup(self.home_patch.stop)

    def manager(self, *args, missing=False):
        self.calls.append(args)
        output, code = b'', 0
        if args[:3] == ('systemctl', '--user', 'show'):
            old = args[3] == 'auto-company.service'
            folder = self.old_root if old else self.root
            path = self.home / '.config/systemd/user' / args[3]
            output = f'ActiveState=inactive\nMainPID=0\nUnitFileState=disabled\nWorkingDirectory={folder}\nFragmentPath={path}\nDropInPaths=\n'.encode()
        elif args[:2] == ('launchctl', 'print'):
            code = 1
        elif args[:2] == ('launchctl', 'print-disabled'):
            output = b'"com.autocompany.loop" => true\n'
        return subprocess.CompletedProcess(args, code, output, b'')

    def unit(self, environment='Environment="AUTO_COMPANY_LANGUAGE=en"\n'):
        file = self.home / '.config/systemd/user/auto-company.service'
        file.parent.mkdir(parents=True)
        file.write_text(f'[Unit]\nDescription=Auto Company Loop\n[Service]\nWorkingDirectory={self.old_root}\n'
                        f'EnvironmentFile=-{self.old_root}/.auto-loop.env\n{environment}'
                        f'ExecStart=/usr/bin/bash "{self.old_root}/scripts/core/auto-loop.sh"\nRestart=always\nRestartSec=10\n')
        return file

    def test_systemd_stopped_definition_round_trip_preserves_custom_settings(self):
        old = self.unit()
        before = old.read_bytes()
        with mock.patch.object(M, 'run', side_effect=self.manager):
            value = M.prepare('systemd', self.old_root, self.root, self.manifest)
            self.assertEqual(old.read_bytes(), before)
            M.apply(self.manifest, value)
            M.apply(self.manifest, value)
            new = old.with_name('autonomous-company.service')
            self.assertFalse(old.exists())
            self.assertIn(b'Restart=always\nRestartSec=10\n', new.read_bytes())
            self.assertIn(b'AUTONOMOUS_COMPANY_LANGUAGE=en', new.read_bytes())
            self.assertIn(str(self.root).encode(), new.read_bytes())
            M.rollback(self.manifest, value)
            self.assertEqual(old.read_bytes(), before)
        self.assertFalse(any('start' in call or 'enable' in call for call in self.calls))

    def test_systemd_duplicate_brand_environment_is_rejected_without_replacement(self):
        old = self.unit('Environment="AUTO_COMPANY_LANGUAGE=en" "AUTONOMOUS_COMPANY_LANGUAGE=zh-CN"\n')
        before = old.read_bytes()
        with mock.patch.object(M, 'run', side_effect=self.manager):
            with self.assertRaisesRegex(ValueError, 'Conflicting'):
                M.prepare('systemd', self.old_root, self.root, self.manifest)
        self.assertEqual(old.read_bytes(), before)
        self.assertFalse(old.with_name('autonomous-company.service').exists())

    def test_launchd_keeps_restart_semantics_but_remains_unloaded_and_disabled(self):
        old = self.home / 'Library/LaunchAgents/com.autocompany.loop.plist'
        old.parent.mkdir(parents=True)
        original = {'Label': 'com.autocompany.loop', 'WorkingDirectory': str(self.old_root),
                    'ProgramArguments': ['/bin/bash', str(self.old_root / 'scripts/core/auto-loop.sh')],
                    'StandardOutPath': str(self.old_root / 'logs/stdout.log'), 'StandardErrorPath': str(self.old_root / 'logs/stderr.log'),
                    'RunAtLoad': True, 'KeepAlive': True,
                    'EnvironmentVariables': {'AUTO_COMPANY_LANGUAGE': 'en', 'CODEX_BIN': str(self.old_root / 'tool/codex')}}
        old.write_bytes(plistlib.dumps(original))
        with mock.patch.object(M.os, 'getuid', return_value=1000, create=True), mock.patch.object(M, 'run', side_effect=self.manager):
            value = M.prepare('launchd', self.old_root, self.root, self.manifest)
            M.apply(self.manifest, value)
            new = plistlib.loads(Path(value['new']).read_bytes())
            self.assertTrue(new['RunAtLoad'])
            self.assertTrue(new['KeepAlive'])
            self.assertEqual(new['StandardOutPath'], str(self.root / 'logs/stdout.log'))
            self.assertEqual(new['EnvironmentVariables']['CODEX_BIN'], str(self.root / 'tool/codex'))
            M.rollback(self.manifest, value)
            self.assertEqual(plistlib.loads(old.read_bytes()), original)
        self.assertTrue(any(call[:2] == ('launchctl', 'disable') for call in self.calls))
        self.assertFalse(any('bootstrap' in call or 'kickstart' in call for call in self.calls))

    def test_replaced_service_registration_is_not_overwritten(self):
        old = self.unit()
        with mock.patch.object(M, 'run', side_effect=self.manager):
            value = M.prepare('systemd', self.old_root, self.root, self.manifest)
            Path(value['new']).write_bytes(b'Another owner')
            with self.assertRaisesRegex(ValueError, 'changed'):
                M.apply(self.manifest, value)
            self.assertEqual(Path(value['new']).read_bytes(), b'Another owner')
            self.assertTrue(old.exists(), 'Target collision must not move the original registration')


@unittest.skipUnless(os.name == 'nt', 'Native Windows task XML path contracts')
class WindowsTaskMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.old_root, self.root = self.folder / 'old-runtime', self.folder / 'new-runtime'
        self.old_root.mkdir()
        self.root.mkdir()
        self.manifest = self.folder / 'task.json'
        xml = '<Task xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"><RegistrationInfo><URI>\\AutoCompany-WSL-Start</URI></RegistrationInfo><Settings><Enabled>false</Enabled></Settings><Actions><Exec><Command>powershell.exe</Command><Arguments>-File "' + str(self.old_root) + '\\scripts\\windows\\start-win.ps1"</Arguments></Exec></Actions></Task>'
        self.tasks = {M.OLD_TASK: xml.encode('utf-16')}
        self.original = self.tasks[M.OLD_TASK]
        self.calls = []

    def manager(self, *args, missing=False):
        self.calls.append(args)
        code, output = 0, b''
        if args[0] == 'schtasks.exe':
            name = args[args.index('/TN') + 1]
            if args[1] == '/Query':
                code = 0 if name in self.tasks else 1
                output = self.tasks.get(name, b'')
            elif args[1] == '/Create':
                self.assertNotIn(name, self.tasks, 'Create cannot overwrite an existing task')
                self.tasks[name] = Path(args[args.index('/XML') + 1]).read_bytes()
            elif args[1] == '/Delete':
                self.tasks.pop(name, None)
        return subprocess.CompletedProcess(args, code, output, b'')

    def test_disabled_task_round_trip_preserves_original_xml_without_force(self):
        with mock.patch.object(M, 'run', side_effect=self.manager):
            value = M.prepare('windows-task', self.old_root, self.root, self.manifest)
            M.apply(self.manifest, value)
            self.assertNotIn(M.OLD_TASK, self.tasks)
            M.rollback(self.manifest, value)
            self.assertEqual(self.tasks[M.OLD_TASK], self.original)
        self.assertFalse(any(('/Create' in args and '/F' in args) or '/Run' in args for args in self.calls))

    def test_new_task_created_after_plan_is_preserved_and_original_untouched(self):
        with mock.patch.object(M, 'run', side_effect=self.manager):
            value = M.prepare('windows-task', self.old_root, self.root, self.manifest)
            self.tasks[M.NEW_TASK] = b'Another task owner'
            with self.assertRaisesRegex(ValueError, 'appeared'):
                M.apply(self.manifest, value)
        self.assertEqual(self.tasks[M.OLD_TASK], self.original)
        self.assertEqual(self.tasks[M.NEW_TASK], b'Another task owner')


if __name__ == '__main__':
    unittest.main()
