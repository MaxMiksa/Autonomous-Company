#!/usr/bin/env python3
"""POSIX execution-domain owner. Communication is files, never the center DB.

The admission protocol prevents accidental competing entry points for managed
roots. It is not a sandbox against another process running as the same user.
"""
from __future__ import annotations

from contextlib import contextmanager

import argparse
import base64
import codecs
import secrets
import shutil
import stat
import ctypes
from functools import lru_cache
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

PROTOCOL = 2
MARKER = ".autonomous-company-center.json"
MAX_JSON = 128 * 1024
HEARTBEAT_TIMEOUT = 15
PAUSE_REQUEST = ".autonomous-company/pause-after-cycle.json"
REVIEW_FILE = ".autonomous-company/recovery-review.json"
CONTROL_FILES = ("scripts/core/auto-loop.sh", "scripts/core/center_runner.py", "scripts/core/stop-loop.sh",
                 "scripts/core/engine-adapters.sh", "scripts/core/engine-metadata.py", "scripts/core/log_redaction.py",
                 "scripts/core/usage.py", "scripts/core/usage_lib.py", "i18n/messages.json",
                 "scripts/core/cycle_reports.py", "scripts/core/live_log.py",
                 "scripts/core/project_isolation.py", "scripts/core/isolation_workspace.py",
                 "scripts/core/isolation_proxy.py", "scripts/core/isolation_entry.py",
                 "scripts/core/isolation_media.py", "scripts/core/isolation-runtime-files.json", "scripts/core/runtime_events.py",
                 "scripts/core/product_media.py", "scripts/core/product_media_worker.cjs",
                 "scripts/core/project-context.py", "scripts/core/product_identity.py",
                 "scripts/core/consensus-format.py", "scripts/core/consensus-guard.sh",
                 "scripts/core/localization.py", "scripts/core/namespace_guard.py", "scripts/core/runtime_artifacts.py",
                 "scripts/core/company_harness.py", "scripts/core/company_harness_bridge.py",
                 "scripts/core/company_harness_client.py", "scripts/core/company_harness_contract.py",
                 "scripts/core/company_harness_handoff.py", "scripts/core/company_harness_inputs.py",
                 "scripts/core/company_harness_loop.sh", "scripts/core/company_harness_quality.py",
                 "scripts/core/company_harness_runner.py", "dashboard/server.py", "Makefile",
                 "scripts/macos/start-daemon.sh", "scripts/macos/install-daemon.sh", "scripts/wsl/dashboard-wsl.sh",
                 "scripts/wsl/install-wsl-daemon.sh", "scripts/windows/start-win.ps1", "scripts/windows/stop-win.ps1")


