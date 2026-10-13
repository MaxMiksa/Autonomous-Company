"""Offline project-operation coordination and failure ownership regressions."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
HEADER = "name\tpath\tlifecycle\tcreated_at_utc\n"


@unittest.skipIf(os.name == "nt", "POSIX project commands run under Linux/WSL and macOS")
class ProjectRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="project-registry-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "Framework with spaces"
        shutil.copytree(ROOT / "scripts/core", self.root / "scripts/core")
        shutil.copy2(ROOT / ".gitignore", self.root / ".gitignore")
        (self.root / "projects").mkdir()
        self.registry = self.root / "projects/registry.tsv"
        self.registry.write_text(HEADER)
        self.initialize_git(self.root)
        self.git("add", "projects/registry.tsv")
        self.bin = Path(self.temp.name) / "bin"
        self.bin.mkdir()
        self.env = {**os.environ, "AUTONOMOUS_COMPANY_ROOT": str(self.root), "PYTHONDONTWRITEBYTECODE": "1",
                    "PATH": str(self.bin) + os.pathsep + os.environ["PATH"]}
        for name in ("AUTONOMOUS_COMPANY_CYCLE", "AUTONOMOUS_COMPANY_CYCLE_ID", "AUTONOMOUS_COMPANY_PROJECT_LOCK_PID", "ACTIVE_PROJECT"):
            self.env.pop(name, None)
        # Only delay/fail the selected boundary. Every other helper, including
        # the real state transaction and command-wide lock, executes unchanged.
        wrapper = self.bin / "python3"
        wrapper.write_text("#!" + sys.executable + "\n" + '''import os, pathlib, subprocess, sys, time
root = pathlib.Path(os.environ["AUTONOMOUS_COMPANY_ROOT"])
args = sys.argv[1:]
script = pathlib.Path(args[0]).name
if os.environ.get("SECONDARY") == "1":
    (root / "secondary-entered").touch()
if script == "project_metadata.py":
    result = subprocess.run([sys.executable, *args])
    project = args[args.index("--project") + 1].split("/")[-1]
    (root / ("metadata-" + project)).touch()
    if project == os.environ.get("DELAY_METADATA"):
        deadline = time.monotonic() + 8
        while not (root / "release-metadata").exists():
            if time.monotonic() >= deadline:
                sys.exit("fixture metadata barrier timed out")
            time.sleep(0.01)
    sys.exit(result.returncode)
if script == "product_identity.py" and "register" in args:
    mode = os.environ.get("FAIL_REGISTRATION", "")
    registry = root / "projects/registry.tsv"
    if mode == "external-row":
        with registry.open("a") as output:
            output.write("external\\tprojects/external\\tlocal\\tunknown\\n")
        sys.exit(7)
    if mode == "changed-row":
        registry.write_text(registry.read_text().replace("\\tlocal\\t", "\\tpublished\\t"))
        sys.exit(7)
    if mode == "after-commit":
        subprocess.run([sys.executable, *args], check=True)
        sys.exit(7)
os.execv(sys.executable, [sys.executable, *args])
''')
        wrapper.chmod(0o755)
        self.processes = []
        self.addCleanup(self.cleanup_processes)

    def cleanup_processes(self):
        (self.root / "release-metadata").touch()
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
            process.communicate(timeout=12)

    def project(self, *args, env=None):
        return subprocess.run(["/bin/bash", str(self.root / "scripts/core/project.sh"), *args],
                              env={**self.env, **(env or {})}, capture_output=True, text=True, timeout=20)

    def spawn(self, *args, env=None):
        process = subprocess.Popen(["/bin/bash", str(self.root / "scripts/core/project.sh"), *args],
                                   env={**self.env, **(env or {})}, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        self.processes.append(process)
        return process

    def finish(self, process):
        output, error = process.communicate(timeout=15)
        return subprocess.CompletedProcess(process.args, process.returncode, output, error)

    def wait_file(self, name):
        deadline = time.monotonic() + 6
        while not (self.root / name).exists():
            if time.monotonic() >= deadline:
                self.fail("fixture did not reach " + name)
            time.sleep(0.01)

    def overlap(self, arguments):
        first = self.spawn("new", "--name", "candidate", env={"DELAY_METADATA": "candidate"})
        self.wait_file("metadata-candidate")
        second = self.spawn(*arguments, env={"SECONDARY": "1"})
        self.wait_file("secondary-entered")
        # Old code completes the competing operation at this barrier; fixed
        # code must keep it outside the registry/source mutation boundary.
        deadline = time.monotonic() + 1
        while second.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        (self.root / "release-metadata").touch()
        return self.finish(first), self.finish(second)

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def rows(self):
        return {row.split("\t")[0]: row.split("\t") for row in self.registry.read_text().splitlines()[1:]}

    def assert_valid(self, name):
        result = subprocess.run([sys.executable, str(self.root / "scripts/core/project-context.py"),
                                 "validate", "--root", str(self.root), "--project", name],
                                capture_output=True, text=True, timeout=10)
        self.assert_ok(result)
        state = json.loads((self.root / ".autonomous-company/product-state.json").read_text())
        self.assertIn("projects/" + name, state["paths"])

    def git(self, *args, root=None):
        result = subprocess.run(["git", "-C", str(root or self.root), *args],
                                capture_output=True, text=True, timeout=15)
        self.assert_ok(result)
        return result.stdout

    def initialize_git(self, root):
        self.git("init", "--initial-branch=main", root=root)
        self.git("config", "user.name", "Registry Fixture", root=root)
        self.git("config", "user.email", "fixture@example.invalid", root=root)

    def legacy(self):
        target = self.root / "projects/legacy"
        target.mkdir()
        (target / "app.txt").write_text("legacy source\n")
        self.registry.write_text(HEADER + "legacy\tprojects/legacy\tlegacy-tracked\tunknown\n")
        self.initialize_git(self.root)
        self.git("add", ".gitignore", "projects/registry.tsv")
        self.git("add", "-f", "projects/legacy/app.txt")
        self.git("commit", "-m", "fixture baseline")
        return target

    def test_concurrent_exploration_registration_keeps_the_successful_product(self):
        result = subprocess.run([sys.executable, str(self.root / "scripts/core/product_identity.py"),
                                 "--root", str(self.root), "reserve", "--attempt", "explore-1", "--run-cycle", "1"],
                                capture_output=True, text=True, timeout=10)
        self.assert_ok(result)
        self.env.update(AUTONOMOUS_COMPANY_CYCLE="1", AUTONOMOUS_COMPANY_CYCLE_ID=json.loads(result.stdout)["cycleId"])
        first, second = self.overlap(("new", "--name", "second"))
        self.assertEqual(sorted([first.returncode, second.returncode]), [0, 1], first.stderr + second.stderr)
        winner = "candidate" if first.returncode == 0 else "second"
        loser = "second" if winner == "candidate" else "candidate"
        self.assertEqual(set(self.rows()), {winner})
        self.assert_valid(winner)
        self.assertFalse((self.root / "projects" / loser).exists())

    def test_concurrent_independent_creations_both_remain_registered(self):
        first, second = self.overlap(("new", "--name", "second"))
        self.assert_ok(first)
        self.assert_ok(second)
        self.assertEqual(set(self.rows()), {"candidate", "second"})
        for name in self.rows():
            self.assert_valid(name)

    def test_failed_registration_removes_only_its_own_row(self):
        result = self.project("new", "--name", "failed", env={"FAIL_REGISTRATION": "external-row"})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.registry.read_text(), HEADER + "external\tprojects/external\tlocal\tunknown\n")
        self.assertFalse((self.root / "projects/failed").exists())
        self.assertEqual(list((self.root / "projects").glob(".registry*")), [])

    def test_changed_own_row_is_retained_with_its_source_for_review(self):
        result = self.project("new", "--name", "changed", env={"FAIL_REGISTRATION": "changed-row"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changed", self.rows())
        self.assertEqual(self.rows()["changed"][2], "published")
        self.assertTrue((self.root / "projects/changed/.git").is_dir())
        self.assertIn("retained source and registry", result.stderr)

    def test_failure_after_committed_identity_preserves_recoverable_product(self):
        result = self.project("new", "--name", "committed", env={"FAIL_REGISTRATION": "after-commit"})
        self.assertNotEqual(result.returncode, 0)
        self.assert_valid("committed")
        self.assertTrue((self.root / "projects/committed/.git").is_dir())
        self.assertIn("retained source and registry", result.stderr)

    def test_early_git_failure_cleans_only_new_source_and_releases_lock(self):
        fake_git = self.bin / "git"
        fake_git.write_text("#!/bin/sh\nexit 7\n")
        fake_git.chmod(0o755)
        result = self.project("new", "--name", "failed")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "projects/failed").exists())
        self.assertEqual(self.registry.read_text(), HEADER)
        self.assertNotIn("unbound variable", result.stderr)
        fake_git.unlink()
        self.assert_ok(self.project("new", "--name", "failed"))
        self.assert_valid("failed")

    def test_busy_operation_fails_before_mutation_and_can_retry(self):
        import fcntl
        folder = self.root / ".autonomous-company"
        folder.mkdir()
        with (folder / "project-registry.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            result = self.project("new", "--name", "blocked")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("retry after it completes", result.stderr)
            self.assertEqual(self.registry.read_text(), HEADER)
            self.assertFalse((self.root / "projects/blocked").exists())
        self.assert_ok(self.project("new", "--name", "blocked"))
        self.assert_valid("blocked")

    def test_concurrent_publish_does_not_lose_lifecycle_update(self):
        self.assert_ok(self.project("new", "--name", "existing"))
        target = self.root / "projects/existing"
        self.initialize_git(target)
        self.git("add", ".", root=target)
        self.git("commit", "-m", "local fixture", root=target)
        remote = Path(self.temp.name) / "remote.git"
        self.git("init", "--bare", str(remote))
        first, published = self.overlap(("publish", "--project", "existing", "--remote-url", str(remote), "--confirm", "PUBLISH"))
        self.assert_ok(first)
        self.assert_ok(published)
        self.assertEqual(self.rows()["existing"][2], "published")
        self.assert_valid("candidate")

    def test_migration_rechecks_clean_registry_after_waiting_for_creation(self):
        target = self.legacy()
        first, migration = self.overlap(("migrate-legacy", "--name", "legacy", "--confirm", "MIGRATE"))
        self.assert_ok(first)
        self.assertNotEqual(migration.returncode, 0)
        self.assertIn("tracked worktree must be clean", migration.stderr)
        self.assertEqual(self.rows()["legacy"][2], "legacy-tracked")
        self.assertFalse((target / ".git").exists())
        self.assertFalse((self.root / ".autonomous-company-migrations").exists())
        self.assert_valid("candidate")

    def test_migration_rollback_preserves_later_registration(self):
        target = self.legacy()
        self.assert_ok(self.project("migrate-legacy", "--name", "legacy", "--confirm", "MIGRATE"))
        first, rollback = self.overlap(("migrate-rollback", "--name", "legacy", "--confirm", "ROLLBACK"))
        self.assert_ok(first)
        self.assertNotEqual(rollback.returncode, 0)
        self.assertIn("registry changed after migration", rollback.stderr)
        self.assertEqual(self.rows()["legacy"][2], "migration-staged")
        self.assertTrue((target / ".git").is_dir())
        self.assert_valid("candidate")


if __name__ == "__main__":
    unittest.main()
