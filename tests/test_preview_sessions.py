"""Real PTY and Linux cycle-owner checks for preview lifetime, without models."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/core"))
from runtime_artifacts import preview_request


@unittest.skipIf(os.name == "nt", "Real POSIX PTY suite; run through WSL on Windows")
class PreviewSessionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "projects/probe").mkdir(parents=True)
        self.env = dict(os.environ, AUTONOMOUS_COMPANY_ROOT=str(self.root), ACTIVE_PROJECT="projects/probe", AUTONOMOUS_COMPANY_CYCLE_ID="cycle-session")
        self.command = [sys.executable, str(ROOT / "scripts/core/runtime_artifacts.py"), "preview"]

    def record(self):
        for path in (self.root / "logs/artifacts").glob("*.json"):
            return json.loads(path.read_text())

    def wait_for_preview(self):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            record = self.record()
            if record and preview_request(record):
                return record
            time.sleep(0.02)
        self.fail("Preview did not become available")

    def test_foreground_pty_stays_usable_and_explicit_stop_exits_cleanly(self):
        import pty
        pid, terminal = pty.fork()
        if pid == 0:
            os.execve(sys.executable, self.command, self.env)
        reaped = False
        try:
            record = self.wait_for_preview()
            self.assertEqual(record["pid"], pid)
            time.sleep(0.3)
            self.assertTrue(preview_request(record))
            self.assertEqual(os.waitpid(pid, os.WNOHANG), (0, 0))
            # This is a separate command while the original tool session lives.
            result = subprocess.run([*self.command[:-1], "preview-stop"], env=self.env, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                child, status = os.waitpid(pid, os.WNOHANG)
                if child:
                    reaped = True
                    self.assertEqual(os.waitstatus_to_exitcode(status), 0)
                    break
                time.sleep(0.02)
            self.assertTrue(reaped)
            self.assertFalse(preview_request(record))
            self.assertEqual(self.record()["state"], "stopped")
        finally:
            if not reaped:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            os.close(terminal)

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux child subreaper ownership")
    def test_cycle_owner_cleans_real_pty_preview_and_keeps_unrelated_process(self):
        helper = self.root / "tool-session.py"
        helper.write_text(
            "import os,pty,sys,time\n"
            "pid,terminal=pty.fork()\n"
            "if pid == 0:\n"
            f" os.execve(sys.executable, {self.command!r}, os.environ.copy())\n"
            "while True: time.sleep(0.1)\n")
        result_path = self.root / "supervisor-result"
        sentinel = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        supervisor = subprocess.Popen([
            sys.executable, str(ROOT / "scripts/core/process-supervisor-linux.py"),
            str(result_path), "30", "2", "2", str(os.getpid()), str(self.root),
            sys.executable, str(helper)], env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            record = self.wait_for_preview()
            self.assertIsNone(supervisor.poll())
            supervisor.terminate()
            self.assertEqual(supervisor.wait(timeout=8), 0)
            self.assertEqual(result_path.read_text().split()[2], "0")
            self.assertFalse(Path(f"/proc/{record['pid']}").exists())
            self.assertFalse(preview_request(record))
            self.assertIsNone(sentinel.poll())
        finally:
            if supervisor.poll() is None:
                supervisor.terminate()
                supervisor.wait(timeout=8)
            supervisor.stderr.close()
            sentinel.terminate()
            sentinel.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