def read_json(path):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > MAX_JSON:
        raise ValueError("unsafe_control_file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("invalid_control_file")
    return value


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + str(os.getpid()) + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        for attempt in range(51):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if attempt == 50:
                    raise
                time.sleep(0.02)
    finally:
        temporary.unlink(missing_ok=True)


def now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def token(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{8,100}", value):
        raise ValueError("invalid_identity")
    return value


def domain_dir(center_id):
    base = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
    path = base / "autonomous-company/center-runners" / token(center_id)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    return path


def owner_dir(marker):
    folder = domain_dir(marker["centerId"])
    if marker.get("protocolVersion", 1) >= 2:
        folder = folder / "runtimes" / token(marker["runtimeId"])
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    return folder


def lock_file(path, shared=False):
    import fcntl
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, (fcntl.LOCK_SH if shared else fcntl.LOCK_EX) | fcntl.LOCK_NB)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def lock_free(path, shared=False):
    try:
        descriptor = lock_file(path, shared)
    except BlockingIOError:
        return False
    os.close(descriptor)
    return True


def legacy_gate(marker):
    """New independent owners share a gate that excludes a legacy center owner."""
    if marker.get("protocolVersion", 1) < 2:
        return None
    folder = domain_dir(marker["centerId"])
    descriptor = lock_file(folder / "slot.lock", shared=True)
    try:
        if (folder / "owner.json").exists():
            previous = read_json(folder / "owner.json")
            if previous.get("state") != "terminal" or not previous.get("cleanupConfirmed"):
                raise ValueError("legacy_owner_recovery_required")
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


@contextmanager
def execution_lock(marker):
    gate, descriptor = legacy_gate(marker), None
    try:
        descriptor = lock_file(owner_dir(marker) / "slot.lock")
        yield descriptor, gate
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if gate is not None:
            os.close(gate)


def existing_lock_free(path):
    """Observe a project writer lock without creating a source-side inode."""
    import fcntl
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return True
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            return False
    finally:
        os.close(descriptor)


def identity(pid):
    from product_media_process import proc_identity
    value = proc_identity(int(pid))
    if not value or value.get("state") == "Z":
        return None
    return {"pid": value["pid"], "start": value["start"], "boot": boot_id()}


def boot_id():
    path = Path("/proc/sys/kernel/random/boot_id")
    if path.is_file():
        return path.read_text().strip()
    result = subprocess.run(["sysctl", "-n", "kern.boottime"], capture_output=True, text=True, timeout=3, check=True)
    return result.stdout.strip()


def same_process(value):
    return bool(value and identity(value.get("pid", 0)) == value)


def marker_for(root):
    marker = read_json(Path(root) / MARKER)
    if marker.get("protocolVersion") not in {1, PROTOCOL}:
        raise ValueError("incompatible_admission")
    for key in ("centerId", "runtimeId", "entryId", "sourceId"):
        token(marker.get(key))
    return marker


def control_for(manifest):
    value = read_json(Path(manifest["controlDir"]) / "control.json")
    for key in ("centerId", "requestId", "dispatchId", "nonce"):
        if value.get(key) != manifest.get(key):
            raise ValueError("control_identity_mismatch")
    if time.time() - float(value.get("heartbeat", 0)) > HEARTBEAT_TIMEOUT:
        raise ValueError("center_disconnected")
    if value.get("stop"):
        raise ValueError(value.get("reason") or "user_stop")
    return value


def admission(root):
    """Verify inherited OS lock ownership as well as dispatch/runner identity."""
    root = Path(root).resolve()
    if not (root / MARKER).exists() and not (root / MARKER).is_symlink():
        return
    import fcntl
    marker = marker_for(root)
    manifest = read_json(os.environ["AUTONOMOUS_COMPANY_CENTER_MANIFEST"])
    if Path(manifest["root"]).resolve() != root:
        raise ValueError("root_mismatch")
    for key in ("centerId", "runtimeId", "entryId", "sourceId"):
        if manifest.get(key) != marker.get(key):
            raise ValueError("admission_identity_mismatch")
    descriptor = int(os.environ["AUTONOMOUS_COMPANY_CENTER_SLOT_FD"])
    slot = owner_dir(marker) / "slot.lock"
    if (os.fstat(descriptor).st_dev, os.fstat(descriptor).st_ino) != (slot.stat().st_dev, slot.stat().st_ino):
        raise ValueError("admission_descriptor_mismatch")
    # An inherited descriptor references the same locked open-file description.
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if lock_free(slot):
        raise ValueError("admission_without_lock")
    owner = read_json(owner_dir(marker) / "owner.json")
    if any(owner.get(key) != manifest.get(key) for key in ("dispatchId", "requestId", "nonce", "runtimeId")):
        raise ValueError("admission_owner_mismatch")
    if not same_process(owner.get("runner")):
        raise ValueError("runner_disconnected")
    control_for(manifest)


def artifact_admission(root, cleanup=False):
    """Accept only descendants of the current loop/media owner.

    Model CLIs do not necessarily forward inherited FDs into tool shells. The
    process ancestry and pinned start identities prove that normal tool path;
    a caller-supplied cycle flag, manifest path or nonce alone does not.
    """
    root = Path(root).resolve()
    if not (root / MARKER).exists() and not (root / MARKER).is_symlink():
        return
    marker = marker_for(root)
    folder = owner_dir(marker)
    owner = read_json(folder / "owner.json")
    if any(owner.get(key) != marker.get(key) for key in ("centerId", "runtimeId", "entryId", "sourceId")):
        raise ValueError("artifact_owner_mismatch")
    if Path(owner["root"]).resolve() != root or lock_free(folder / "slot.lock"):
        raise ValueError("artifact_owner_unavailable")
    candidates = [owner.get("runner"), owner.get("child")]
    if not cleanup:
        candidates = [value for value in candidates if same_process(value)]
    from product_media_process import proc_identity
    parent, seen = os.getppid(), set()
    while parent > 1 and parent not in seen:
        seen.add(parent)
        observed = identity(parent)
        if observed and observed in candidates:
            return
        row = proc_identity(parent)
        if not row:
            break
        parent = row["ppid"]
    raise ValueError("artifact_outside_managed_owner")


def protective_reason(root):
    for filename, reason in ((".auto-loop-budget-paused", "budget_pause"),
                             (".auto-loop-paused", "governance_pause"),
                             (".auto-loop-stop-pending", "stop_unconfirmed")):
        if (Path(root) / filename).exists():
            return reason
    return None


@lru_cache(maxsize=1)
def consensus_rules():
    spec = importlib.util.spec_from_file_location("center_consensus_format", Path(__file__).with_name("consensus-format.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def governance_reason(root):
    """Read the original P1 grammar without recovering or changing consensus."""
    from product_identity import safe_path
    try:
        root = Path(root)
        consensus = safe_path(root, "memories/consensus.md")
        if not consensus.exists():
            # A fresh exploration is initialized by the original guard. Missing
            # established consensus requires explicit operator recovery.
            prior = ("memories/.consensus-initialized", "memories/consensus.md.bak", ".auto-loop-state",
                     "memories/snapshots", "memories/resets")
            return "context_unavailable" if any(safe_path(root, name).exists() for name in prior) else None
        if consensus.stat().st_size > 2 * 1024 * 1024:
            return "context_unavailable"
        rules = consensus_rules()
        sections = rules.sections(consensus)
        return "unresolved_p1" if rules.unresolved_p1(sections[rules.HEADINGS[1]]) else None
    except (OSError, ValueError, KeyError):
        return "context_unavailable"


def current_loop_state(root, since_ns):
    """Ignore stale or changing state left by a previous loop invocation."""
    try:
        path = Path(root) / ".auto-loop-state"
        before = path.stat()
        if path.is_symlink() or before.st_size > 16384 or before.st_mtime_ns < since_ns:
            return None
        state = dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)
        if path.stat().st_mtime_ns != before.st_mtime_ns:
            return None
        return state
    except (OSError, ValueError):
        pass
    return None


def execution_blocked_reason(root, since_ns, previous=None):
    """Only a guard observation from this live loop establishes a work block."""
    try:
        state = current_loop_state(root, since_ns)
        if state is None:
            return previous
        # An unavailable or incomplete observation is not a confirmed unblock.
        if not state.get("STATUS") or "PAUSE_REASON" not in state:
            return previous
        if state["STATUS"] == "paused" and state["PAUSE_REASON"] == "unresolved_p1":
            governance = governance_reason(root)
            if governance == "context_unavailable":
                return previous
            if governance == "unresolved_p1":
                return "unresolved_p1"
    except (OSError, ValueError):
        return previous
    return None


def compatible(root):
    root, framework = Path(root), Path(__file__).resolve().parents[2]
    try:
        # A partially upgraded context must stay read-only. Match the verified
        # framework's full control boundary, allowing native newline conversion.
        for name in CONTROL_FILES:
            source, reference = root / name, framework / name
            if source.is_symlink() or source.stat().st_size > 2 * 1024 * 1024:
                return False
            if hashlib.sha256(source.read_bytes().replace(b"\r\n", b"\n")).digest() != hashlib.sha256(reference.read_bytes().replace(b"\r\n", b"\n")).digest():
                return False
        return True
    except OSError:
        return False


def execution_context(root, expected_product_id=None, check_git=False):
    """Read the original effective target without recovering or writing state."""
    from localization import read_settings
    from product_identity import read_state, get_identity, project_value, safe_path
    root = Path(root).resolve()
    result = {"valid": False, "reason": "context_unavailable", "project": None, "productId": None}
    try:
        for relative in (".autonomous-company/product-state.transaction.json", ".autonomous-company/product-state.lock", ".autonomous-company.local.language-update"):
            if safe_path(root, relative).exists():
                return result
        if check_git and not existing_lock_free(safe_path(root, ".autonomous-company/project-registry.lock")):
            return result
        _, settings = read_settings(root)
        state = read_state(root)
        selected = settings.get("ACTIVE_PROJECT")
        if selected is not None:
            if not selected.startswith("projects/") or project_value(selected) != selected:
                return result
            project = selected
        else:
            continuation = state.get("continuationProductId")
            item = state["identities"].get(continuation) if continuation else None
            if continuation and (not item or item.get("kind") != "product"):
                return result
            project = item["project"] if item else ""
        if not project:
            if expected_product_id:
                return result
            return {**result, "valid": True, "reason": None}
        product = get_identity(root, project, create=False)
        if not product or product.get("kind") != "product" or expected_product_id and product["id"] != expected_product_id:
            return result
        result.update(project=project, productId=product["id"], reason="product_registration_invalid")
        registry = safe_path(root, "projects/registry.tsv")
        if registry.stat().st_size > 2 * 1024 * 1024:
            return result
        rows = [line.split("\t") for line in registry.read_text(encoding="utf-8").splitlines()[1:]]
        matching = [row for row in rows if row and row[0] == project.split("/")[1]]
        if len(matching) != 1 or len(matching[0]) != 4 or matching[0][1] != project:
            return result
        result["reason"] = "context_unavailable"
        if not safe_path(root, project + "/.git").is_dir():
            return result
        if check_git:
            # The original validator runs in the execution domain. Its validate
            # branch checks independent Git ownership and never takes config locks.
            checked = subprocess.run([sys.executable, "-B", str(root / "scripts/core/project-context.py"), "validate",
                                      "--root", str(root), "--project", project], stdin=subprocess.DEVNULL,
                                     capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
            if checked.returncode:
                return result
        return {**result, "valid": True, "reason": None}
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return result


def preflight(root, center_id=None, allow_protected=False, require_context=True, expected_product_id=None):
    root = Path(root).resolve()
    result = {"compatible": compatible(root), "quiescent": False, "reason": None}
    if not result["compatible"]:
        result["reason"] = "runtime_incompatible"
        return result
    if (root / ".autonomous-company.local.team-active").exists():
        result["reason"] = "interactive_team_active"
        return result
    if (reason := protective_reason(root)) and not allow_protected:
        result["reason"] = reason
        return result
    if require_context:
        context = execution_context(root, expected_product_id, check_git=True)
        if not context["valid"]:
            result["reason"] = context["reason"]
            return result
        if reason := governance_reason(root):
            result["reason"] = reason
            return result
    return _quiescence_preflight(root, center_id, result)


def _quiescence_preflight(root, center_id, result):
    if not existing_lock_free(root / ".auto-loop.pid"):
        result["reason"] = "external_loop_active"
        return result
    # Enabled legacy service bindings must be explicitly retired by the operator.
    if sys.platform == "linux":
        command = ["systemctl", "--user", "show", "autonomous-company.service", "-p", "ExecStart", "-p", "ActiveState", "-p", "UnitFileState"]
    else:
        command = ["launchctl", "print", "gui/%s/com.autonomouscompany.loop" % os.getuid()]
    try:
        service = subprocess.run(command, capture_output=True, text=True, timeout=3)
        if service.returncode:
            diagnostic = service.stderr.lower()
            missing_unit = "could not be found" in diagnostic or "could not find service" in diagnostic
            no_user_manager = (
                sys.platform == "linux"
                and not Path("/run/user/%s/systemd/private" % os.getuid()).exists()
                and re.search(
                    r"failed to connect to (?:user scope )?bus(?: via local transport)?: "
                    r"(?:no medium found|no such file or directory|"
                    r"\$dbus_session_bus_address and \$xdg_runtime_dir not defined)(?:\s|$)",
                    diagnostic,
                ) is not None
            )
            if not missing_unit and not no_user_manager:
                result["reason"] = "service_state_unknown"
                return result
        if str(root) in service.stdout and (sys.platform != "linux" or "ActiveState=active" in service.stdout or "UnitFileState=enabled" in service.stdout):
            result["reason"] = "legacy_service_bound"
            return result
    except FileNotFoundError:
        # A platform without this service manager cannot have its live binding.
        pass
    except (OSError, subprocess.SubprocessError):
        result["reason"] = "service_state_unknown"
        return result
    if center_id:
        marker = marker_for(root) if (root / MARKER).exists() else {"centerId": center_id}
        folder = owner_dir(marker)
        if not lock_free(folder / "slot.lock"):
            result["reason"] = "slot_busy"
            return result
        if (folder / "owner.json").exists():
            owner = read_json(folder / "owner.json")
            if owner.get("state") != "terminal" or not owner.get("cleanupConfirmed"):
                result["reason"] = "owner_recovery_required"
                return result
    result["quiescent"] = True
    return result


def disposal_provenance(root, center_id, expected_framework_revision):
    root = Path(root)
    for ancestor in (root, *root.parents):
        if ancestor.is_symlink():
            raise ValueError("unsafe_disposal_path")
    root = root.resolve()
    token(center_id)
    revision = expected_framework_revision
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("disposal_revision_invalid")
    marker = marker_for(root)
    for name in ("centerId", "runtimeId", "entryId", "sourceId", "operationId"):
        token(marker[name])
    if marker["centerId"] != center_id or marker.get("protocolVersion") != PROTOCOL:
        raise ValueError("disposal_identity_mismatch")
    if root.name != marker["runtimeId"] or root.parent.name != "runtimes":
        raise ValueError("disposal_root_mismatch")
    data = root.parent.parent
    attempt = marker.get("preparationAttempt")
    genesis_path = "staging/" + marker["operationId"]
    if attempt is not None:
        if not isinstance(attempt, str) or not re.fullmatch(r"attempt_[0-9a-f]{32}", attempt):
            raise ValueError("disposal_attempt_invalid")
        genesis_path += "/attempts/" + attempt
    genesis = read_json(control_path(data, genesis_path + "/intent.json"))
    reserved = genesis.get("reserved", {})
    if (genesis.get("centerId") != center_id or genesis.get("operationId") != marker["operationId"]
            or genesis.get("frameworkRevision") != revision or genesis.get("preparationAttempt") != attempt
            or any(reserved.get(key) != marker[key] for key in ("runtimeId", "entryId", "sourceId"))):
        raise ValueError("disposal_genesis_mismatch")
    target = genesis.get("target")
    if isinstance(target, str) and re.match(r"^[A-Za-z]:[\\/]", target):
        target = "/mnt/" + target[0].lower() + "/" + target[3:].replace("\\", "/")
    if not isinstance(target, str) or not Path(target).is_absolute() or Path(target).resolve() != root:
        raise ValueError("disposal_genesis_target_mismatch")
    framework = Path(__file__).resolve().parents[2]
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    def git(directory, *arguments):
        checked = subprocess.run(["git", "--no-replace-objects", "-c", "core.fsmonitor=false", "-C", str(directory), *arguments],
                                 stdin=subprocess.DEVNULL, capture_output=True, env=environment, timeout=10)
        if checked.returncode:
            raise ValueError("disposal_revision_unavailable")
        return checked.stdout
    if git(framework, "rev-parse", "--verify", revision + "^{commit}").strip().decode("ascii") != revision:
        raise ValueError("disposal_revision_unavailable")
    git(framework, "merge-base", "--is-ancestor", revision, "HEAD")
    if not control_path(root, ".git").is_dir() or git(root, "rev-parse", "--verify", "HEAD").strip().decode("ascii") != revision:
        raise ValueError("disposal_head_mismatch")
    import ast
    historical_runner = git(framework, "show", revision + ":scripts/core/center_runner.py").decode("utf-8")
    contract = next((ast.literal_eval(node.value) for node in ast.parse(historical_runner).body
                     if isinstance(node, ast.Assign) and any(isinstance(item, ast.Name) and item.id == "CONTROL_FILES" for item in node.targets)), CONTROL_FILES)
    for name in contract:
        source = control_path(root, name)
        metadata = source.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_size > 2 * 1024 * 1024:
            raise ValueError("disposal_control_changed")
        reference = git(framework, "show", revision + ":" + name)
        if source.read_bytes() != reference:
            raise ValueError("disposal_control_changed")
    return {"disposalCompatible": True, "marker": marker, "frameworkRevision": revision}


def disposal_preflight(root, center_id, expected_framework_revision):
    result = {"compatible": compatible(root), "disposalCompatible": False, "quiescent": False, "reason": None}
    try:
        proof = disposal_provenance(root, center_id, expected_framework_revision)
        root = Path(root).resolve()
        result.update(disposalCompatible=True, frameworkRevision=proof["frameworkRevision"])
        if (root / ".autonomous-company.local.team-active").exists():
            result["reason"] = "interactive_team_active"
            return result
        for relative in (".autonomous-company.local.lock", ".autonomous-company.local.language-update",
                         ".autonomous-company/product-state.lock", ".autonomous-company/product-state.transaction.json"):
            if control_path(root, relative).exists():
                result["reason"] = "configuration_writer_active"
                return result
        if not existing_lock_free(control_path(root, ".autonomous-company/project-registry.lock")):
            result["reason"] = "configuration_writer_active"
            return result
        if operator_previews(root):
            result["reason"] = "preview_owner_unconfirmed"
            return result
        result = _quiescence_preflight(root, center_id, result)
        if result["quiescent"]:
            gate = legacy_gate(proof["marker"])
            os.close(gate)
        return result
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        result.update(quiescent=False, reason=str(exc))
        return result


def probe(center_id, manifest_path=None, runtime_id=None):
    marker = {"centerId": center_id, "runtimeId": runtime_id, "protocolVersion": 2 if runtime_id else 1}
    if manifest_path:
        manifest = read_json(manifest_path)
        if manifest["centerId"] != center_id:
            raise ValueError("probe_identity_mismatch")
        marker = marker_for(manifest["root"])
    folder = owner_dir(marker)
    result = {"slotFree": lock_free(folder / "slot.lock"), "owner": None, "receipt": None, "ownerAlive": False}
    try:
        result["owner"] = read_json(folder / "owner.json")
        result["ownerAlive"] = same_process(result["owner"].get("runner"))
    except (OSError, ValueError, KeyError):
        pass
    if marker.get("protocolVersion", 1) >= 2:
        try:
            gate = legacy_gate(marker)
            os.close(gate)
        except (OSError, ValueError):
            result["slotFree"] = False
            result["legacyConflict"] = True
    if manifest_path:
        manifest = read_json(manifest_path)
        try:
            receipt = read_json(Path(manifest["controlDir"]) / "receipt.json")
            if all(receipt.get(key) == manifest.get(key) for key in ("centerId", "runtimeId", "requestId", "dispatchId", "nonce")):
                result["receipt"] = receipt
        except (OSError, ValueError):
            pass
    return result


def signal_owned(value, sig):
    if not same_process(value):
        return
    if sys.platform == "linux":
        descriptor = os.pidfd_open(value["pid"])
        try:
            if same_process(value):
                signal.pidfd_send_signal(descriptor, sig)
        finally:
            os.close(descriptor)
    elif same_process(value):
        os.kill(value["pid"], sig)


def owned_children():
    from product_media_process import posix_rows
    rows = posix_rows()
    owned, parents = {}, {os.getpid()}
    while True:
        children = {row["pid"] for row in rows if row["ppid"] in parents and row["pid"] not in parents}
        if not children:
            break
        for pid in children:
            value = identity(pid)
            if value:
                owned[pid] = value
        parents.update(children)
    return owned


def run(manifest_path):
    manifest = read_json(manifest_path)
    with execution_lock(marker_for(manifest["root"])) as (descriptor, gate):
        return run_owned(manifest_path, descriptor, gate)


def run_owned(manifest_path, descriptor, gate):
    manifest_path = Path(manifest_path).resolve()
    manifest = read_json(manifest_path)
    root = Path(manifest["root"]).resolve()
    marker = marker_for(root)
    if any(marker.get(key) != manifest.get(key) for key in ("centerId", "runtimeId", "entryId", "sourceId")):
        raise ValueError("managed_identity_mismatch")
    folder = owner_dir(marker)
    receipt_path = Path(manifest["controlDir"]) / "receipt.json"
    # Lock contention produces no terminal receipt: another dispatch may own it.
    os.set_inheritable(descriptor, True)
    if receipt_path.exists():
        raise ValueError("dispatch_already_received")
    if (folder / "owner.json").exists():
        previous = read_json(folder / "owner.json")
        if previous.get("state") != "terminal" or not previous.get("cleanupConfirmed"):
            raise ValueError("previous_owner_requires_recovery")
    runner = identity(os.getpid())
    receipt = {key: manifest[key] for key in ("centerId", "runtimeId", "entryId", "sourceId", "requestId", "dispatchId", "nonce")}
    receipt.update(runner=runner, root=str(root), manifest=str(Path(manifest_path).resolve()), state="accepted", acceptedAt=now(), cleanupConfirmed=False)
    atomic_json(folder / "owner.json", receipt)
    atomic_json(receipt_path, receipt)
    launched, child, child_identity, stopping, owned = False, None, None, None, {}

    def publish(state, **fields):
        if state != "running":
            receipt.update(executionBlockedReason=None, executionBlockedAt=None)
        receipt.update(state=state, observedAt=now(), **fields)
        atomic_json(receipt_path, receipt)
        atomic_json(folder / "owner.json", receipt)

    def stop_signal(_sig, _frame):
        nonlocal stopping
        stopping = stopping or "runner_shutdown"

    def cleanup_children():
        # Use the same bounded TERM grace period even when receipt storage fails.
        # A deadline changes the signal, never the ownership requirement.
        cleanup_deadline = time.monotonic() + 10
        while True:
            owned.update(owned_children())
            if child_identity:
                owned[child_identity["pid"]] = child_identity
            if child:
                child.poll()
            live = [value for value in owned.values() if same_process(value)]
            while True:
                try:
                    reaped, _ = os.waitpid(-1, os.WNOHANG)
                    if not reaped:
                        break
                except ChildProcessError:
                    break
            if not live:
                return
            expired = time.monotonic() >= cleanup_deadline
            for value in live:
                try:
                    signal_owned(value, signal.SIGKILL if expired else signal.SIGTERM)
                except OSError:
                    pass
            if expired:
                try:
                    publish("attention", reason="stop_unconfirmed")
                except OSError:
                    pass
            # Orphans remain descendants of the Linux subreaper. On macOS,
            # retain and validate every observed descendant by start identity.
            time.sleep(0.1)

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, stop_signal)
    if sys.platform == "linux":
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "Cannot establish center child subreaper")
    try:
        control_for(manifest)
        check = preflight(root, expected_product_id=manifest.get("productId"))
        if not check["quiescent"]:
            raise ValueError(check["reason"])
        env = dict(os.environ)
        # Browser input never selects executable paths, shell text or credentials.
        env.update(manifest["environment"])
        env.update(AUTONOMOUS_COMPANY_CENTER_MANIFEST=str(manifest_path), AUTONOMOUS_COMPANY_CENTER_SLOT_FD=str(descriptor))
        control_for(manifest)
        command = ["bash", str(root / "scripts/core/auto-loop.sh")]
        launched_at_ns = time.time_ns()
        with (Path(manifest["controlDir"]) / "runner.log").open("ab") as output:
            child = subprocess.Popen(command, cwd=root, env=env, stdin=subprocess.DEVNULL, stdout=output,
                                     stderr=subprocess.STDOUT, start_new_session=True, pass_fds=tuple(fd for fd in (descriptor, gate) if fd is not None))
        launched, child_identity = True, identity(child.pid)
        publish("running", child=child_identity, startedAt=now())
        stop_started = None
        while child.poll() is None:
            owned.update(owned_children())
            try:
                control_for(manifest)
            except (OSError, ValueError, KeyError) as exc:
                stopping = stopping or str(exc)
            stopping = stopping or protective_reason(root)
            # Runtime capacity pauses are loop facts, unlike a model phase.
            state = current_loop_state(root, launched_at_ns) or {}
            if state.get("STATUS") in ("waiting_limit", "circuit_break"):
                stopping = stopping or "provider_pause"
            if not stopping:
                blocked = execution_blocked_reason(root, launched_at_ns, receipt.get("executionBlockedReason"))
                if blocked != receipt.get("executionBlockedReason"):
                    # P1_BLOCK keeps the original loop alive and retains the slot.
                    # It is a work fact, not an instruction to stop or clear P1.
                    publish("running", executionBlockedReason=blocked, executionBlockedAt=now() if blocked else None)
            if stopping and stop_started is None:
                publish("stopping", reason=stopping)
                atomic_json(Path(manifest["controlDir"]) / "stop-observed.json", {"reason": stopping, "at": now()})
                (root / ".auto-loop-stop").touch()
                signal_owned(child_identity, signal.SIGTERM)
                stop_started = time.monotonic()
            if stop_started is not None and time.monotonic() - stop_started > 25:
                publish("attention", reason="stop_unconfirmed")
                for value in owned.values():
                    try:
                        signal_owned(value, signal.SIGKILL)
                    except (OSError, ValueError):
                        pass
            time.sleep(0.1)
        cleanup_children()
        completed_pause = pause_request(root)
        if completed_pause and completed_pause.get("state") == "requested" and completed_pause.get("dispatchId") == manifest["dispatchId"]:
            with request_lock(root):
                completed_pause = {**completed_pause, "state": "canceled", "canceledAt": now(), "reason": stopping or "run_ended"}
                atomic_json(control_path(root, PAUSE_REQUEST), completed_pause)
        graceful_pause = completed_pause and completed_pause.get("state") == "completed" and completed_pause.get("dispatchId") == manifest["dispatchId"]
        publish("terminal", reason=stopping or ("pause_after_cycle" if graceful_pause else "natural" if child.returncode == 0 else "runtime"),
                exitCode=child.returncode, launched=launched, cleanupConfirmed=True, endedAt=now())
        return 0
    except (OSError, ValueError, KeyError) as exc:
        if not launched:
            publish("terminal", reason=str(exc), launched=False, cleanupConfirmed=True, endedAt=now())
            return 1
        # A failed receipt write must not release ownership while descendants
        # still run. Do not rely on a DB/heartbeat timeout to reclaim this slot.
        try:
            publish("attention", reason="recovery_required")
        except OSError:
            pass
        cleanup_children()
        raise


def operator_previews(root, project=None):
    from runtime_artifacts import artifact_records
    from product_identity import get_identity
    result = []
    for record in artifact_records(Path(root)):
        if (record.get("kind") != "preview" or record.get("state") != "running" or record.get("lifetime") != "operator"
                or project is not None and record.get("project") != project):
            continue
        product = get_identity(Path(root), record.get("project"), create=False)
        if not product or product["id"] != record.get("productId"):
            raise ValueError("preview_identity_unconfirmed")
        result.append(record)
    return result


def stop_operator_previews(root, project=None):
    """Token-addressed graceful stop; never signal an unverified old PID."""
    from runtime_artifacts import preview_request
    for record in operator_previews(root, project):
        process = record.get("processIdentity")
        if not process:
            raise ValueError("preview_owner_unconfirmed")
        alive = same_process(process)
        healthy = preview_request(record)
        if healthy:
            if not preview_request(record, stop=True):
                raise ValueError("preview_stop_unconfirmed")
        elif alive:
            raise ValueError("preview_owner_unconfirmed")
        deadline = time.monotonic() + 5
        while same_process(process) or preview_request(record):
            if time.monotonic() >= deadline:
                raise ValueError("preview_stop_unconfirmed")
            time.sleep(0.05)


def media_command(command, root, project, preserve_preview, descriptor, timeout=150, control_path=None, operation_id=None):
    """Retain the slot through confirmed capture cleanup, including orphans."""
    if sys.platform == "linux":
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "Cannot establish media child subreaper")
    stopping, timed_out = False, False
    def stop(_sig, _frame):
        nonlocal stopping
        stopping = True
    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
    child, owned, retained = None, {}, set()
    try:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=True, pass_fds=(descriptor,))
        child_identity = identity(child.pid)
        deadline = time.monotonic() + timeout
        while child.poll() is None:
            owned.update(owned_children())
            if control_path:
                try:
                    control = read_json(control_path)
                    stopping = stopping or control.get("operationId") != operation_id or bool(control.get("stop")) or time.time() - control.get("heartbeat", 0) > HEARTBEAT_TIMEOUT
                except (OSError, ValueError):
                    stopping = True
            if time.monotonic() >= deadline:
                stopping, timed_out = True, True
            if stopping:
                signal_owned(child_identity, signal.SIGTERM)
                break
            time.sleep(0.05)
        if preserve_preview and not stopping and child.returncode == 0:
            from runtime_artifacts import preview_request
            for preview in operator_previews(root, project):
                owner = preview.get("processIdentity")
                if owner and same_process(owner) and preview_request(preview):
                    retained.add(owner["pid"])
    finally:
        try:
            cleanup_deadline = time.monotonic() + 8
            while child is not None:
                owned.update(owned_children())
                live = [value for pid, value in owned.items() if pid not in retained and same_process(value)]
                child.poll()
                while True:
                    try:
                        pid, status = os.waitpid(-1, os.WNOHANG)
                        if not pid:
                            break
                        if pid == child.pid:
                            child.returncode = os.waitstatus_to_exitcode(status)
                    except ChildProcessError:
                        break
                if not live:
                    break
                for value in live:
                    try:
                        signal_owned(value, signal.SIGTERM if time.monotonic() < cleanup_deadline else signal.SIGKILL)
                    except OSError:
                        pass
                # Timeout changes diagnostics, never releases a still-owned process.
                time.sleep(0.05)
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
    return {"ok": child.returncode == 0 and not stopping, "reason": "media_timeout" if timed_out else "media_interrupted" if stopping else None if child.returncode == 0 else "media_failed"}


