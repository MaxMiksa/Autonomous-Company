"""Managed roots must reject legacy service/config writes before side effects."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == 'Windows', 'Native PowerShell entrypoints')
class CenterLegacyWindowsTests(unittest.TestCase):
    def test_managed_start_and_stop_reject_before_configuration_or_wsl(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / 'scripts/windows'
            scripts.mkdir(parents=True)
            # No WSL invocation is allowed: the marker must be checked first.
            (scripts / 'messages-win.ps1').write_text(
                'function Get-AutonomousCompanyMessage { param($Key) return $Key }\n')
            (root / '.autonomous-company-center.json').write_text('{}')
            (root / '.auto-loop.env').write_text('PROTECTED=original\n')
            for script in ('start-win.ps1', 'stop-win.ps1'):
                shutil.copyfile(ROOT / 'scripts/windows' / script, scripts / script)
                result = subprocess.run(
                    ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(scripts / script)],
                    cwd=root, capture_output=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b'This runtime is managed by the product center', result.stdout + result.stderr)
            self.assertEqual((root / '.auto-loop.env').read_text(), 'PROTECTED=original\n')
            self.assertFalse((root / '.autonomous-company.local').exists())
            self.assertFalse((root / '.auto-loop-stop').exists())


@unittest.skipIf(platform.system() == 'Windows', 'POSIX wrappers must run under WSL/Linux/macOS')
class CenterLegacyShellTests(unittest.TestCase):
    def test_managed_service_wrappers_exit_before_host_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = ('scripts/macos/start-daemon.sh', 'scripts/macos/install-daemon.sh',
                       'scripts/wsl/install-wsl-daemon.sh', 'scripts/wsl/dashboard-wsl.sh')
            for script in scripts:
                destination = root / script
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / script, destination)
            messages = root / 'scripts/core/ui-messages.sh'
            messages.parent.mkdir(parents=True)
            messages.write_text('ui_message() { echo "$1"; }\nif [ "${BASH_SOURCE[0]}" = "$0" ]; then ui_message "$@"; fi\n')
            (root / '.autonomous-company-center.json').write_text('{}')
            for script in scripts:
                arguments = ('start', 'stop', 'check') if script.endswith('dashboard-wsl.sh') else ('',)
                for argument in arguments:
                    with self.subTest(script=script, argument=argument):
                        command = ['bash', str(root / script)] + ([argument] if argument else [])
                        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=5)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('center.managed', result.stdout + result.stderr)
            self.assertFalse((root / '.auto-loop-stop').exists())
            self.assertFalse((root / '.auto-loop-paused').exists())


if __name__ == '__main__':
    unittest.main()
