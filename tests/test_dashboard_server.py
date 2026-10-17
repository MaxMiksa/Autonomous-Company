"""Old CLI names forward to the center; service ownership remains protected."""

import importlib.util
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

SERVER_PATH = Path(__file__).resolve().parents[1] / "dashboard/server.py"


class DashboardEntrypointTests(unittest.TestCase):
    def test_old_cli_names_forward_center_options_without_another_server(self):
        for name in ("server.py", "journal_server.py"):
            spec = importlib.util.spec_from_file_location("forward_" + name, SERVER_PATH.with_name(name))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            with mock.patch("center_server.main") as center:
                arguments = ["--port", "8877", "--data-dir", "isolated", "--source", "history"]
                module.main(arguments)
                center.assert_called_once_with(arguments)
            self.assertFalse(hasattr(module, "DashboardHandler"))
            self.assertFalse(hasattr(module, "JournalServer"))

    def test_remote_bind_is_rejected_before_server_creation(self):
        from center_server import main
        with self.assertRaises(SystemExit) as result:
            main(["--host", "0.0.0.0"])
        self.assertEqual(result.exception.code, 2)

    @unittest.skipUnless(platform.system() == "Linux", "Linux adapter uses Bash and /proc")
    def test_linux_service_adapter_requires_matching_checkout(self) -> None:
        source = SERVER_PATH.parents[1] / "scripts" / "wsl" / "dashboard-wsl.sh"
        fixture = Path(__file__).parent / "fixtures" / "fake-systemctl.sh"
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            adapter = root / "scripts" / "wsl" / "dashboard-wsl.sh"
            adapter.parent.mkdir(parents=True)
            shutil.copy2(source, adapter)
            (root / "scripts/core").mkdir()
            for name in ("ui-messages.sh", "localization.py", "namespace_guard.py", "stop-loop.sh", "loop-lock.py"):
                shutil.copy2(SERVER_PATH.parents[1] / "scripts/core" / name, root / "scripts/core" / name)
            shutil.copytree(SERVER_PATH.parents[1] / "i18n", root / "i18n")
            fake_bin = root / "bin"
            fake_bin.mkdir()
            shutil.copy2(fixture, fake_bin / "systemctl")
            (fake_bin / "systemctl").chmod(0o755)
            env = dict(os.environ, PATH=f"{fake_bin}:{os.environ['PATH']}",
                       FAKE_SERVICE_ROOT=str(root), FAKE_SERVICE_LOG=str(root / "actions"),
                       FAKE_SERVICE_STATE="active", FAKE_SERVICE_ENABLED="enabled")
            def run(action: str) -> subprocess.CompletedProcess:
                return subprocess.run(["bash", str(adapter), action], env=env,
                                      capture_output=True, text=True, timeout=10)
            for state in ("active", "inactive", "failed"):
                env["FAKE_SERVICE_STATE"] = state
                result = run("status")
                self.assertIn("=== Daemon ===\nState=" + state + "\n", result.stdout)
                self.assertIn("EnabledState=enabled", result.stdout)
            env["FAKE_SERVICE_STATE"] = "active"
            self.assertEqual(run("start").returncode, 0)
            self.assertEqual(run("stop").returncode, 0)
            self.assertEqual((root / "actions").read_text().splitlines(), ["start", "stop"])
            env["FAKE_SERVICE_ROOT"] = "/another/checkout"
            self.assertEqual(run("start").returncode, 3)
            self.assertEqual(run("stop").returncode, 3)
            self.assertIn("=== Daemon ===\nState=mismatched\n", run("status").stdout)
            self.assertEqual((root / "actions").read_text().splitlines(), ["start", "stop"])
            env["FAKE_SERVICE_MISSING"] = "1"
            self.assertEqual(run("start").returncode, 2)
            self.assertIn("make install", run("status").stdout)
            env.pop("FAKE_SERVICE_MISSING")
            shutil.copy2(SERVER_PATH.parents[1] / "Makefile", root / "Makefile")
            for name in ("usage.py", "usage_lib.py"):
                shutil.copy2(SERVER_PATH.parents[1] / "scripts/core" / name, root / "scripts/core" / name)
            pause = root / ".auto-loop-paused"
            budget = root / ".auto-loop-budget-paused"
            pause.write_text("operator marker\n")
            budget.write_text('{"reason":"usage_hard_limit"}')
            for target in ("pause", "resume"):
                result = subprocess.run(["make", target, "UNAME_S=Linux"], cwd=root,
                                        env=env, capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(pause.read_text(), "operator marker\n")
                self.assertEqual(budget.read_text(), '{"reason":"usage_hard_limit"}')
                self.assertEqual((root / "actions").read_text().splitlines(), ["start", "stop"])
            env["FAKE_SERVICE_ROOT"] = str(root)
            for target in ("pause", "resume"):
                result = subprocess.run(["make", target, "UNAME_S=Linux"], cwd=root,
                                        env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(pause.exists())
            self.assertFalse(budget.exists())
            self.assertEqual((root / "actions").read_text().splitlines(), ["start", "stop", "stop", "start"])


if __name__ == "__main__":
    unittest.main()