def media_status(manifest_path):
    manifest = read_json(manifest_path)
    receipt_path = Path(manifest_path).with_name("receipt.json")
    result = {"slotFree": lock_free(owner_dir(marker_for(manifest["root"])) / "slot.lock"), "receipt": None}
    if receipt_path.exists():
        receipt = read_json(receipt_path)
        if all(receipt.get(key) == manifest.get(key) for key in ("centerId", "runtimeId", "sourceId", "entryId", "operationId")):
            result["receipt"] = receipt
    return result


def media(manifest_path):
    manifest = read_json(manifest_path)
    with execution_lock(marker_for(manifest["root"])) as (descriptor, _gate):
        return media_owned(manifest_path, descriptor)


def media_owned(manifest_path, descriptor):
    manifest = read_json(manifest_path)
    root = Path(manifest["root"])
    marker = marker_for(root)
    if any(marker.get(key) != manifest.get(key) for key in ("centerId", "runtimeId", "entryId", "sourceId")):
        raise ValueError("managed_identity_mismatch")
    owner_path = owner_dir(marker) / "owner.json"
    owner = {**{key: manifest[key] for key in ("centerId", "runtimeId", "entryId", "sourceId")},
             "operationId": manifest.get("operationId"), "root": str(root.resolve()), "runner": identity(os.getpid()),
             "state": "media", "cleanupConfirmed": False}
    published = False
    receipt_path = Path(manifest_path).with_name("receipt.json")
    try:
        if owner_path.exists():
            previous = read_json(owner_path)
            if previous.get("state") != "terminal" or not previous.get("cleanupConfirmed"):
                raise ValueError("previous_owner_requires_recovery")
        context = preflight(root, allow_protected=manifest["action"] == "preview_stop",
                            require_context=manifest["action"] != "preview_stop", expected_product_id=manifest.get("productId"))
        if not context["quiescent"]:
            raise ValueError(context.get("reason") or "context_busy")
        from product_identity import get_identity
        product = get_identity(root, manifest["project"], create=False)
        if not product or product["id"] != manifest["productId"]:
            raise ValueError("product_identity_changed")
        action = manifest["action"]
        command = [sys.executable, str(root / "scripts/core/runtime_artifacts.py"), "--root", str(root), "--project", manifest["project"]]
        if action == "capture":
            command += ["media", "--retry"]
        elif action == "preview_start":
            from product_media import load_profile
            profile = load_profile(root / manifest["project"])
            if profile["type"] != "static":
                raise ValueError("preview_unsupported")
            command += ["preview", "--background", "--directory", profile["webRoot"]]
        elif action == "preview_stop":
            command += ["preview-stop"]
        else:
            raise ValueError("unsupported_media_action")
        atomic_json(owner_path, owner)
        atomic_json(receipt_path, owner)
        published = True
        if action == "preview_stop":
            stop_operator_previews(root, manifest["project"])
            result = {"ok": True, "reason": None}
        else:
            result = media_command(command, root, manifest["project"], action == "preview_start", descriptor,
                                   control_path=Path(manifest_path).with_name("control.json"), operation_id=manifest["operationId"])
        owner.update(state="terminal", cleanupConfirmed=True, endedAt=now(), result=result)
        atomic_json(owner_path, owner)
        atomic_json(receipt_path, owner)
        return result
    except Exception:
        if published:
            owner.update(state="attention", reason="media_cleanup_unconfirmed")
            atomic_json(owner_path, owner)
            atomic_json(receipt_path, owner)
        else:
            # No subprocess was started. Record the failed attempt without
            # overwriting a previous uncertain domain owner.
            result = {"ok": False, "reason": "media_preflight_failed"}
            atomic_json(receipt_path, {**owner, "state": "terminal", "cleanupConfirmed": True, "endedAt": now(), "result": result})
            return result
        raise


