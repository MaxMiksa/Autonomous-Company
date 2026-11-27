"""Real kernel boundaries and transactional collection (no sandbox stubs)."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/core"))
import project_isolation as boundary
import isolation_workspace as workspace
from product_identity import read_state, reserve_cycle
from runtime_artifacts import base_record, run_check, save


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "projects/sample").mkdir(parents=True)
        (self.root / "projects/sample/value.txt").write_text("original")
        (self.root / "projects/registry.tsv").write_text("name\tpath\tlifecycle\tcreated_at_utc\nsample\tprojects/sample\tlocal\t2026-10-02\n")
        (self.root / "memories").mkdir()
        (self.root / "memories/consensus.md").write_text("# Legacy\n\n## Current Phase\nOTHER_PROJECT_CANARY\n\n## Human Overrides\n- keep\n\n## Priority Issues\n- none\n")
        self.view = workspace.CompanyView(self.root, "projects/sample", "cycle-probe")
        with patch.object(workspace, "TEMPLATES", ()):
            self.view.prepare()

    def tearDown(self):
        shutil.rmtree(self.view.folder, ignore_errors=True)
        self.temporary.cleanup()

    def test_foreign_artifact_refuses_before_any_host_mutation(self):
        (self.view.workspace / "projects/sample/value.txt").write_text("new")
        artifacts = self.view.workspace / "logs/artifacts"
        artifacts.mkdir()
        (artifacts / ("a" * 32 + ".json")).write_text(json.dumps({"cycleId": "another", "project": "projects/other"}))
        with self.assertRaises(boundary.IsolationError):
            self.view.collect()
        self.assertEqual((self.root / "projects/sample/value.txt").read_text(), "original")
        self.assertFalse((self.root / ".autonomous-company/isolation-pending.json").exists())

    def test_unknown_consensus_has_only_governance_input(self):
        body = (self.view.workspace / "memories/consensus.md").read_text()
        self.assertNotIn("OTHER_PROJECT_CANARY", body)
        self.assertIn("- keep", body)

    def test_current_output_is_collected_and_old_logs_are_not_overwritten(self):
        (self.root / "logs").mkdir()
        (self.root / "logs/old.json").write_text("old")
        (self.view.workspace / "logs/old.json").write_text("poison")
        (self.view.workspace / "projects/sample/value.txt").write_text("new")
        self.view.collect()
        self.assertEqual((self.root / "projects/sample/value.txt").read_text(), "new")
        self.assertEqual((self.root / "logs/old.json").read_text(), "old")
        self.assertFalse((self.root / ".autonomous-company/isolation-pending.json").exists())

    def test_interrupted_collection_is_recoverable_and_blocks_restart(self):
        ready = self.view.store / "collect-recovery"
        ready.mkdir()
        (ready / "candidate").write_text("new")
        target = self.root / "projects/sample/value.txt"
        original_rename = Path.rename
        def fail_second(path, destination):
            if path == ready / "candidate":
                raise OSError("synthetic interruption")
            return original_rename(path, destination)
        with patch.object(Path, "rename", fail_second):
            with self.assertRaises(boundary.IsolationError):
                workspace.collect_transaction(self.root, ready, [(ready / "candidate", target)])
        with self.assertRaises(boundary.IsolationError):
            workspace.CompanyView(self.root, "projects/sample", "next")
        workspace.recover_collection(self.root)
        self.assertEqual(target.read_text(), "original")
        self.assertEqual((ready / "candidate").read_text(), "new")

    def test_uncollected_root_output_retains_private_view(self):
        (self.view.workspace / "acceptance.json").write_text('{"result": "actual"}')
        self.view.collect()
        self.assertTrue(self.view.retain_view)
        record = json.loads((self.view.store / "last-run.json").read_text())
        self.assertEqual(record["uncollectedRootOutputs"], ["acceptance.json"])
        self.assertEqual((Path(record["workspace"]) / "workspace/acceptance.json").read_text(), '{"result": "actual"}')
        self.assertFalse((self.root / "acceptance.json").exists())

    def test_collected_preview_cannot_contact_host_service(self):
        artifact = {"id": "a" * 32, "version": 1, "source": "runner", "kind": "preview", "state": "running",
                    "cycleId": self.view.cycle, "project": self.view.project, "url": "http://127.0.0.1:23456/", "token": "b" * 32}
        source = self.view.workspace / "logs/artifacts" / (artifact["id"] + ".json")
        workspace.write_json(source, artifact)
        self.view.collect()
        target = self.root / source.relative_to(self.view.workspace)
        self.assertEqual(json.loads(target.read_text())["state"], "stopped")
        original, = self.view.store.glob("collect-*/original-preview-records/*.json")
        self.assertEqual(json.loads(original.read_text()), artifact)
        from runtime_artifacts import finalize
        with patch("runtime_artifacts.preview_request") as request:
            finalize(self.root, self.view.cycle, capture=False)
            request.assert_not_called()


class ExplorationArtifactCollectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)

    def make_view(self, name="exploration", project=""):
        root = self.base / name
        (root / "projects").mkdir(parents=True)
        registry = "name\tpath\tlifecycle\tcreated_at_utc\n"
        if project:
            (root / project).mkdir()
            registry += "sample\tprojects/sample\tlocal\t2026-10-23\n"
        (root / "projects/registry.tsv").write_text(registry)
        cycle = reserve_cycle(root, project, "artifact-attempt", 1)["cycleId"]
        view = workspace.CompanyView(root, project, cycle)
        self.addCleanup(shutil.rmtree, view.folder, ignore_errors=True)
        with patch.object(workspace, "TEMPLATES", ()):
            view.prepare()
        return root, view

    def check_record(self, view):
        with patch.dict(os.environ, {"AUTONOMOUS_COMPANY_CYCLE_ID": view.cycle}):
            record = base_record("", "check", view.workspace)
        record.update(state="completed", exitCode=0)
        return record

    def assert_refused(self, root, view):
        before = read_state(root)
        (view.workspace / "docs/candidate.txt").write_text("candidate")
        with self.assertRaises(boundary.IsolationError):
            view.collect()
        self.assertFalse(view.collected)
        self.assertEqual(read_state(root), before)
        self.assertFalse((root / "logs/artifacts").exists())
        self.assertFalse((view.store / "docs/candidate.txt").exists())
        self.assertFalse((root / ".autonomous-company/isolation-pending.json").exists())

    @unittest.skipUnless(sys.platform == "linux" and (os.environ.get("AUTONOMOUS_COMPANY_BWRAP") or shutil.which("bwrap")),
                         "Requires real Linux namespaces and bubblewrap; no emulation")
    def test_real_exploration_checks_preserve_success_and_failure_observations(self):
        for code in (0, 3):
            with self.subTest(exit_code=code):
                root, view = self.make_view("check-" + str(code))
                record = self.check_record(view)
                arguments = Namespace(adapter="exit-code", report=None,
                    command=[sys.executable, "-c", "from pathlib import Path; Path('docs/check-output.txt').write_text('actual check'); raise SystemExit(" + str(code) + ")"])
                self.assertEqual(run_check(view.workspace, view.workspace, record, arguments), code)
                source = view.workspace / "logs/artifacts" / (record["id"] + ".json")
                original = source.read_bytes()
                self.assertEqual(record["productId"], view.scope)
                self.assertEqual(record["state"], "completed")
                view.collect()
                self.assertEqual((root / "logs/artifacts" / source.name).read_bytes(), original)
                self.assertEqual((view.store / "docs/check-output.txt").read_text(), "actual check")
                journal, = view.store.glob("collect-*/collection.json")
                self.assertIn("logs/artifacts/" + source.name,
                              [item["target"] for item in json.loads(journal.read_text())["operations"]])

    def test_exploration_exception_requires_exact_cycle_identity_and_check_kind(self):
        changes = ({"cycleId": "cycle-foreign"}, {"project": "projects/other"},
                   {"productId": "f" * 32}, {"productId": None}, {"id": "f" * 32},
                   {"kind": "document"}, {"kind": "preview", "state": "running"},
                   {"version": 2}, {"source": "agent"})
        for index, change in enumerate(changes):
            with self.subTest(change=change):
                root, view = self.make_view("foreign-" + str(index))
                record = self.check_record(view)
                filename = record["id"] + ".json"
                record.update(change)
                workspace.write_json(view.workspace / "logs/artifacts" / filename, record)
                self.assert_refused(root, view)

    def test_exploration_exception_requires_original_reservation_and_scope(self):
        for change in ("missing-cycle", "wrong-scope", "wrong-owner"):
            with self.subTest(change=change):
                root, view = self.make_view(change)
                save(view.workspace, self.check_record(view))
                if change == "missing-cycle":
                    view.initial["cycles"].clear()
                elif change == "wrong-scope":
                    view.scope = "f" * 32
                else:
                    view.initial["explorationId"] = "f" * 32
                self.assert_refused(root, view)

    def test_product_cycle_cannot_collect_empty_project_check(self):
        root, view = self.make_view("product", "projects/sample")
        record = self.check_record(view)
        record["productId"] = view.scope
        save(view.workspace, record)
        self.assert_refused(root, view)

    def test_exploration_check_cannot_overwrite_host_observation(self):
        root, view = self.make_view()
        record = self.check_record(view)
        save(view.workspace, record)
        target = root / "logs/artifacts" / (record["id"] + ".json")
        target.parent.mkdir(parents=True)
        target.write_bytes(b"historical observation")
        with self.assertRaisesRegex(boundary.IsolationError, "overwrite"):
            view.collect()
        self.assertEqual(target.read_bytes(), b"historical observation")
        self.assertFalse(view.collected)

    def test_governance_violation_holds_back_product_and_docs_on_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "gov-host"
            (root / "projects/sample").mkdir(parents=True)
            (root / "projects/sample/value.txt").write_text("original")
            (root / "projects/registry.tsv").write_text("name\tpath\tlifecycle\tcreated_at_utc\nsample\tprojects/sample\tlocal\t2026-10-02\n")
            (root / "memories").mkdir()
            (root / "memories/consensus.md").write_text(
                "# Legacy\n\n## Current Phase\nBuilding\n\n## Human Overrides\n- keep-me\n\n## Priority Issues\n- None.\n"
            )
            view = workspace.CompanyView(root, "projects/sample", "gov-holdback")
            self.addCleanup(shutil.rmtree, view.folder, ignore_errors=True)
            with patch.object(workspace, "TEMPLATES", ()):
                view.prepare()
            (view.workspace / "projects/sample/value.txt").write_text("rogue-edit")
            (view.workspace / "docs").mkdir(exist_ok=True)
            (view.workspace / "docs/rogue.md").write_text("rogue doc")
            (view.workspace / "memories/consensus.md").write_text(
                "# Legacy\n\n## Current Phase\nBuilding\n\n## Human Overrides\n- tampered\n\n## Priority Issues\n- None.\n"
            )
            view.collect()
            self.assertTrue(view.collected)
            self.assertTrue(view.retain_view)
            self.assertEqual((root / "projects/sample/value.txt").read_text(), "original")
            self.assertFalse((root / "docs/rogue.md").exists())
            record = json.loads((view.store / "last-run.json").read_text())
            self.assertTrue(record["governanceViolationHeldBack"])
            self.assertIn("- tampered", (root / "memories/consensus.md").read_text())

    def test_harness_governance_violation_holds_back_consensus_and_ignores_new_git_in_expected_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "harness-gov"
            (root / "projects/sample").mkdir(parents=True)
            (root / "projects/sample/value.txt").write_text("original")
            (root / "projects/registry.tsv").write_text("name\tpath\tlifecycle\tcreated_at_utc\nsample\tprojects/sample\tlocal\t2026-10-02\n")
            (root / "memories").mkdir()
            consensus_text = "# Legacy\n\n## Current Phase\nBuilding\n\n## Human Overrides\n- keep-me\n\n## Priority Issues\n- None.\n"
            (root / "memories/consensus.md").write_text(consensus_text)
            with patch.dict(os.environ, {"COMPANY_HARNESS_ENABLED": "1", "AUTONOMOUS_COMPANY_ATTEMPT_ID": "att-gov-1"}):
                for mode in ("deleted", "mutated"):
                    with self.subTest(mode=mode):
                        view = workspace.CompanyView(root, "projects/sample", f"gov-{mode}")
                        self.addCleanup(shutil.rmtree, view.folder, ignore_errors=True)
                        with patch.object(workspace, "TEMPLATES", ()):
                            view.prepare()
                        (view.workspace / "projects/sample/value.txt").write_text(f"rogue-{mode}")
                        # Adding .git inside workspace before collect must still match pre-collect expected_versions.
                        subprocess.run(["git", "-C", str(view.workspace / "projects/sample"), "init", "-q"], check=True)
                        versions = {name: workspace.fingerprint(view.workspace / name) for name in ("projects", "docs", "memories")}
                        target = view.workspace / "memories/consensus.md"
                        if mode == "deleted":
                            target.unlink()
                            # Recompute memories digest only so post_submission_change reflects deletion vs expected_versions check separately.
                            expected = None
                        else:
                            target.write_text(consensus_text.replace("- keep-me", "- tampered"))
                            expected = {**versions, "memories": workspace.fingerprint(view.workspace / "memories")}
                        view.expected_versions = expected
                        view.collect()
                        view.active_record.unlink(missing_ok=True)
                        self.assertTrue(view.governance_violation)
                        self.assertEqual(view.governance_reason, "human_override_mutated")
                        self.assertFalse(view.post_submission_change)
                        self.assertEqual((root / "memories/consensus.md").read_text(), consensus_text)
                        self.assertEqual((root / "projects/sample/value.txt").read_text(), "original")
                # Clean consensus + newly added .git preserves expected_versions match without false postSubmissionChange.
                view_ok = workspace.CompanyView(root, "projects/sample", "gov-clean-git")
                self.addCleanup(shutil.rmtree, view_ok.folder, ignore_errors=True)
                with patch.object(workspace, "TEMPLATES", ()):
                    view_ok.prepare()
                subprocess.run(["git", "-C", str(view_ok.workspace / "projects/sample"), "init", "-q"], check=True)
                view_ok.expected_versions = {name: workspace.fingerprint(view_ok.workspace / name) for name in ("projects", "docs", "memories")}
                view_ok.collect()
                view_ok.active_record.unlink(missing_ok=True)
                self.assertFalse(view_ok.governance_violation)
                self.assertFalse(view_ok.post_submission_change)

    def test_legacy_consensus_deletion_propagates_empty_file_for_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "legacy-del"
            (root / "projects/sample").mkdir(parents=True)
            (root / "projects/registry.tsv").write_text("name\tpath\tlifecycle\tcreated_at_utc\nsample\tprojects/sample\tlocal\t2026-10-02\n")
            (root / "memories").mkdir()
            (root / "memories/consensus.md").write_text("# Legacy\n\n## Human Overrides\n- keep-me\n\n## Priority Issues\n- None.\n")
            with patch.dict(os.environ, {"COMPANY_HARNESS_ENABLED": "0"}):
                view = workspace.CompanyView(root, "projects/sample", "legacy-del-1")
                self.addCleanup(shutil.rmtree, view.folder, ignore_errors=True)
                with patch.object(workspace, "TEMPLATES", ()):
                    view.prepare()
                (view.workspace / "memories/consensus.md").unlink()
                view.collect()
            self.assertTrue(view.governance_violation)
            self.assertEqual((root / "memories/consensus.md").read_bytes(), b"")

    def test_run_engine_fails_closed_if_acceptance_version_read_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fail-closed"
            for name in workspace.TEMPLATES:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
            (root / "projects/sample").mkdir(parents=True)
            (root / "projects/sample/value.txt").write_text("original")
            (root / "projects/registry.tsv").write_text(
                "name\tpath\tlifecycle\tcreated_at_utc\nsample\tprojects/sample\tlocal\t2026-10-02\n"
            )
            (root / "memories").mkdir(exist_ok=True)
            (root / "memories/consensus.md").write_text(
                "# Legacy\n\n## Current Phase\nBuilding\n\n## Human Overrides\n- keep-me\n\n## Priority Issues\n- None.\n"
            )
            sock = root / "harness.sock"
            inputs = root / "inputs"
            inputs.mkdir()
            manifest_path = root / "attempt-manifest.json"
            manifest_path.write_text(json.dumps({
                "root": str(root),
                "context": {"cycleId": "cycle-fc-1", "attemptId": "att-fc-1", "generation": "gen-1"},
                "token": "tok",
                "socket": str(sock),
                "inputsDirectory": str(inputs),
                "recovery": False,
                "collectRelative": ".autonomous-company/harness/att-fc-1.collect.json",
            }))
            fake_bin = root / "fake-codex"
            fake_bin.write_text("#!/bin/sh\nexit 0\n")
            with patch.dict(os.environ, {
                "COMPANY_HARNESS_ENABLED": "1",
                "AUTONOMOUS_COMPANY_CYCLE_ID": "cycle-fc-1",
                "AUTONOMOUS_COMPANY_ATTEMPT_ID": "att-fc-1",
                "COMPANY_HARNESS_MANIFEST": str(manifest_path),
            }), patch.object(workspace, "runtime_binary", return_value=Path("/usr/bin/bwrap")), \
                 patch.object(workspace, "TEMPLATES", ()), \
                 patch.object(workspace, "run_isolated", return_value=0), \
                 patch("company_harness.HarnessStore.snapshot", side_effect=OSError("corrupt db")):
                with self.assertRaisesRegex(boundary.IsolationError, "accepted submission versions"):
                    workspace.run_engine(root, "projects/sample", "codex", str(fake_bin), "prompt")
            self.assertEqual((root / "projects/sample/value.txt").read_text(), "original")

    def test_run_engine_fails_closed_when_cycle_missing_or_acceptance_versions_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fail-closed-invalid"
            for name in workspace.TEMPLATES:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
            (root / "projects/sample").mkdir(parents=True)
            (root / "projects/sample/value.txt").write_text("original")
            (root / "projects/registry.tsv").write_text(
                "name\tpath\tlifecycle\tcreated_at_utc\nsample\tprojects/sample\tlocal\t2026-10-02\n"
            )
            (root / "memories").mkdir(exist_ok=True)
            (root / "memories/consensus.md").write_text(
                "# Legacy\n\n## Current Phase\nBuilding\n\n## Human Overrides\n- keep-me\n\n## Priority Issues\n- None.\n"
            )
            inputs = root / "inputs"
            inputs.mkdir()
            manifest_path = root / "attempt-manifest.json"
            manifest_path.write_text(json.dumps({
                "root": str(root),
                "context": {"cycleId": "cycle-fc-2", "attemptId": "att-fc-2", "generation": "gen-2"},
                "token": "tok",
                "socket": str(root / "harness.sock"),
                "inputsDirectory": str(inputs),
                "recovery": False,
                "collectRelative": ".autonomous-company/harness/att-fc-2.collect.json",
            }))
            fake_bin = root / "fake-codex"
            fake_bin.write_text("#!/bin/sh\nexit 0\n")
            for snap in (
                {"cycles": []},
                {"cycles": [{"cycleId": "cycle-fc-2", "submissions": [{"attemptId": "att-fc-2", "submissionId": "sub-1", "acceptanceVersions": None}]}]},
            ):
                with self.subTest(snap=snap), patch.dict(os.environ, {
                    "COMPANY_HARNESS_ENABLED": "1",
                    "AUTONOMOUS_COMPANY_CYCLE_ID": "cycle-fc-2",
                    "AUTONOMOUS_COMPANY_ATTEMPT_ID": "att-fc-2",
                    "COMPANY_HARNESS_MANIFEST": str(manifest_path),
                }), patch.object(workspace, "runtime_binary", return_value=Path("/usr/bin/bwrap")), \
                     patch.object(workspace, "TEMPLATES", ()), \
                     patch.object(workspace, "run_isolated", return_value=0), \
                     patch("company_harness.HarnessStore.snapshot", return_value=snap):
                    with self.assertRaises(boundary.IsolationError):
                        workspace.run_engine(root, "projects/sample", "codex", str(fake_bin), "prompt")
                    self.assertEqual((root / "projects/sample/value.txt").read_text(), "original")

    def test_chunked_copy_and_fingerprint_handle_multichunk_regular_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "chunk-src"
            dst = Path(tmp) / "chunk-dst"
            src.mkdir()
            payload = (b"A1-chunk-boundary-" * 12000)  # > 200 KiB
            (src / "large.bin").write_bytes(payload)
            workspace.copy_tree(src, dst)
            self.assertEqual((dst / "large.bin").read_bytes(), payload)
            self.assertEqual(workspace.fingerprint(src), workspace.fingerprint(dst))
            os.link(src / "large.bin", src / "hardlink.bin")
            with self.assertRaises(boundary.IsolationError):
                workspace.fingerprint(src)


@unittest.skipUnless(sys.platform == "linux" and (os.environ.get("AUTONOMOUS_COMPANY_BWRAP") or shutil.which("bwrap")),
                     "Requires real Linux namespaces and bubblewrap; no emulation")
class KernelTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.project = self.base / "project"
        self.project.mkdir()
        (self.base / "other").mkdir()
        (self.base / "other/canary").write_text("synthetic")

    def tearDown(self):
        self.temporary.cleanup()

    def test_inheritance_and_normal_io(self):
        script = f'''import os,pathlib,subprocess,sys
assert not pathlib.Path({str(self.base / 'other')!r}).exists()
assert not pathlib.Path('/mnt/d').exists()
assert not pathlib.Path('/home/max').exists()
assert subprocess.run([sys.executable,'-c',"import pathlib; assert not pathlib.Path({str(self.base / 'other/canary')!r}).exists()"]).returncode == 0
pathlib.Path('/workspace/success').write_text('yes')
'''
        (self.project / "check.py").write_text(script)
        self.assertEqual(boundary.run_isolated(["/usr/bin/python3", "/workspace/check.py"], self.project), 0)
        self.assertEqual((self.project / "success").read_text(), "yes")

    @unittest.skipUnless(shutil.which("node"), "Native Node runtime is required")
    def test_selected_node_binary_is_mounted_without_its_tool_cache(self):
        cache = self.base / "tool-cache"
        cache.mkdir()
        shutil.copy2(Path(shutil.which("node")).resolve(), cache / "node")
        (cache / "private-cache-file").write_text("synthetic")
        script = ("const fs=require('node:fs');"
                  "if(process.execPath!=='/opt/runtime/node') process.exit(2);"
                  f"if(fs.existsSync({json.dumps(str(cache / 'private-cache-file'))})) process.exit(3);"
                  "fs.writeFileSync('/workspace/node-output','ok');")
        with patch.dict(os.environ, {"PATH": str(cache) + os.pathsep + os.environ["PATH"]}):
            self.assertEqual(boundary.run_isolated(["node", "-e", script], self.project), 0)
        self.assertEqual((self.project / "node-output").read_text(), "ok")

    def test_root_link_and_external_hardlink_refuse(self):
        alias = self.base / "alias"
        alias.symlink_to(self.project)
        with self.assertRaises(boundary.IsolationError):
            boundary.run_isolated(["/usr/bin/true"], alias)
        os.link(self.base / "other/canary", self.project / "hardlink")
        with self.assertRaises(boundary.IsolationError):
            boundary.run_isolated(["/usr/bin/true"], self.project)

    def test_missing_backend_never_executes_command(self):
        with patch.dict(os.environ, {"AUTONOMOUS_COMPANY_BWRAP": str(self.base / "missing")}):
            with self.assertRaises(boundary.IsolationError):
                boundary.run_isolated(["/usr/bin/touch", "/workspace/escaped"], self.project)
        self.assertFalse((self.project / "escaped").exists())

    def test_exploration_creates_and_collects_independent_product(self):
        root = self.base / "company"
        for name in workspace.TEMPLATES:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        (root / "projects").mkdir()
        (root / "projects/registry.tsv").write_text("name\tpath\tlifecycle\tcreated_at_utc\n")
        cycle = reserve_cycle(root, "", "exploration-probe", 1)["cycleId"]
        view = workspace.CompanyView(root, "", cycle)
        self.addCleanup(shutil.rmtree, view.folder, ignore_errors=True)
        view.prepare()
        readonly = [(view.workspace / name, "/workspace/" + name) for name in ("scripts", "Makefile", ".autonomous-company.local")]
        code = boundary.run_isolated(["/bin/sh", "-c", "awk 'BEGIN {exit 0}' && exec make project-new NAME=new-probe"], view.workspace,
                                     readonly=readonly, environment={"AUTONOMOUS_COMPANY_ROOT": "/workspace", "AUTONOMOUS_COMPANY_CYCLE_ID": cycle})
        self.assertEqual(code, 0)
        view.collect()
        state = read_state(root)
        identity = state["paths"]["projects/new-probe"]
        self.assertEqual(state["continuationProductId"], identity)
        self.assertEqual(state["cycles"][cycle]["createdProductIds"], [identity])
        self.assertTrue((root / "projects/new-probe/.git/HEAD").is_file())
        self.assertTrue((root / "projects/new-probe/README.md").is_file())

    def test_git_status_filter_cannot_read_host_or_change_original(self):
        def git(*arguments):
            return subprocess.run(["git", "-C", str(self.project), *arguments], check=True, capture_output=True)
        git("init", "-q")
        (self.project / "tracked.txt").write_text("original")
        git("add", "tracked.txt")
        git("-c", "user.name=Synthetic probe", "-c", "user.email=probe@example.invalid", "commit", "-qm", "fixture")
        (self.project / "tracked.txt").write_text("modified")
        (self.project / ".gitattributes").write_text("tracked.txt filter=probe\n")
        program = ("import pathlib,sys\ntry:\n data=pathlib.Path(" + repr(str(self.base / "other/canary")) + ").read_text(); "
                   "pathlib.Path('leak.txt').write_text(data); print('LEAK',file=sys.stderr)\n"
                   "except OSError: print('DENIED',file=sys.stderr)\nsys.stdout.write(sys.stdin.read())\n")
        git("config", "filter.probe.clean", "python3 -c " + shlex.quote(program))
        # Confirm this exact configured filter really executes on ordinary host
        # status, using only the synthetic canary, then test the protected entry.
        git("status", "--porcelain")
        self.assertEqual((self.project / "leak.txt").read_text(), "synthetic")
        (self.project / "leak.txt").unlink()
        before = workspace.fingerprint(self.project)
        with (self.base / "status.log").open("wb") as output:
            self.assertEqual(boundary.git_status(self.project, output=output), 0)
        body = (self.base / "status.log").read_text()
        self.assertIn("DENIED", body)
        self.assertNotIn("LEAK", body)
        self.assertIn("tracked.txt", body)
        self.assertEqual(workspace.fingerprint(self.project), before)

    def test_host_python_launcher_uses_isolated_python(self):
        launcher = self.base / "host-python"
        launcher.symlink_to(sys.executable)
        program = "import pathlib,sys; print(sys.executable); assert not pathlib.Path(" + repr(str(self.base / "other/canary")) + ").exists()"
        result = subprocess.run([str(launcher), str(Path(boundary.__file__)), "--workspace", str(self.project),
                                 "--", str(launcher), "-c", program], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "/usr/bin/python3")

    def test_pnpm_isolation_workspaces_require_copy_imports(self):
        for rel in ("scripts/media/pnpm-workspace.yaml", "tests/browser/pnpm-workspace.yaml"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("virtualStoreType: project", text)
            self.assertIn("packageImportMethod: copy", text)
        media_modules = ROOT / "scripts/media/node_modules"
        if sys.platform == "linux" and media_modules.is_dir():
            boundary.checked_tree(media_modules)


if __name__ == "__main__":
    unittest.main()