def bind(manifest_path):
    manifest = read_json(manifest_path)
    marker = manifest.get("oldMarker") or manifest["marker"]
    with execution_lock(marker):
        previous_path = owner_dir(marker) / "owner.json"
        if previous_path.exists():
            previous = read_json(previous_path)
            if previous.get("state") != "terminal" or not previous.get("cleanupConfirmed"):
                raise ValueError("owner_recovery_required")
        return bind_owned(manifest_path)


def bind_owned(manifest_path):
    """Close the check-to-bind race with normal auto-loop's actual root lock."""
    manifest = read_json(manifest_path)
    root = Path(manifest["root"]).resolve()
    marker = manifest["marker"]
    root_lock = None
    try:
        check = preflight(root, allow_protected=manifest["action"] == "release", require_context=manifest["action"] != "release",
                          expected_product_id=manifest.get("productId"))
        if not check["quiescent"]:
            raise ValueError(check["reason"])
        root_lock = lock_file(root / ".auto-loop.pid")
        target = root / MARKER
        existing = read_json(target) if target.exists() else None
        if existing != manifest.get("oldMarker"):
            raise ValueError("ownership_changed")
        if manifest["action"] == "takeover":
            if any(not record.get("processIdentity") for record in operator_previews(root)):
                # The old CLI is still available before binding, so an old
                # unverified preview can be stopped through its original owner.
                raise ValueError("preview_owner_unconfirmed")
            atomic_json(target, marker)
        elif manifest["action"] == "release":
            if existing:
                stop_operator_previews(root)
                target.unlink()
        else:
            raise ValueError("unsupported_binding")
        return {"ok": True}
    finally:
        if root_lock is not None:
            os.close(root_lock)


def recovery_provenance(root, center_id, expected_framework_revision, genesis_target=None, framework=None):
    """Historical code is data here; it never grants permission to execute it."""
    root = Path(root)
    if not root.is_absolute():
        raise ValueError("unsafe_recovery_path")
    for ancestor in (root, *root.parents):
        if ancestor.is_symlink():
            raise ValueError("unsafe_recovery_path")
    root = root.resolve()
    token(center_id)
    revision = expected_framework_revision
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("recovery_revision_invalid")
    marker = marker_for(root)
    for name in ("centerId", "runtimeId", "entryId", "sourceId", "operationId"):
        token(marker[name])
    if marker["centerId"] != center_id or marker.get("protocolVersion") != PROTOCOL:
        raise ValueError("recovery_identity_mismatch")
    if root.name != marker["runtimeId"] or root.parent.name != "runtimes":
        raise ValueError("recovery_root_mismatch")
    data = root.parent.parent
    attempt = marker.get("preparationAttempt")
    genesis_path = "staging/" + marker["operationId"]
    if attempt is not None:
        if not isinstance(attempt, str) or not re.fullmatch(r"attempt_[0-9a-f]{32}", attempt):
            raise ValueError("recovery_attempt_invalid")
        genesis_path += "/attempts/" + attempt
    genesis = read_json(control_path(data, genesis_path + "/intent.json"))
    reserved = genesis.get("reserved", {})
    if (genesis.get("centerId") != center_id or genesis.get("operationId") != marker["operationId"]
            or genesis.get("frameworkRevision") != revision or genesis.get("preparationAttempt") != attempt
            or any(reserved.get(key) != marker[key] for key in ("runtimeId", "entryId", "sourceId"))):
        raise ValueError("recovery_genesis_mismatch")
    target = genesis.get("target")
    if isinstance(target, str) and re.match(r"^[A-Za-z]:[\\/]", target):
        # The selected WSL domain resolves its own Windows path. Never assume
        # automount locations or accept a caller-supplied mapping without proof.
        mapped = subprocess.run(["wslpath", "-a", "-u", target], stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        if not genesis_target or mapped != genesis_target:
            raise ValueError("recovery_genesis_target_mismatch")
        target = mapped
    if genesis_target is not None and Path(genesis_target).resolve() != root:
        raise ValueError("recovery_genesis_target_mismatch")
    if not isinstance(target, str) or not Path(target).is_absolute() or Path(target).resolve() != root:
        raise ValueError("recovery_genesis_target_mismatch")
    framework = Path(framework) if framework is not None else Path(__file__).resolve().parents[2]
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    def git(directory, *arguments):
        checked = subprocess.run(["git", "--no-replace-objects", "-c", "core.fsmonitor=false", "-C", str(directory), *arguments],
                                 stdin=subprocess.DEVNULL, capture_output=True, env=environment, timeout=10)
        if checked.returncode:
            raise ValueError("recovery_revision_unavailable")
        return checked.stdout
    if git(framework, "rev-parse", "--verify", revision + "^{commit}").strip().decode("ascii") != revision:
        raise ValueError("recovery_revision_unavailable")
    git(framework, "merge-base", "--is-ancestor", revision, "HEAD")
    if not control_path(root, ".git").is_dir() or git(root, "rev-parse", "--verify", "HEAD").strip().decode("ascii") != revision:
        raise ValueError("recovery_head_mismatch")
    import ast
    historical_runner = git(framework, "show", revision + ":scripts/core/center_runner.py").decode("utf-8")
    contract = next((ast.literal_eval(node.value) for node in ast.parse(historical_runner).body
                     if isinstance(node, ast.Assign) and any(isinstance(item, ast.Name) and item.id == "CONTROL_FILES" for item in node.targets)), None)
    if not isinstance(contract, tuple) or not contract or any(not isinstance(name, str) for name in contract):
        raise ValueError("recovery_contract_unavailable")
    for name in contract:
        source = control_path(root, name)
        metadata = source.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_size > 2 * 1024 * 1024:
            raise ValueError("recovery_control_changed")
        reference = git(framework, "show", revision + ":" + name)
        if source.read_bytes() != reference:
            raise ValueError("recovery_control_changed")
    return {"recoveryCompatible": True, "marker": marker, "frameworkRevision": revision}


def control_path(root, relative):
    from product_identity import safe_path
    return safe_path(Path(root).resolve(), relative)


def state_pairs(root, relative):
    path = control_path(root, relative)
    if not path.exists():
        return {}
    if path.stat().st_size > 16384:
        raise ValueError("state_file_oversized")
    return dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)


def dependency_checks(root=None, engine=None, model=None, require_isolation=True, effort=None, product_language=None):
    """Probe operator-installed dependencies without running a provider/model."""
    checks = []
    settings = {}
    if root:
        from localization import read_settings
        _, settings = read_settings(Path(root))
    environment = {**os.environ, **settings}
    if engine is not None:
        environment["ENGINE"] = engine
    if model is not None:
        environment["MODEL"] = model
    if effort is not None:
        environment["CODEX_REASONING_EFFORT"] = effort
    if product_language is not None:
        environment["AUTONOMOUS_COMPANY_LANGUAGE"] = product_language
    def record(name, required, function):
        try:
            value = function()
            checks.append({"name": name, "required": required, "ok": True, **value})
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            checks.append({"name": name, "required": required, "ok": False, "reason": str(exc)})
    def binary(name):
        selected = shutil.which(name)
        if not selected:
            raise ValueError(name + " is required in the execution domain")
        version = subprocess.run([selected, "--version"], capture_output=True, text=True, timeout=5, check=True)
        return {"path": selected, "version": version.stdout.splitlines()[0] if version.stdout else "unknown"}
    if engine is not None:
        def configuration():
            if engine not in {"codex", "claude", "cursor", "openai-compatible"}:
                raise ValueError("unsupported_engine")
            if model is not None and (not isinstance(model, str) or len(model) > 200 or any(ord(char) < 32 for char in model)):
                raise ValueError("invalid_model")
            if product_language is not None and product_language not in {"en", "zh-CN"}:
                raise ValueError("invalid_product_language")
            if engine == "codex" and effort is not None and effort not in {"", "none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"}:
                raise ValueError("invalid_reasoning_effort")
            return {"engine": engine, "model": model, "effort": effort, "productLanguage": product_language}
        record("configuration", True, configuration)
    record("python", True, lambda: {"path": sys.executable, "version": sys.version.split()[0]})
    record("git", True, lambda: binary("git"))
    record("bash", True, lambda: binary("bash"))
    if require_isolation:
        def isolation():
            from project_isolation import runtime_binary
            selected = runtime_binary()
            version = subprocess.run([selected, "--version"], capture_output=True, text=True, timeout=5, check=True).stdout.strip()
            matched = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", version)
            if not matched or tuple(int(value or 0) for value in matched.groups()) < (0, 9, 0):
                raise ValueError("bubblewrap >= 0.9 is required; observed " + (version or "unknown version"))
            return {"path": selected, "version": version}
        record("bubblewrap", True, isolation)
        def seccomp():
            ctypes.CDLL("libseccomp.so.2", use_errno=True)
            return {"version": "libseccomp.so.2"}
        record("seccomp", True, seccomp)
        if engine:
            def provider():
                adapter = Path(__file__).with_name("engine-adapters.sh")
                validated = subprocess.run(["bash", "-c", 'source "$1"; engine_adapter_validate_options',
                    "center-provider", str(adapter)], env=environment,
                    capture_output=True, text=True, timeout=10)
                if validated.returncode:
                    raise ValueError(validated.stderr.strip() or validated.stdout.strip() or "Provider configuration is invalid")
                if engine == "openai-compatible":
                    return {"version": "Python adapter", "model": model}
                # Use the same fixed resolver as auto-loop (including a Linux
                # nvm install); a Windows npm launcher is not a Linux provider.
                adapter = Path(__file__).with_name("engine-adapters.sh")
                resolved = subprocess.run(["bash", "-c", 'source "$1"; engine_adapter_resolve',
                    "center-dependency", str(adapter)], env=environment,
                    capture_output=True, text=True, timeout=10)
                selected = resolved.stdout.strip()
                if resolved.returncode or not selected or "\n" in selected:
                    raise ValueError(engine + " CLI is missing in the execution domain")
                from project_isolation import native_engine
                native = native_engine(selected)
                return {"path": str(native), "model": model, "version": "native Linux executable"}
            record("provider", True, provider)
    failed = next((item for item in checks if item["required"] and not item["ok"]), None)
    return {"ok": not failed, "reason": "dependency_missing" if failed else None,
            "diagnostic": failed["reason"] if failed else None, "checks": checks}


def effective_settings(root, marker=None, observation=None):
    from localization import read_settings
    _, settings = read_settings(root)
    allowed = {"ENGINE", "MODEL", "CODEX_MODEL", "CODEX_EFFORT", "CODEX_REASONING_EFFORT", "LANGUAGE", "AUTONOMOUS_COMPANY_LANGUAGE",
               "ACTIVE_PROJECT", "CLAUDE_MODEL", "CURSOR_MODEL", "OPENAI_COMPATIBLE_MODEL", "COMPANY_HARNESS_ENABLED", "CODEX_SANDBOX_MODE"}
    value = {key: data for key, data in settings.items() if key in allowed}
    owner = (observation or {}).get("owner") or {}
    if marker and owner and owner.get("manifest") and all(owner.get(key) == marker.get(key) for key in ("centerId", "runtimeId", "entryId", "sourceId")):
        manifest = read_json(owner["manifest"])
        if (Path(manifest["root"]).resolve() == Path(root).resolve()
                and all(manifest.get(key) == marker.get(key) for key in ("centerId", "runtimeId", "entryId", "sourceId"))
                and all(manifest.get(key) == owner.get(key) for key in ("requestId", "dispatchId", "nonce"))):
            value.update({key: data for key, data in manifest.get("environment", {}).items() if key in allowed})
    if "CODEX_REASONING_EFFORT" in value:
        value["CODEX_EFFORT"] = value["CODEX_REASONING_EFFORT"]
    return value


def readonly_probe(marker):
    """Observe owner locks without creating directories or control files."""
    base = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
    domain = base / "autonomous-company/center-runners" / token(marker["centerId"])
    folder = domain / "runtimes" / token(marker["runtimeId"]) if marker.get("protocolVersion", 1) >= 2 else domain
    result = {"slotFree": existing_lock_free(folder / "slot.lock"), "owner": None, "receipt": None, "ownerAlive": False}
    try:
        owner = read_json(folder / "owner.json")
        if any(owner.get(key) != marker.get(key) for key in ("centerId", "runtimeId", "entryId", "sourceId")):
            raise ValueError("ownership_changed")
        result.update(owner=owner, ownerAlive=same_process(owner.get("runner")))
    except FileNotFoundError:
        pass
    if marker.get("protocolVersion", 1) >= 2:
        legacy = read_json(domain / "owner.json") if (domain / "owner.json").exists() else None
        if not existing_lock_free(domain / "slot.lock") or legacy and (legacy.get("state") != "terminal" or not legacy.get("cleanupConfirmed")):
            result.update(slotFree=False, legacyConflict=True)
    return result


def harness_run_observation(root):
    from product_identity import read_state
    try:
        pending = read_json(control_path(root, 'logs/usage.jsonl.pending'))
        if pending.get('record_role') != 'harness_attempt':
            return None
        cycle = read_state(root)['cycles'][pending['logical_cycle_id']]
        record = read_json(control_path(root, '.autonomous-company/isolation/' + cycle['identityId'] + '/active-run.json'))
        process = identity(record['pid'])
        if (not process or record.get('cycle') != pending['logical_cycle_id'] or record.get('attemptId') != pending['attempt_id'] or
                str(process['start']) != record.get('processStart')):
            return None
        return {'cycleId': record['cycle'], 'attemptId': record['attemptId'], 'pid': record['pid'], 'processStart': record['processStart']}
    except (OSError, ValueError, KeyError, TypeError):
        return None


def source_query(root, query="status", center_id=None, relative_path=None, offset=0, limit=262144, expected_product_id=None):
    root = Path(root).resolve()
    marker = marker_for(root) if control_path(root, MARKER).exists() else None
    if center_id and (not marker or marker["centerId"] != center_id):
        raise ValueError("ownership_changed")
    if query in {"status", "capabilities", "recovery"}:
        observation = readonly_probe(marker) if marker else None
        pairs = state_pairs(root, ".auto-loop-state")
        running = not existing_lock_free(control_path(root, ".auto-loop.pid"))
        pause_reason = state_pairs(root, ".auto-loop-paused").get("PAUSE_REASON")
        context = execution_context(root, expected_product_id)
        safe_settings = effective_settings(root, marker, observation)
        result = {"ok": True, "timestamp": now(), "compatible": compatible(root), "context": context,
                  "protection": {"reason": protective_reason(root), "pauseReason": pause_reason},
                  "protectiveReason": protective_reason(root), "pauseReason": pause_reason,
                  "governanceReason": governance_reason(root), "marker": marker,
                  "owner": observation.get("owner") if observation else None, "probe": observation,
                  "owned": bool(marker and (not center_id or marker["centerId"] == center_id)),
                  "stateFile": pairs, "loopState": pairs, "settings": safe_settings,
                  "parsed": {"loop": {"state": pairs.get("STATUS", "unknown"),
                                        "processState": "running" if running else "stopped",
                                        "pid": None}}}
        product_lock = control_path(root, ".autonomous-company/product-state.lock")
        result["productLock"] = {"emptyDirectory": product_lock.is_dir() and not any(product_lock.iterdir()),
                                 "directoryOwnerKnown": False}
        pid_path = control_path(root, ".auto-loop.pid")
        if pid_path.exists() and pid_path.stat().st_size > 4096:
            raise ValueError("state_file_oversized")
        result["pid"] = pid_path.read_text().strip() if pid_path.exists() else None
        result["pidMtimeNs"] = pid_path.stat().st_mtime_ns if pid_path.exists() else None
        pending = control_path(root, "logs/usage.jsonl.pending")
        result["usagePendingMtimeNs"] = pending.stat().st_mtime_ns if pending.exists() else None
        result["parsed"]["loop"]["pid"] = int(result["pid"]) if (result["pid"] or "").isdigit() else None
        process = identity(result['parsed']['loop']['pid']) if running and result['parsed']['loop']['pid'] else None
        result.update(processStart=str(process['start']) if process else None, harnessRun=harness_run_observation(root) if running else None)
        if query == "recovery":
            result.update(recoverable=pause_reason == "interrupted_cycle",
                          pendingRecovery=control_path(root, "memories/.consensus-cycle-pending").exists(),
                          reviewScope="Consensus and human configuration only; review product code and external effects manually")
        return result
    if query == "config":
        observation = readonly_probe(marker) if marker else None
        if expected_product_id and not execution_context(root, expected_product_id)["valid"]:
            raise ValueError("product_registration_invalid")
        return {"ok": True, "marker": marker, "settings": effective_settings(root, marker, observation), "timestamp": now()}
    if query not in {"log", "file"}:
        raise ValueError("unsupported_query")
    if not isinstance(relative_path, str) or "\\" in relative_path:
        raise ValueError("invalid_read_path")
    allowed = relative_path in {".auto-loop-state", ".auto-loop.pid", ".auto-loop-paused",
                                ".autonomous-company/product-state.json", "logs/usage.jsonl", "logs/usage.jsonl.pending"}
    log_allowed = re.fullmatch(r"logs/(?:auto-loop\.log|cycle-[A-Za-z0-9_-]+\.(?:log|json))", relative_path)
    harness_attempt = re.fullmatch(r"logs/(attempt-[A-Za-z0-9_-]+)\.(?:log|json)", relative_path)
    if harness_attempt:
        from company_harness import HarnessStore
        from product_identity import read_state
        state = read_state(root)
        cycles = HarnessStore(root).snapshot(compact=True)['cycles']
        cycle = next((cycle for cycle in cycles if any(attempt['attemptId'] == harness_attempt[1] for attempt in cycle['attempts'])), None)
        identity = state['cycles'].get(cycle['cycleId']) if cycle else None
        if not identity or expected_product_id and expected_product_id not in {identity['identityId'], *identity.get('createdProductIds', [])}:
            raise ValueError('attempt_not_recorded')
        log_allowed = True
    if not log_allowed and (query == "log" or not allowed):
        raise ValueError("invalid_read_path")
    path = control_path(root, relative_path)
    if not path.is_file():
        raise ValueError("source_file_missing")
    if query == "log" and relative_path != "logs/auto-loop.log" and not harness_attempt:
        # Require a real durable companion record; caller cannot select an
        # arbitrary file by presenting a path that merely resembles a cycle.
        record = path.with_suffix(".json")
        if not record.is_file() or record.is_symlink():
            cycle_id = path.stem
            pairs = state_pairs(root, ".auto-loop-state")
            context_path = control_path(root, f"logs/{cycle_id}.context.json")
            pending_path = control_path(root, "logs/usage.jsonl.pending")
            active = (pairs.get("STATUS") == "running" and pairs.get("PRODUCT_CYCLE_ID") == cycle_id
                      and not existing_lock_free(control_path(root, ".auto-loop.pid")))
            if not active or not context_path.is_file() or not pending_path.is_file() or \
                    read_json(context_path).get("cycleId") != cycle_id or read_json(pending_path).get("cycle_id") != cycle_id:
                raise ValueError("cycle_not_recorded")
            from product_identity import read_state
            state = read_state(root)
            row = state["cycles"].get(cycle_id)
            owner = state["identities"].get(row["identityId"]) if row else None
            context = read_json(context_path)
            if (not row or not owner or row.get("state") != "dispatching" or not row.get("dispatchAt")
                    or context.get("project") != row.get("project") or row.get("project") != owner.get("project")
                    or expected_product_id and row.get("identityId") != expected_product_id):
                raise ValueError("cycle_not_recorded")
        elif expected_product_id:
            from product_identity import read_state
            row = read_state(root)["cycles"].get(path.stem)
            if not row or expected_product_id not in {row.get("identityId"), *row.get("createdProductIds", [])}:
                raise ValueError("cycle_not_recorded")
    file_stat = path.stat()
    size = file_stat.st_size
    offset, limit = max(0, int(offset)), max(1, min(int(limit), 262144))
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                or (opened.st_dev, opened.st_ino) != (file_stat.st_dev, file_stat.st_ino)):
            raise ValueError("unsafe_read_path")
        stream.seek(min(offset, size))
        payload = stream.read(limit)
        following = min(offset, size) + len(payload)
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        content = decoder.decode(payload, final=following >= size)
        # Finish a split UTF-8 character so sequential byte pages keep Chinese
        # logs intact; at most three extra bytes are read past the page limit.
        while decoder.getstate()[0] and following < size:
            extra = stream.read(1)
            if not extra:
                content += decoder.decode(b"", final=True)
                break
            following += len(extra)
            payload += extra
            content += decoder.decode(extra, final=following >= size)
    return {"ok": True, "marker": marker, "relativePath": relative_path, "content": content,
            "offset": min(offset, size), "nextOffset": following, "totalBytes": size, "size": size,
            "bytesBase64": base64.b64encode(payload).decode("ascii"), "revision": f"{size}:{file_stat.st_mtime_ns}",
            "eof": following >= size, "timestamp": now()}


def checked_control_manifest(manifest_path):
    manifest = read_json(manifest_path)
    root = Path(manifest["root"]).resolve()
    marker = marker_for(root)
    if any(manifest.get(key) != marker.get(key) for key in ("centerId", "runtimeId", "entryId", "sourceId")):
        raise ValueError("ownership_changed")
    if not compatible(root):
        raise ValueError("runtime_incompatible")
    return manifest, root, marker


def recovery_fingerprint(root):
    """Pin the reviewed governance and product bytes; external effects remain human evidence."""
    value = hashlib.sha256()
    paths = [control_path(root, name) for name in (MARKER, ".autonomous-company.local", ".auto-loop-paused",
             "memories/consensus.md", ".autonomous-company/product-state.json", "logs/usage.jsonl", ".auto-loop-budget-paused") ]
    products = control_path(root, "projects")
    if products.exists():
        for folder, directories, files in os.walk(products, followlinks=False):
            directories[:] = sorted(name for name in directories if name not in {".git", "node_modules", ".venv"})
            if any((Path(folder) / name).is_symlink() for name in directories):
                raise ValueError("unsafe_review_path")
            paths.extend(Path(folder) / name for name in sorted(files))
    for path in paths:
        relative = path.relative_to(root).as_posix()
        control_path(root, relative)
        if path.is_symlink():
            raise ValueError("unsafe_review_path")
        value.update(relative.encode())
        if path.exists():
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(262144), b""):
                    value.update(chunk)
        else:
            value.update(b"missing")
    return value.hexdigest()


def pause_request(root):
    path = control_path(root, PAUSE_REQUEST)
    return read_json(path) if path.exists() else None


@contextmanager
def request_lock(root):
    path = control_path(root, ".autonomous-company/pause-after-cycle.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + 5
    while True:
        try:
            descriptor = lock_file(path)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                raise ValueError("pause_request_busy")
            time.sleep(0.025)
    try:
        yield
    finally:
        os.close(descriptor)


def boundary_pause(root):
    root = Path(root).resolve()
    admission(root)
    with request_lock(root):
        requested = pause_request(root)
        if not requested or requested.get("state") != "requested":
            return False
        marker = marker_for(root)
        if any(requested.get(key) != marker.get(key) for key in ("centerId", "runtimeId", "entryId", "sourceId")):
            raise ValueError("pause_request_identity_mismatch")
        manifest = read_json(os.environ["AUTONOMOUS_COMPANY_CENTER_MANIFEST"])
        if requested.get("dispatchId") != manifest.get("dispatchId"):
            raise ValueError("pause_request_dispatch_mismatch")
        from product_identity import read_state, OPEN
        if (control_path(root, "memories/.consensus-cycle-pending").exists()
                or control_path(root, "logs/usage.jsonl.pending").exists()
                or any(row["state"] in OPEN for row in read_state(root)["cycles"].values())):
            raise ValueError("cycle_boundary_unsealed")
        harness_db = control_path(root, ".autonomous-company/company-harness.sqlite3")
        if harness_db.exists():
            from company_harness import HarnessStore
            if any(row.get("protocolState") != "closed" for row in HarnessStore(root).snapshot()["cycles"]):
                raise ValueError("cycle_boundary_unsealed")
        atomic_json(control_path(root, PAUSE_REQUEST), {**requested, "state": "completed", "completedAt": now()})
        return True


def source_control(manifest_path):
    manifest, root, marker = checked_control_manifest(manifest_path)
    action = manifest["action"]
    if action in {"pause_after_cycle", "cancel_pause_after_cycle"}:
        observation = probe(marker["centerId"], runtime_id=marker["runtimeId"] if marker.get("protocolVersion", 1) >= 2 else None)
        owner = observation.get("owner") or {}
        if (observation["slotFree"] or not observation["ownerAlive"] or owner.get("state") != "running"
                or any(owner.get(key) != marker.get(key) for key in ("centerId", "runtimeId", "entryId", "sourceId"))
                or owner.get("dispatchId") != manifest.get("expectedDispatchId")):
            raise ValueError("active_owner_required")
        with request_lock(root):
            previous = pause_request(root)
            if action == "cancel_pause_after_cycle":
                if not previous or previous.get("state") != "requested":
                    raise ValueError("pause_request_already_completed")
                if previous.get("dispatchId") != owner["dispatchId"]:
                    raise ValueError("pause_request_dispatch_mismatch")
                result = {**previous, "state": "canceled", "canceledAt": now()}
            else:
                result = {"state": "requested", "requestedAt": now(), "dispatchId": owner["dispatchId"],
                          **{key: marker[key] for key in ("centerId", "runtimeId", "entryId", "sourceId")}}
            atomic_json(control_path(root, PAUSE_REQUEST), result)
        return {"ok": True, "pauseAfterCycle": result}
    if action not in {"review_recovery", "confirm_recovery"}:
        raise ValueError("unsupported_control")
    with execution_lock(marker):
        previous_path = owner_dir(marker) / "owner.json"
        if previous_path.exists():
            previous = read_json(previous_path)
            if (previous.get("state") != "terminal" or not previous.get("cleanupConfirmed")
                    or any(previous.get(key) != marker.get(key) for key in ("centerId", "runtimeId", "entryId", "sourceId"))
                    or same_process(previous.get("runner")) or same_process(previous.get("child"))
                    or any(same_process(item) for item in previous.get("ownedProcesses", []))):
                raise ValueError("owner_recovery_required")
        check = preflight(root, allow_protected=True, require_context=False)
        if not check["quiescent"]:
            raise ValueError(check["reason"])
        descriptor = lock_file(control_path(root, ".auto-loop.pid"))
        try:
            # No config, interactive team, model, loop, media, or old runtime
            # writer may remain while recovering or confirming human review.
            if operator_previews(root):
                raise ValueError("preview_owner_unconfirmed")
            if control_path(root, ".auto-loop-stop-pending").exists():
                raise ValueError("stop_unconfirmed")
            for name in (".autonomous-company.local.lock", ".autonomous-company.local.team-active",
                         ".autonomous-company.local.language-update", ".autonomous-company/product-state.lock"):
                if control_path(root, name).exists():
                    raise ValueError("configuration_writer_active")
            if not existing_lock_free(control_path(root, ".autonomous-company/project-registry.lock")):
                raise ValueError("configuration_writer_active")
            environment = {**os.environ, "AUTONOMOUS_COMPANY_ROOT": str(root)}
            budget = subprocess.run([sys.executable, str(root / "scripts/core/usage.py"), "check",
                "--ledger", str(root / "logs/usage.jsonl"), "--pause-file", str(root / ".auto-loop-budget-paused")],
                cwd=root, env=environment, capture_output=True, text=True, timeout=15)
            if budget.returncode or control_path(root, ".auto-loop-budget-paused").exists():
                raise ValueError("budget_pause")
            if action == "review_recovery":
                if control_path(root, ".autonomous-company/harness.sqlite3").exists():
                    subprocess.run([sys.executable, str(root / "scripts/core/company_harness_runner.py"),
                        "--root", str(root), "reconcile-crash", "--reason", "center_review_recovery"],
                        cwd=root, env=environment, capture_output=True, text=True, timeout=30, check=True)
                command = subprocess.run(["bash", str(root / "scripts/core/consensus-guard.sh"), "recover"],
                    cwd=root, env=environment, capture_output=True, text=True, timeout=15)
                if command.returncode not in {0, 42} or control_path(root, "memories/.consensus-cycle-pending").exists():
                    raise ValueError("interrupted_recovery_failed")
                for arguments in (("usage.py", "recover", "--ledger", str(root / "logs/usage.jsonl"),
                                   "--pause-file", str(root / ".auto-loop-budget-paused")),
                                  ("product_identity.py", "--root", str(root), "recover")):
                    subprocess.run([sys.executable, str(root / "scripts/core" / arguments[0]), *arguments[1:]],
                        cwd=root, capture_output=True, text=True, timeout=15, check=True)
                reason = state_pairs(root, ".auto-loop-paused").get("PAUSE_REASON")
                if reason != "interrupted_cycle":
                    raise ValueError(reason or "no_interrupted_pause")
                original = subprocess.run(["bash", str(root / "scripts/core/consensus-guard.sh"), "preflight", "0"],
                    cwd=root, env=environment, capture_output=True, text=True, timeout=15)
                if original.returncode:
                    raise ValueError("unresolved_p1" if original.returncode == 41 else "governance_invalid")
                if protective_reason(root) == "budget_pause":
                    raise ValueError("budget_pause")
                context = execution_context(root, manifest.get("productId"), check_git=True)
                if not context["valid"]:
                    raise ValueError(context["reason"])
                review = {"reviewToken": secrets.token_hex(24), "createdAt": now(), "expiresAt": time.time() + 900,
                          "fingerprint": recovery_fingerprint(root), "pauseReason": reason,
                          **{key: marker[key] for key in ("centerId", "runtimeId", "entryId", "sourceId")}}
                atomic_json(control_path(root, REVIEW_FILE), review)
                return {"ok": True, "reviewToken": review["reviewToken"], "pauseReason": reason,
                        "writersStopped": True, "recoveryComplete": True, "context": context,
                        "requiresConfirmation": ["productCodeReviewed", "externalEffectsReviewed"],
                        "reviewScope": "Restored consensus and human configuration; product code and external effects are not rolled back"}
            review = read_json(control_path(root, REVIEW_FILE))
            if manifest.get("reviewToken") != review["reviewToken"] or time.time() > review["expiresAt"] or \
                    any(review.get(key) != marker.get(key) for key in ("centerId", "runtimeId", "entryId", "sourceId")):
                raise ValueError("recovery_review_expired")
            if not all(manifest.get(key) is True for key in ("productCodeReviewed", "externalEffectsReviewed")):
                raise ValueError("human_review_required")
            if review["fingerprint"] != recovery_fingerprint(root):
                raise ValueError("recovery_review_changed")
            if state_pairs(root, ".auto-loop-paused").get("PAUSE_REASON") != "interrupted_cycle":
                raise ValueError("governance_pause_changed")
            if governance_reason(root) or control_path(root, "memories/.consensus-cycle-pending").exists():
                raise ValueError(governance_reason(root) or "interrupted_recovery_pending")
            if control_path(root, ".auto-loop-budget-paused").exists() or control_path(root, ".auto-loop-stop-pending").exists():
                raise ValueError(protective_reason(root))
            context = execution_context(root, manifest.get("productId"), check_git=True)
            if not context["valid"]:
                raise ValueError(context["reason"])
            if control_path(root, ".autonomous-company/harness.sqlite3").exists():
                subprocess.run([sys.executable, str(root / "scripts/core/company_harness_runner.py"),
                    "--root", str(root), "approve-recovery", "--review-token", review["reviewToken"],
                    "--reason", "center_human_confirmed"],
                    cwd=root, env=environment, capture_output=True, text=True, timeout=30, check=True)
            confirmation = {**review, "confirmedAt": now(), "productCodeReviewed": True, "externalEffectsReviewed": True}
            atomic_json(control_path(root, REVIEW_FILE), confirmation)
            control_path(root, ".auto-loop-paused").unlink()
            return {"ok": True, "confirmedAt": confirmation["confirmedAt"], "resumed": False}
        finally:
            os.close(descriptor)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("run", "probe", "admit", "preflight", "disposal-preflight", "media", "media-status", "bind", "dependencies", "query", "control", "boundary-pause", "stream-log", "stream-log-complete"))
    parser.add_argument("--query", default="status")
    parser.add_argument("--relative-path", "--path", dest="relative_path")
    parser.add_argument("--input-path")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=262144)
    parser.add_argument("--engine")
    parser.add_argument("--model")
    parser.add_argument("--effort")
    parser.add_argument("--product-language")
    parser.add_argument("--require-isolation", choices=("0", "1"), default="1")
    parser.add_argument("--manifest")
    parser.add_argument("--root")
    parser.add_argument("--center-id")
    parser.add_argument("--runtime-id")
    parser.add_argument("--allow-protected", choices=("0", "1"), default="0")
    parser.add_argument("--require-context", choices=("0", "1"), default="1")
    parser.add_argument("--expected-product-id")
    parser.add_argument("--expected-framework-revision")
    args = parser.parse_args()
    try:
        if args.action == "run":
            return run(args.manifest)
        if args.action == "admit":
            admission(args.root)
            return 0
        if args.action == "stream-log-complete":
            from live_log import stream_log_complete
            stream_log_complete(args.input_path)
            return 0
        if args.action == "stream-log":
            from live_log import stream_log
            stream_log(args.root, args.input_path, args.relative_path, admission=admission, control_path=control_path)
            return 0
        if args.action == "boundary-pause":
            return 0 if boundary_pause(args.root) else 1
        if args.action == "dependencies":
            result = dependency_checks(args.root, args.engine, args.model, args.require_isolation == "1", args.effort, args.product_language)
        elif args.action == "query":
            result = source_query(args.root, args.query, args.center_id, args.relative_path, args.offset, args.limit, args.expected_product_id)
        elif args.action == "control":
            result = source_control(args.manifest)
        elif args.action == "disposal-preflight":
            result = disposal_preflight(args.root, args.center_id, args.expected_framework_revision)
        elif args.action == "preflight":
            result = preflight(args.root, args.center_id, args.allow_protected == "1", args.require_context == "1", args.expected_product_id)
        elif args.action == "media":
            result = media(args.manifest)
        elif args.action == "media-status":
            result = media_status(args.manifest)
        elif args.action == "bind":
            result = bind(args.manifest)
        else:
            result = probe(args.center_id, args.manifest, args.runtime_id)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print("Center admission/runtime refused: " + str(exc), file=sys.stderr)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
