"""Persistent operator intent and FIFO scheduling, separate from source facts.

Only this process writes center storage. The POSIX adapter owns OS process/lock
evidence and exchanges bounded JSON receipts; neither layer guesses success.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid

from center_store import CenterError
import center_profiles as profiles
import center_environment

STATES = frozenset(("queued", "starting", "running", "stopping", "attention", "ended", "failed", "canceled"))
OPEN = frozenset(("queued", "starting", "running", "stopping", "attention"))
ACTIVE = frozenset(("starting", "running", "stopping", "attention"))
TERMINAL = STATES - OPEN
EDGES = {"queued": {"canceled", "attention", "starting"},
         "starting": {"running", "stopping", "attention", "failed", "ended"},
         "running": {"stopping", "attention", "ended", "failed"},
         "stopping": {"attention", "ended", "failed"},
         "attention": {"running", "stopping", "ended", "failed", "canceled"}}
MARKER = ".autonomous-company-center.json"
ENGINES = {"claude", "codex", "cursor", "openai-compatible"}
EFFORTS = profiles.EFFORTS
RUNTIME_ENV_NAMES = {"CODEX_BIN", "CODEX_SANDBOX_MODE", "CLAUDE_BIN", "CLAUDE_PERMISSION_MODE", "CURSOR_BIN",
                     "CURSOR_ADAPTER_ENABLED", "CURSOR_SANDBOX_MODE", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                     "OPENAI_BASE_URL", "ANTHROPIC_BASE_URL", "OPENAI_COMPATIBLE_ADAPTER_ENABLED", "OPENAI_COMPATIBLE_ENDPOINT",
                     "OPENAI_COMPATIBLE_API_KEY", "OPENAI_COMPATIBLE_ALLOW_INSECURE_HTTP", "OPENAI_COMPATIBLE_MODEL",
                     "LOOP_INTERVAL", "CYCLE_TIMEOUT_SECONDS", "CYCLE_TERM_GRACE_SECONDS", "CYCLE_KILL_WAIT_SECONDS",
                     "USAGE_BUDGET_PERIOD", "USAGE_WARNING_USD", "USAGE_HARD_LIMIT_USD", "USAGE_WARNING_TOKENS", "USAGE_HARD_LIMIT_TOKENS",
                     "AUTONOMOUS_COMPANY_BWRAP", "AUTONOMOUS_COMPANY_BROWSER_RUNTIME", "AUTONOMOUS_COMPANY_LIBRARY_RUNTIME",
                     "COMPANY_HARNESS_ENABLED", "COMPANY_HARNESS_CORRECTIONS", "COMPANY_HARNESS_RECOVERY_ATTEMPTS",
                     "COMPANY_HARNESS_RECOVERY_SECONDS", "COMPANY_HARNESS_CLOSE_SECONDS", "COMPANY_HARNESS_MAX_SAME_ERROR"}


def now():
    return datetime.now(timezone.utc).isoformat()


def harness_capability(root, engine):
    if engine != 'codex':
        return {'supported': False, 'enabled': False, 'reason': 'unsupported_adapter'}
    if os.environ.get('CODEX_SANDBOX_MODE', 'danger-full-access') != 'danger-full-access':
        return {'supported': False, 'enabled': False, 'reason': 'unsupported_inner_sandbox'}
    supported = all((Path(root) / 'scripts/core' / name).is_file() for name in (
        'company_harness.py', 'company_harness_bridge.py', 'company_harness_client.py',
        'company_harness_contract.py', 'company_harness_handoff.py', 'company_harness_inputs.py',
        'company_harness_loop.sh', 'company_harness_quality.py', 'company_harness_runner.py'))
    return {'supported': supported, 'enabled': supported, 'reason': None if supported else 'unsupported_framework'}


def recently_confirmed(request):
    try:
        return 0 <= (datetime.now(timezone.utc) - datetime.fromisoformat(request["liveConfirmedAt"])).total_seconds() <= 15
    except (KeyError, TypeError, ValueError):
        return False


def uid(prefix):
    return prefix + "_" + uuid.uuid4().hex


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
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
                # Windows/WSL readers can briefly hold a non-delete-shared
                # handle. Preserve the previous durable control during retry.
                if attempt == 50:
                    raise
                time.sleep(0.02)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > 128 * 1024:
        raise ValueError("Unsafe control file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Invalid control file")
    return value


def config_fingerprint(root):
    result = {}
    for name in (".autonomous-company.local", "PROMPT.md", ".auto-loop.env", "scripts/core/auto-loop.sh",
                 "scripts/core/center_runner.py", "scripts/core/engine-adapters.sh", "scripts/core/loop-lock.py"):
        path = Path(root) / name
        if path.exists():
            if path.is_symlink() or path.stat().st_size > 1024 * 1024:
                raise CenterError("CONTEXT_UNAVAILABLE", "Configuration is unsafe or oversized", 409)
            result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            result[name] = None
    return digest(result)


class PosixAdapter:
    """Fixed argv bridge; all WSL processes use the saved distro and user."""
    def __init__(self, framework_root, domain):
        self.framework_root = Path(framework_root)
        self.domain = domain
        self.paths = {}

    @property
    def available(self):
        return bool(self.domain and self.domain.get("platform") in {"posix", "wsl"})

    def _wsl(self):
        return ["wsl.exe", "--distribution", self.domain["distribution"], "--user", self.domain["user"]]

    def path(self, path):
        path = str(Path(path).resolve())
        if self.domain.get("platform") != "wsl":
            return path
        if path not in self.paths:
            value = self._execute(self._wsl() + ["--exec", "wslpath", "-a", path], timeout=15).stdout.strip()
            if not value.startswith("/") or "\n" in value or "\r" in value:
                raise CenterError("CONTEXT_UNAVAILABLE", "WSL path conversion failed", 503)
            self.paths[path] = value
        return self.paths[path]

    def _execute(self, command, timeout=15):
        # These commands are noninteractive; sharing the server's pending stdin
        # pipe read can hang Windows Git before it emits any output.
        return subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                              env=self.environment(),
                              **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}), check=True)

    def environment(self):
        environment = dict(os.environ)
        if self.domain and self.domain.get("platform") == "wsl":
            # Controlled process environment references never enter manifests,
            # SQLite, log messages, or HTTP configuration snapshots.
            forwarded = sorted(name for name in RUNTIME_ENV_NAMES if name in environment)
            environment["WSLENV"] = ":".join(filter(None, [environment.get("WSLENV", ""), *forwarded]))
        return environment

    def command(self, action, **kwargs):
        if not self.available:
            raise CenterError("EXECUTION_DOMAIN_UNCONFIGURED", "Select an explicit execution domain first", 409)
        if action == "product-lock-recovery":
            command = ["python3", self.path(self.framework_root / "dashboard/center_recovery.py")]
        else:
            command = ["python3", self.path(self.framework_root / "scripts/core/center_runner.py"), action]
        for name, value in kwargs.items():
            if value is not None:
                command += ["--" + name.replace("_", "-"), self.path(value) if name in {"root", "manifest"} else str(value)]
        return self._wsl() + ["--exec", *command] if self.domain["platform"] == "wsl" else command

    def query(self, action, **kwargs):
        if action == "product-lock-recovery" and self.domain.get("platform") == "wsl" and os.name == "nt":
            # A Windows-created worktree's Git administrative paths are not
            # readable by Linux Git. Export committed objects with native Git,
            # retaining the shared registration and the operation's evidence.
            manifest_path = Path(kwargs["manifest"])
            manifest = read_json(manifest_path)
            bundle = manifest_path.parent / "recovery-framework.bundle"
            self._execute(["git", "-C", str(self.framework_root), "bundle", "create", str(bundle), "HEAD"], timeout=180)
            heads = self._execute(["git", "bundle", "list-heads", str(bundle)], timeout=15).stdout.splitlines()
            if heads != [manifest["frameworkHead"] + " HEAD"]:
                raise CenterError("FRAMEWORK_UNVERIFIED", "Framework changed during recovery preparation", 409)
            manifest["frameworkBundle"] = self.path(bundle)
            manifest["frameworkBundleSha256"] = hashlib.sha256(bundle.read_bytes()).hexdigest()
            atomic_json(manifest_path, manifest)
        timeout = {"product-lock-recovery": 120, "control": 110, "dependencies": 60}.get(action, 15)
        return json.loads(self._execute(self.command(action, **kwargs), timeout=timeout).stdout)

    def launch(self, manifest):
        path = Path(manifest)
        output = (path.parent / "bridge.log").open("ab")
        try:
            return subprocess.Popen(self.command("run", manifest=manifest), stdin=subprocess.DEVNULL, stdout=output,
                                    env=self.environment(),
                                    stderr=subprocess.STDOUT, **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}))
        finally:
            output.close()

    def media(self, manifest):
        return json.loads(self._execute(self.command("media", manifest=manifest), timeout=165).stdout)

    def clone(self, source, prepared, revision, staging):
        if self.domain.get("platform") == "wsl":
            # Windows worktree administrative paths are not valid in WSL. A
            # bundle preserves the full Git baseline without sharing metadata.
            bundle = Path(staging) / "framework.bundle"
            self._execute(["git", "-C", str(source), "bundle", "create", str(bundle), "HEAD"], timeout=180)
            self._execute(self._wsl() + ["--exec", "git", "clone", "--no-checkout", self.path(bundle), self.path(prepared)], timeout=180)
            self._execute(self._wsl() + ["--exec", "git", "-C", self.path(prepared), "checkout", "--detach", revision], timeout=90)
        else:
            self._execute(["git", "clone", "--no-hardlinks", "--no-checkout", "--local", str(source), str(prepared)], timeout=180)
            self._execute(["git", "-C", str(prepared), "checkout", "--detach", revision], timeout=90)


class CenterRuntime:
    def __init__(self, store, catalog, framework_root, execution_domain=None, *, adapter=None):
        self.store, self.catalog, self.framework_root = store, catalog, Path(framework_root).resolve()
        self.data_dir = Path(store.data_dir)
        self._mutex = threading.RLock()
        self._controls_mutex = threading.Lock()
        self._prepare_mutex = threading.Lock()
        self._session_id = uid("session")
        self._closing = threading.Event()
        self._thread = None
        self._heartbeat_thread = None
        self._workers = set()
        self._children = {}
        self._last_refresh = {}
        if execution_domain is None and os.name != "nt":
            execution_domain = {"platform": "posix"}
        self._validate_domain(execution_domain)
        with store.transaction() as tx:
            domain = tx.get("controls", "execution_domain")
            if domain and execution_domain and domain["domain"] != execution_domain:
                raise CenterError("EXECUTION_DOMAIN_CONFLICT", "This center already owns another execution domain", 409)
            if not domain and execution_domain:
                domain = {"domain": execution_domain}
                tx.put("controls", "execution_domain", domain)
            self.domain = domain["domain"] if domain else None
            queue = tx.get("controls", "queue") or {"revision": 0}
            queue.setdefault("maxConcurrentProjects", 4)
            queue.update(dispatchEnabled=False, revision=queue["revision"] + 1, reason="center_restarted")
            tx.put("controls", "queue", queue)
            if not tx.get("preferences", "main"):
                sys.path.insert(0, str(self.framework_root / "scripts/core"))
                from localization import system_language
                language = system_language(os.environ)
                installed = profiles.installation_defaults(self.framework_root, language)
                tx.put("preferences", "main", {"language": language, **installed, "installationConfig": installed,
                                               "defaultTemplateId": None, "revision": 1})
            else:
                preferences = tx.get("preferences", "main")
                if "installationConfig" not in preferences:
                    preferences["installationConfig"] = {key: preferences[key] for key in profiles.FIELDS}
                    preferences["lastConfig"] = dict(preferences["installationConfig"])
                    preferences["defaultTemplateId"] = None
                    tx.put("preferences", "main", preferences)
            # A single-item authorization also expires at a center restart.
            self._revoke_start_authorizations(tx)
            for operation in tx.list("operations"):
                if operation.get("state") in {"preparing", "running"}:
                    operation.update(state="attention", reason="recovery_required")
                    tx.put("operations", operation["operationId"], operation)
        self.adapter = adapter or PosixAdapter(self.framework_root, self.domain)

    @staticmethod
    def _validate_domain(domain):
        if domain is None:
            return
        if not isinstance(domain, dict) or domain.get("platform") not in {"posix", "wsl"}:
            raise CenterError("INVALID_DOMAIN", "Invalid execution domain")
        if domain["platform"] == "wsl":
            for key in ("distribution", "user"):
                if not isinstance(domain.get(key), str) or not re.fullmatch(r"[A-Za-z0-9_. -]{1,80}", domain[key]) or domain[key].startswith("-"):
                    raise CenterError("INVALID_DOMAIN", "WSL requires an explicit distribution and user")

    def _environment_record(self, tx):
        saved = tx.get("controls", "execution_domain") or {}
        return {"domain": self.domain, "revision": saved.get("revision", 1 if self.domain else 0),
                "checks": saved.get("checks", [])}

    def _expected_environment(self, tx, body):
        expected = self._revision_value(body, "environmentRevision")
        if expected is not None and expected != self._environment_record(tx)["revision"]:
            raise CenterError("REVISION_CONFLICT", "Execution environment changed", 409)

    def environment(self):
        with self._mutex, self.store.transaction() as tx:
            result = self._environment_record(tx)
        return {**result, "candidates": center_environment.candidates()}

    def environment_action(self, action, body):
        if action not in {"check", "connect"}:
            raise CenterError("INVALID_ACTION", "Unknown environment action")
        domain = body.get("domain")
        self._validate_domain(domain)
        if domain is None or (os.name == "nt" and domain["platform"] != "wsl"):
            raise CenterError("INVALID_DOMAIN", "Select an explicit execution environment")
        # Serialize connection with creation and preparation. An environment
        # check never migrates existing runtime identities or grants dispatch.
        with self._mutex, self._prepare_mutex:
            with self.store.transaction() as tx:
                if action == "connect":
                    key, body_hash, previous = self._idempotent(tx, "environment/connect", body)
                    if previous:
                        return previous
                saved = self._environment_record(tx)
                if self._revision_value(body, "expectedRevision") is None:
                    raise CenterError("INVALID_REQUEST", "Environment revision is required")
                self._expected(body, saved)
                if action == "connect" and (any(row["state"] in OPEN for row in tx.list("requests"))
                        or any(row.get("state") in {"preparing", "running"} for row in tx.list("operations"))
                        or domain != self.domain and tx.list("runtimes")):
                    raise CenterError("EXECUTION_DOMAIN_CONFLICT", "Resolve existing work before connecting an environment", 409)
            adapter = PosixAdapter(self.framework_root, domain)
            checks = center_environment.check(adapter)
            result = {"domain": domain, "checks": checks, "ready": all(item["ok"] for item in checks),
                      "revision": saved["revision"]}
            if action == "check":
                return result
            if not result["ready"]:
                raise CenterError("ENVIRONMENT_UNAVAILABLE", "Selected environment checks failed", 409, {"checks": checks})
            with self.store.transaction() as tx:
                self._pause(tx, "environment_connected")
                result["revision"] += 1
                tx.put("controls", "execution_domain", {"domain": domain, "revision": result["revision"], "checks": checks})
                self._remember(tx, key, body_hash, result)
            self.domain, self.adapter = domain, adapter
            return result

    def preflight(self, body=None):
        body = body or {}
        groups = body.get("groups", [body])
        if not isinstance(groups, list) or not groups or len(groups) > 100 or any(not isinstance(group, dict) for group in groups):
            raise CenterError("INVALID_BATCH", "Provide valid configuration groups")
        with self._mutex:
            with self.store.transaction() as tx:
                environment = self._environment_record(tx)
                expected = self._revision_value(body, "environmentRevision")
                if expected is not None and expected != environment["revision"]:
                    raise CenterError("REVISION_CONFLICT", "Execution environment changed", 409)
                configs = [self._config(group, tx=tx) for group in groups]
            checks = []
            try:
                revision = self._framework()
                checks.append({"code": "framework", "ok": True, "message": "Committed framework verified", "revision": revision})
            except (CenterError, OSError, subprocess.SubprocessError) as exc:
                checks.append({"code": getattr(exc, "code", "FRAMEWORK_UNVERIFIED"), "ok": False,
                               "message": "Framework must be a clean committed compatible checkout",
                               "detail": "Review and commit framework changes, then check again."})
            if not self.adapter.available:
                checks.append({"code": "EXECUTION_DOMAIN_UNCONFIGURED", "ok": False,
                               "message": "Connect an existing execution environment first"})
            else:
                for config in {digest(config): config for config in configs}.values():
                    try:
                        dependencies = self.adapter.query("dependencies", engine=config["engine"], model=config["model"],
                                                          effort=config["effort"], product_language=config["productLanguage"])
                        details = dependencies.get("checks", [])
                        checks.extend({**item, "code": item.get("code", item.get("name")), "engine": config["engine"],
                                       "model": config["model"], "message": item.get("message") or item.get("reason") or item.get("name")}
                                      for item in details)
                        if not dependencies.get("ready", dependencies.get("ok", False)) or not details:
                            checks.append({"code": "DEPENDENCIES_UNAVAILABLE", "ok": False, "engine": config["engine"],
                                           "model": config["model"], "message": "Execution dependencies require attention"})
                    except (CenterError, OSError, ValueError, subprocess.SubprocessError) as exc:
                        checks.append({"code": "EXECUTION_DOMAIN_UNAVAILABLE", "ok": False,
                                       "message": "Execution environment could not be checked", "detail": type(exc).__name__})
            return {"ready": all(item.get("ok") is True for item in checks), "checks": checks,
                    "executionDomain": self.domain, "environmentRevision": environment["revision"]}

    def resolve_import_path(self, root):
        from center_paths import resolve_import_path
        with self._mutex, self.store.transaction() as tx:
            environment = self._environment_record(tx)
            return resolve_import_path(root, self.domain, environment["revision"], self.adapter)

    def execution_query(self, source_id, query, **kwargs):
        if isinstance(source_id, dict):
            source_id = source_id["sourceId"]
        if "path" in kwargs and "relative_path" not in kwargs:
            kwargs["relative_path"] = kwargs.pop("path")
        if query not in {"status", "config", "capabilities", "log", "recovery"} or set(kwargs) - {"relative_path", "offset", "limit"}:
            raise CenterError("INVALID_QUERY", "Unsupported execution query")
        with self.store.transaction() as tx:
            source = tx.get("sources", source_id)
            runtime = tx.get("runtimes", source.get("runtimeId")) if source and source.get("runtimeId") else None
        if not source:
            raise CenterError("NOT_FOUND", "Source not found", 404)
        if not runtime or not runtime.get("managed") or runtime.get("executionDomain") != self.domain:
            raise CenterError("READ_ONLY_SOURCE", "Source has no managed execution context", 403)
        marker = read_json(Path(source["root"]) / MARKER)
        if any(marker.get(key) != value for key, value in {"centerId": self.store.center_id, "runtimeId": runtime["runtimeId"],
               "entryId": source["entryId"], "sourceId": source_id}.items()):
            raise CenterError("SOURCE_CONFLICT", "Managed source identity changed", 409)
        result = self.adapter.query("query", root=source["root"], query=query, center_id=self.store.center_id,
                                    expected_product_id=source.get("productId"), **kwargs)
        observed = result.get("marker") or {}
        if any(observed.get(key) != marker.get(key) for key in ("centerId", "runtimeId", "entryId", "sourceId")):
            raise CenterError("SOURCE_CONFLICT", "Execution source identity changed", 409)
        return result


    def observe_source(self, source):
        status = self.execution_query(source["sourceId"], "status")
        # The runner owns POSIX facts; the bridge owns the explicitly selected
        # domain. Catalog observations require both to preserve provenance.
        status = {**status, "executionDomain": dict(self.domain)}
        settings = self.execution_query(source["sourceId"], "config").get("settings", {})
        engine = settings.get("ENGINE")
        configuration = {"engine": engine, "model": settings.get("MODEL") or settings.get({"codex": "CODEX_MODEL", "claude": "CLAUDE_MODEL", "cursor": "CURSOR_MODEL"}.get(engine, "OPENAI_COMPATIBLE_MODEL")),
                         "effort": settings.get("CODEX_REASONING_EFFORT") or settings.get("CODEX_EFFORT"), "productLanguage": settings.get("AUTONOMOUS_COMPANY_LANGUAGE") or settings.get("LANGUAGE")}
        return {"status": status, "config": configuration, "managed": True}


    @staticmethod
    def _control_error_detail(error):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/core"))
        from log_redaction import redact_text
        value = getattr(error, "stderr", None) or str(error)
        return redact_text(value).strip()[:2000]

    def _source_control(self, entry, source, runtime, action, body, idempotency):
        operation_id = uid("operation")
        manifest = {"operationId": operation_id, "action": action.replace("-", "_"),
                    "root": self.adapter.path(source["root"]), "centerId": self.store.center_id,
                    "runtimeId": runtime["runtimeId"], "entryId": entry["entryId"], "sourceId": source["sourceId"],
                    "productId": source.get("productId"), "reviewToken": body.get("reviewToken"),
                    "productCodeReviewed": body.get("confirmCodeEffects") is True,
                    "externalEffectsReviewed": body.get("confirmExternalEffects") is True,
                    "expectedDispatchId": body.get("expectedDispatchId")}
        path = self.data_dir / "operations" / operation_id / "control-manifest.json"
        atomic_json(path, manifest)
        operation = {"operationId": operation_id, "kind": action, "state": "preparing",
                     "sourceId": source["sourceId"], "entryId": entry["entryId"], "createdAt": now(), "revision": 1,
                     "actorKind": "local_operator_intent", "provenance": body.get("_provenance", {"channel": "local_api"})}
        with self.store.transaction() as tx:
            tx.put("operations", operation_id, operation)
            self._remember(tx, *idempotency, {"operationId": operation_id})
        try:
            result = self.adapter.query("control", manifest=path)
            if not result.get("ok"):
                raise CenterError("CONTROL_REFUSED", result.get("reason", "Execution control refused"), 409)
        except (CenterError, OSError, ValueError, subprocess.SubprocessError) as exc:
            with self.store.transaction() as tx:
                operation.update(state="failed", endedAt=now(), reason="recovery_unconfirmed", revision=2)
                tx.put("operations", operation_id, operation)
            raise CenterError("CONTROL_REFUSED", self._control_error_detail(exc), 409) from exc
        result = {**result, "operationId": operation_id}
        with self.store.transaction() as tx:
            operation.update(state="succeeded", endedAt=now(), revision=2, result=result)
            tx.put("operations", operation_id, operation)
        return result


    def _recovery_action(self, source_id, action, body):
        with self._mutex:
            with self.store.transaction() as tx:
                key, body_hash, previous = self._idempotent(tx, source_id + "/" + action, body)
                if previous:
                    operation = tx.get("operations", previous["operationId"])
                    if not operation or operation.get("state") != "succeeded":
                        raise CenterError("CONTROL_REFUSED", "Prior recovery is unconfirmed; perform a fresh review", 409)
                    return self._product_lock_view(operation["result"]) if previous.get("productLock") else operation["result"]
                source = tx.get("sources", source_id)
                if not source:
                    raise CenterError("NOT_FOUND", "Source not found", 404)
                self._expected(body, source)
                if self._revision_value(body, "expectedSourceRevision") != source["sourceRevision"]:
                    raise CenterError("SOURCE_CHANGED", "Source changed before review", 409)
                if any(row["sourceId"] == source_id and row["state"] in OPEN for row in tx.list("requests")) or self._busy_operation(tx, source_id):
                    raise CenterError("OPEN_REQUEST_EXISTS", "Resolve active work before recovery review", 409)
            entry, source, runtime = self._source(source["entryId"], source_id)
            try:
                result = self._source_control(entry, source, runtime, action, body, (key, body_hash))
            except CenterError as error:
                if (action == "review-recovery" and error.code == "CONTROL_REFUSED"
                        and str(error) == "Center admission/runtime refused: configuration_writer_active"):
                    result = self._product_lock_action(source_id, "review-product-lock", body)
                    with self.store.transaction() as tx:
                        self._remember(tx, key, body_hash, {"operationId": result["operationId"], "productLock": True})
                    return result
                raise
            if action == "review-recovery":
                result.update(canConfirm=result.get("writersStopped") is True and result.get("recoveryComplete") is True, checks=[{"code": "writers", "ok": result.get("writersStopped", False), "message": "Writers stopped"},
                              {"code": "recovery", "ok": result.get("recoveryComplete", False), "message": "Consensus and configuration recovered"}], reasons=[])
            refreshed = self._refresh_source(source_id)
            result.update(expectedRevision=refreshed["revision"], expectedSourceRevision=refreshed["sourceRevision"])
            with self.store.transaction() as tx:
                operation = tx.get("operations", result["operationId"])
                operation["result"] = result
                tx.put("operations", result["operationId"], operation)
                self._remember(tx, key, body_hash, {"operationId": result["operationId"]})
            return result


    @staticmethod
    def _product_lock_view(result):
        revisions = {key: result[key] for key in ("expectedRevision", "expectedSourceRevision") if key in result}
        if result.get("lockRecovered"):
            return {**{key: result[key] for key in ("ok", "lockRecovered", "reviewRequired", "resumed", "operationId")}, **revisions}
        return {"ok": True, "canConfirm": False, "canRecoverLock": True,
                **revisions,
                "lockReviewToken": result["lockReviewToken"], "operationId": result["operationId"],
                "checks": [{"code": "known_writers", "ok": True, "message": "Known center, loop, preview and configuration writers are stopped"},
                           {"code": "product_lock", "ok": False, "message": "The empty product-state lock has no writer identity; all other writers must be confirmed stopped by the operator"}],
                "reasons": ["configuration_writer_active"], "directoryOwnerKnown": False}


    def _product_lock_action(self, source_id, action, body):
        with self._mutex:
            framework_head = self._framework()
            with self.store.transaction() as tx:
                key, body_hash, previous = self._idempotent(tx, source_id + "/" + action, body)
                if previous:
                    operation = tx.get("operations", previous["operationId"])
                    if operation.get("state") != "succeeded":
                        raise CenterError("CONTROL_REFUSED", "Prior lock recovery is unconfirmed; perform a fresh review", 409)
                    return self._product_lock_view(operation["result"])
                source = tx.get("sources", source_id)
                if not source:
                    raise CenterError("NOT_FOUND", "Source not found", 404)
                self._expected(body, source)
                if self._revision_value(body, "expectedSourceRevision") != source["sourceRevision"]:
                    raise CenterError("SOURCE_CHANGED", "Source changed before directory lock review", 409)
                if any(row["sourceId"] == source_id and row["state"] in OPEN for row in tx.list("requests")) or self._busy_operation(tx, source_id):
                    raise CenterError("OPEN_REQUEST_EXISTS", "Resolve active work before directory lock review", 409)
                requests = sorted([row for row in tx.list("requests") if row["sourceId"] == source_id and row.get("startedAt")],
                                  key=lambda row: (row["createdAt"], row["requestId"]), reverse=True)
                if not requests or not self._cleaned_execution(tx, requests[0]):
                    raise CenterError("OWNER_RECOVERY_REQUIRED", "A trusted stopped and cleaned execution is required", 409)
                request = requests[0]
                review_operation = next((row for row in tx.list("operations") if row.get("kind") == "review-product-lock"
                                         and row.get("sourceId") == source_id and row.get("state") == "succeeded"
                                         and not row.get("result", {}).get("tokenConsumedBy")
                                         and not row.get("result", {}).get("tokenSupersededBy")
                                         and row.get("result", {}).get("lockReviewToken") == body.get("lockReviewToken")), None)
                review = review_operation.get("result") if review_operation else None
                if action == "confirm-product-lock" and not review:
                    raise CenterError("CONTROL_REFUSED", "Directory lock review is unavailable", 409)
            entry, source, runtime = self._source(source["entryId"], source_id)
            marker = read_json(Path(source["root"]) / MARKER)
            with self.store.transaction() as tx:
                creation = tx.get("operations", marker.get("operationId"))
                if (not creation or creation.get("kind") != "exploration" or creation.get("state") != "succeeded"
                        or creation.get("reserved", {}).get("runtimeId") != runtime["runtimeId"]
                        or any(creation.get("reserved", {}).get(field) != marker.get(field) for field in ("runtimeId", "entryId", "sourceId"))
                        or runtime.get("frameworkRevision") != creation.get("frameworkRevision")
                        or marker.get("frameworkRevision", creation.get("frameworkRevision")) != creation.get("frameworkRevision")
                        or creation.get("preparationAttempt") != marker.get("preparationAttempt")
                        or runtime.get("preparationAttempt") != marker.get("preparationAttempt")):
                    raise CenterError("SOURCE_CONFLICT", "Directory lock recovery provenance differs", 409)
                intent = read_json(self._preparation_staging(creation) / "intent.json")
                target = self.data_dir / "runtimes" / creation["reserved"]["runtimeId"]
                expected_intent = {"operationId": creation["operationId"], "centerId": self.store.center_id,
                                   "reserved": creation["reserved"], "frameworkRevision": creation["frameworkRevision"], "target": str(target)}
                if creation.get("preparationAttempt"):
                    expected_intent["preparationAttempt"] = creation["preparationAttempt"]
                if intent != expected_intent or Path(source["root"]).resolve() != target.resolve():
                    raise CenterError("SOURCE_CONFLICT", "Preparation genesis differs", 409)
                operation_id = uid("operation")
                operation = {"operationId": operation_id, "kind": action, "state": "preparing", "entryId": entry["entryId"],
                             "sourceId": source_id, "createdAt": now(), "revision": 1,
                             "actorKind": "local_operator_intent", "provenance": body.get("_provenance", {"channel": "local_api"})}
                tx.put("operations", operation_id, operation)
                if action == "review-product-lock":
                    for previous_review in tx.list("operations"):
                        previous_result = previous_review.get("result") or {}
                        if (previous_review.get("kind") == action and previous_review.get("sourceId") == source_id
                                and previous_review.get("state") == "succeeded" and previous_result.get("lockReviewToken")
                                and not previous_result.get("tokenConsumedBy") and not previous_result.get("tokenSupersededBy")):
                            previous_result["tokenSupersededBy"] = operation_id
                            previous_review["revision"] += 1
                            tx.put("operations", previous_review["operationId"], previous_review)
                if action == "confirm-product-lock":
                    review_operation["result"]["tokenConsumedBy"] = operation_id
                    review_operation["revision"] += 1
                    tx.put("operations", review_operation["operationId"], review_operation)
                self._remember(tx, key, body_hash, {"operationId": operation_id})
            manifest = {**{field: marker[field] for field in ("centerId", "runtimeId", "entryId", "sourceId")},
                        "root": self.adapter.path(source["root"]), "action": action.replace("-", "_"),
                        "expectedMarker": marker, "frameworkRevision": creation["frameworkRevision"],
                        "frameworkHead": framework_head,
                        "genesisTarget": self.adapter.path(target),
                        "sourceRevision": review.get("reviewSourceRevision", source["sourceRevision"]) if review else source["sourceRevision"],
                        "expectedDispatchId": request["dispatchId"],
                        "expectedRequestId": request["requestId"], "expectedNonce": request["nonce"], "review": review,
                        "lockReviewToken": body.get("lockReviewToken"),
                        "confirmAllWritersStopped": body.get("confirmAllWritersStopped") is True,
                        "confirmLockRecoveryScope": body.get("confirmLockRecoveryScope") is True}
            path = self.data_dir / "operations" / operation_id / "product-lock-manifest.json"
            atomic_json(path, manifest)
            try:
                result = {**self.adapter.query("product-lock-recovery", manifest=path), "operationId": operation_id}
                if not result.get("ok"):
                    raise CenterError("CONTROL_REFUSED", result.get("reason", "Directory lock recovery refused"), 409)
                if action == "review-product-lock":
                    result["reviewSourceRevision"] = source["sourceRevision"]
            except (CenterError, OSError, ValueError, subprocess.SubprocessError) as error:
                with self.store.transaction() as tx:
                    operation.update(state="failed", endedAt=now(), reason="lock_recovery_unconfirmed")
                    tx.put("operations", operation_id, operation)
                detail = self._control_error_detail(error)
                raise CenterError("CONTROL_REFUSED", detail, 409) from error
            refreshed = self._refresh_source(source_id)
            result.update(expectedRevision=refreshed["revision"], expectedSourceRevision=refreshed["sourceRevision"])
            with self.store.transaction() as tx:
                operation.update(state="succeeded", endedAt=now(), result=result)
                tx.put("operations", operation_id, operation)
            return self._product_lock_view(result)


    def _cleaned_execution(self, tx, request):
        receipt = request.get("receipt") or {}
        if (not isinstance(receipt, dict) or request.get("state") != "ended"
                or receipt.get("state") != "terminal" or receipt.get("cleanupConfirmed") is not True
                or receipt.get("launched") is not True or receipt.get("centerId") != self.store.center_id
                or receipt.get("reason") != request.get("terminalReason")
                or any(not request.get(field) or receipt.get(field) != request[field]
                       for field in ("requestId", "dispatchId", "entryId", "sourceId", "runtimeId", "nonce"))):
            return False
        return any(event.get("requestId") == request["requestId"] and event.get("actorKind") == "runner"
                   and event.get("toState") == "ended" and event.get("reason") == request["terminalReason"]
                   and event.get("provenance", {}).get("channel") == "runner_receipt"
                   and event.get("provenance", {}).get("receiptId") == request["dispatchId"] for event in tx.list("events"))


    def start(self):
        if self._thread is None:
            with self.store.transaction() as tx:
                preparations = [row["operationId"] for row in tx.list("operations") if row.get("kind") == "exploration"
                                and row.get("state") == "attention" and row.get("reason") == "recovery_required"]
            for operation_id in preparations:
                self._worker(self._prepare_exploration, operation_id)
            self._heartbeat_thread = threading.Thread(target=self._heartbeat, name="center-heartbeat", daemon=True)
            self._heartbeat_thread.start()
            self._thread = threading.Thread(target=self._supervise, name="center-supervisor", daemon=True)
            self._thread.start()

    def close(self):
        # Callers intentionally shutting down the backend also stop its work.
        self._closing.set()
        with self._mutex:
            with self.store.transaction() as tx:
                self._pause(tx, "center_shutdown")
                for request in tx.list("requests"):
                    if request["state"] in {"starting", "running", "stopping"} or request["state"] == "attention" and request.get("dispatchId"):
                        self._stop_tx(tx, request, {}, "center", "center_shutdown")
                self._stop_media_tx(tx)
            self._write_controls()
        if self._thread:
            self._thread.join()
        if self._heartbeat_thread:
            self._heartbeat_thread.join()
        for worker in list(self._workers):
            # Clone/media commands have their own bounded deadlines. Storage
            # ownership outlives their final audit write, including shutdown.
            worker.join()

    @staticmethod
    def _revision_value(body, field):
        value = body.get(field)
        if value is not None and (type(value) is not int or not 0 <= value <= 9007199254740991):
            raise CenterError("INVALID_REQUEST", f"{field} must be an integer")
        return value

    def _expected(self, body, record=None):
        expected = self._revision_value(body, "expectedRevision")
        actual = record.get("revision", 0) if record else self.store.revision
        if expected is not None and expected != actual:
            raise CenterError("REVISION_CONFLICT", "The item changed; refresh before retrying", 409, {"revision": actual})

    def _idempotent(self, tx, scope, body):
        if self._closing.is_set():
            raise CenterError("CENTER_CLOSING", "Center is shutting down", 503)
        key = body.get("idempotencyKey")
        if not isinstance(key, str) or not 8 <= len(key) <= 200:
            raise CenterError("IDEMPOTENCY_REQUIRED", "A stable idempotency key is required")
        identity = digest([scope, key])
        body_hash = digest({key: value for key, value in body.items() if key != "_provenance"})
        previous = tx.get("idempotency", identity)
        if previous and previous["bodyHash"] != body_hash:
            raise CenterError("IDEMPOTENCY_CONFLICT", "The idempotency key belongs to different input", 409)
        return identity, body_hash, previous.get("result") if previous else None

    def _remember(self, tx, identity, body_hash, result):
        tx.put("idempotency", identity, {"bodyHash": body_hash, "result": result, "createdAt": now()})

    def _event(self, tx, request, before, actor, reason=None, body=None):
        event_id = uid("event")
        supplied = (body or {}).get("_provenance", {})
        provenance = {key: supplied[key] for key in ("channel", "actionId", "sessionId", "receiptId") if key in supplied}
        provenance.setdefault("channel", {"local_operator_intent": "local_api", "runner": "runner_receipt", "recovery": "reconciliation"}.get(actor, "center"))
        if actor == "runner" and request.get("dispatchId"):
            provenance.setdefault("receiptId", request["dispatchId"])
        tx.put("events", event_id, {"eventId": event_id, "requestId": request["requestId"], "fromState": before,
                                   "toState": request["state"], "actorKind": actor, "authenticatedUserId": None,
                                   "provenance": provenance, "recordedAt": now(), "reason": reason})

    def _transition(self, tx, request, state, actor, reason=None, body=None, **fields):
        old = request["state"]
        if state != old and state not in EDGES.get(old, set()):
            raise CenterError("INVALID_TRANSITION", "The request is already in a different state", 409)
        if old in TERMINAL:
            return request
        request.update(state=state, revision=request.get("revision", 0) + 1, **fields)
        if state != "running":
            request.update(executionBlockedReason=None, executionBlockedAt=None)
        if state in TERMINAL:
            request["endedAt"] = now()
            request["attentionReason"] = None
        tx.put("requests", request["requestId"], request)
        self._event(tx, request, old, actor, reason, body)
        return request

    @staticmethod
    def _revoke_start_authorizations(tx):
        for request in tx.list("requests"):
            if request["state"] == "queued" and request.get("startAuthorized"):
                request.update(startAuthorized=False, revision=request["revision"] + 1)
                tx.put("requests", request["requestId"], request)
        for operation in tx.list("operations"):
            if (operation.get("kind") == "exploration" and operation.get("state") in {"preparing", "attention"}
                    and operation.get("input", {}).get("executionMode") == "start_now" and not operation.get("authorizationRevoked")):
                operation.update(authorizationRevoked=True, revision=operation["revision"] + 1)
                tx.put("operations", operation["operationId"], operation)

    def _pause(self, tx, reason):
        self._revoke_start_authorizations(tx)
        queue = tx.get("controls", "queue")
        if queue.get("dispatchEnabled") or queue.get("reason") != reason:
            queue.update(dispatchEnabled=False, reason=reason, revision=queue["revision"] + 1)
        tx.put("controls", "queue", queue)

    def _pause_request(self, tx, request, reason):
        # Legacy single-owner recovery remains conservative. Independent project
        # errors hold only that project's request; provider/domain failures are shared.
        if request.get("ownershipProtocol", 1) < 2 or reason in {"provider_pause", "runner_unavailable", "center_shutdown"}:
            self._pause(tx, reason)

    def summary(self):
        with self.store.transaction() as tx:
            requests, queue = tx.list("requests"), tx.get("controls", "queue")
            entries = [entry for entry in tx.list("entries") if not entry.get("detached")]
            preparations = [row for row in tx.list("operations") if row.get("kind") == "exploration" and not row.get("archived")]
            current = [self._request_view(tx, request) for request in requests if request["state"] in ACTIVE and request.get("dispatchId")]
            return {"dispatchEnabled": queue["dispatchEnabled"], "queueRevision": queue["revision"], "currentRequest": current[0] if current else None,
                    "currentRequests": current, "occupiedCount": len(current), "maxConcurrentProjects": queue["maxConcurrentProjects"],
                    "queuedCount": sum(row["state"] == "queued" for row in requests),
                    "attentionCount": sum(row["state"] == "attention" for row in requests)
                                      + sum(row["state"] in {"failed", "attention"} for row in preparations),
                    "preparationCount": sum(row["state"] == "preparing" for row in preparations),
                    "counts": {kind: sum(row.get("kind") == kind for row in entries) for kind in ("product", "exploration", "legacy", "reference")},
                    "language": tx.get("preferences", "main")["language"], "executionDomain": self.domain,
                    "executionAvailable": self.adapter.available, "dispatchReason": queue.get("reason")}

    def decorate_entry(self, entry):
        """Cheap list projection; live evidence is cached by the supervisor."""
        result = dict(entry)
        with self.store.transaction() as tx:
            rows = sorted([row for row in tx.list("requests") if row["entryId"] == entry["entryId"]], key=lambda row: row["createdAt"], reverse=True)
            request = next((row for row in rows if row["state"] in OPEN), rows[0] if rows else None)
            runtime = tx.get("runtimes", entry.get("runtimeId")) if entry.get("runtimeId") else None
            source = tx.get("sources", entry.get("sourceId")) if entry.get("sourceId") else None
            busy = any(row["state"] in ACTIVE for row in rows) or self._busy_operation(tx, entry.get("sourceId"))
            preparations = [row for row in tx.list("operations") if row.get("reserved", {}).get("entryId") == entry["entryId"] and row.get("state") == "preparing"]
            last_execution = next((row for row in rows if row.get("startedAt")), None)
            cleaned_execution = bool(last_execution and self._cleaned_execution(tx, last_execution))
        if request:
            state = request["state"]
            if state in {"starting", "running", "stopping"} and not recently_confirmed(request):
                state = "unknown"
            elif state == "running" and request.get("executionBlockedReason"):
                state = "blocked"
            if state == "failed":
                state = "attention"
            elif state == "canceled":
                state = "ended"
            result["executionSummary"] = {"state": state, "requestId": request["requestId"], "terminalReason": request.get("terminalReason"),
                                          "attentionReason": request.get("attentionReason"), "reason": request.get("executionBlockedReason") if state == "blocked" else None}
        else:
            readonly = not entry.get("runtimeId") and entry.get("availability") == "available"
            result["executionSummary"] = {"state": "preparing" if preparations else "idle" if runtime and runtime.get("managed") else "read_only" if readonly else "unknown",
                                          "reason": None if runtime and runtime.get("managed") else "read_only_source" if readonly else "unmanaged_source"}
        executable = bool(runtime and runtime.get("managed") and runtime.get("executionDomain") == self.domain and self.adapter.available
                          and entry.get("availability") == "available" and not entry.get("archived") and not entry.get("detached"))
        if executable:
            try:
                marker = read_json(Path(runtime["root"]) / MARKER)
                executable = all(marker.get(key) == value for key, value in {"centerId": self.store.center_id, "runtimeId": runtime["runtimeId"],
                                      "entryId": entry["entryId"], "sourceId": entry["sourceId"]}.items())
            except (OSError, ValueError, KeyError):
                executable = False
        owned = executable
        observation = {}
        if source and self.adapter.available and owned:
            try:
                observation = self.execution_query(source["sourceId"], "capabilities")
            except subprocess.CalledProcessError as exc:
                if (exc.stderr or "").strip() == "Center admission/runtime refused: ownership_changed":
                    observation = {"context": {"valid": False, "reason": "ownership_changed"}}
                else:
                    observation = {}
            except (CenterError, OSError, ValueError, subprocess.SubprocessError):
                observation = {}
        context = observation.get("context") or {"valid": False, "reason": "context_unavailable"}
        if source and source.get("productId") and context.get("valid") and context.get("productId") != source["productId"]:
            context = {"valid": False, "reason": "product_registration_invalid"}
        control_compatible = observation.get("compatible", False)
        execution_reason = context.get("reason") if not context.get("valid") else "runtime_incompatible" if not control_compatible else observation.get("protectiveReason") or observation.get("governanceReason")
        if source and not (runtime and runtime.get("managed")) and self.adapter.available:
            try:
                observation = self.adapter.query("query", root=source["root"], query="capabilities")
                context = observation.get("context") or {"valid": False, "reason": "context_unavailable"}
                control_compatible = observation.get("compatible", False)
                execution_reason = context.get("reason") if not context.get("valid") else "runtime_incompatible" if not control_compatible else observation.get("protectiveReason") or observation.get("governanceReason")
            except (CenterError, OSError, ValueError, subprocess.SubprocessError):
                pass
        executable = owned and execution_reason is None
        takeover = False
        if source and not (runtime and runtime.get("managed")) and self.adapter.available and entry.get("kind") in {"product", "exploration"} and entry.get("availability") == "available" and not entry.get("archived"):
            takeover = control_compatible and execution_reason is None
        result["capabilities"] = {**entry.get("capabilities", {}), "execute": executable,
                                  "preview": executable and bool(entry.get("productId")) and not busy,
                                  "capture": executable and bool(entry.get("productId")) and not busy,
                                  "previewStop": owned and bool(entry.get("productId")) and not busy,
                                  "takeover": takeover, "release": owned and not any(row["state"] in OPEN for row in rows) and not busy}
        result["managedByCenter"] = owned
        reviewable = owned and not busy and not any(row["state"] in OPEN for row in rows) and observation.get("pauseReason") == "interrupted_cycle"
        result["recovery"] = {"pauseReason": observation.get("pauseReason"), "canReview": reviewable and control_compatible,
                              "canReviewLock": reviewable and cleaned_execution and observation.get("productLock", {}).get("emptyDirectory") is True}
        result["capabilities"]["reviewRecovery"] = result["recovery"]["canReview"]
        result["capabilities"]["reviewProductLock"] = result["recovery"]["canReviewLock"]
        result["sourceRecordRevision"] = source.get("revision") if source else None
        result["capabilityReasons"] = {"execute": "execution_domain_unconfigured" if not self.adapter.available else "read_only_source" if not owned else execution_reason,
                                       "takeover": None if takeover else "execution_domain_unconfigured" if not self.adapter.available else execution_reason or "runtime_incompatible",
                                       "release": "execution_domain_unconfigured" if not self.adapter.available else "read_only_source" if not owned else
                                                  "open_request_exists" if any(row["state"] in OPEN for row in rows) else "slot_busy" if busy else None,
                                       "previewStop": "execution_domain_unconfigured" if not self.adapter.available else "read_only_source" if not owned else "slot_busy" if busy else None,
                                       "media": "slot_busy" if busy else None}
        return result



    def list_requests(self, query=None):
        query = query or {}
        with self.store.transaction() as tx:
            items = tx.list("requests")
            if query.get("state"):
                items = [row for row in items if row["state"] == query["state"]]
            items.sort(key=lambda row: (row.get("order", 0), row["createdAt"]))
            return {"items": [self._request_view(tx, row) for row in items], "revision": tx.get("controls", "queue")["revision"]}

    @staticmethod
    def _request_view(tx, request):
        entry = tx.get("entries", request["entryId"]) or {}
        projection = tx.get("projections", request["sourceId"]) or {}
        visible = {key: value for key, value in request.items() if key not in {"nonce", "configFingerprint"}}
        if request["state"] != "running" or not recently_confirmed(request):
            visible.update(executionBlockedReason=None, executionBlockedAt=None)
        if isinstance(visible.get("receipt"), dict):
            visible["receipt"] = {key: value for key, value in visible["receipt"].items() if key not in {"root", "nonce"}}
        return {**visible, "displayName": projection.get("displayName") or entry.get("displayName"),
                "entryKind": entry.get("kind"), "cycleNumber": projection.get("cycleNumber"), "reportedPhase": projection.get("reportedPhase")}

    def get_request(self, request_id):
        with self.store.transaction() as tx:
            request = tx.get("requests", request_id)
            if not request:
                raise CenterError("NOT_FOUND", "Request not found", 404)
            return {**self._request_view(tx, request), "events": sorted([row for row in tx.list("events") if row.get("requestId") == request_id], key=lambda row: row["recordedAt"])}

    def _source(self, entry_id, source_id=None):
        entry, source, _ = self.catalog.resolve_source(entry_id, source_id)
        with self.store.transaction() as tx:
            runtime = tx.get("runtimes", source.get("runtimeId")) if source.get("runtimeId") else None
        if entry.get("archived") or entry.get("detached") or source.get("availability") not in {"available", None}:
            raise CenterError("CONTEXT_UNAVAILABLE", "Source is unavailable or archived", 409)
        if not runtime or not runtime.get("managed") or runtime.get("executionDomain") != self.domain:
            raise CenterError("READ_ONLY_SOURCE", "Source has no managed execution context", 403)
        marker = read_json(Path(source["root"]) / MARKER)
        if any(marker.get(key) != value for key, value in {"centerId": self.store.center_id, "runtimeId": runtime["runtimeId"], "entryId": entry_id, "sourceId": source["sourceId"]}.items()):
            raise CenterError("SOURCE_CONFLICT", "Managed source identity changed", 409)
        return entry, source, runtime

    def _config(self, body, root=None, tx=None):
        config_revision = self._revision_value(body, "configRevision")
        if tx is not None:
            preferences = tx.get("preferences", "main")
        else:
            with self.store.transaction() as config_tx:
                preferences = config_tx.get("preferences", "main")
        if tx is not None:
            config, _ = profiles.defaults(tx, preferences)
        else:
            with self.store.transaction() as config_tx:
                config, _ = profiles.defaults(config_tx, preferences)
        supplied = body.get("config", {})
        if not isinstance(supplied, dict) or set(supplied) - set(config):
            raise CenterError("INVALID_CONFIG", "Unsupported execution configuration")
        config.update(supplied)
        profiles.validate(config)
        if config_revision is not None and config_revision != preferences["revision"]:
            raise CenterError("REVISION_CONFLICT", "Default configuration changed", 409)
        if root:
            sys.path.insert(0, str(self.framework_root / "scripts/core"))
            from localization import language_state
            language = language_state(Path(root), {"AUTONOMOUS_COMPANY_LANGUAGE": config["productLanguage"]})
            if language["locked"]:
                if "productLanguage" in supplied and supplied["productLanguage"] != language["language"]:
                    raise CenterError("PRODUCT_LANGUAGE_LOCKED", "Existing product language is immutable", 409)
                config["productLanguage"] = language["language"]
        config["configRevision"] = preferences["revision"]
        return config

    def _new_request(self, tx, entry, source, runtime, body, request_id=None):
        kind, mode = body.get("kind", "continue"), body.get("executionMode", "enqueue")
        if not isinstance(kind, str) or not isinstance(mode, str) or kind not in {"explore", "continue"} or mode not in {"enqueue", "start_now"}:
            raise CenterError("INVALID_REQUEST", "Invalid request kind or execution mode")
        rows = tx.list("requests")
        if any((row["entryId"] == entry["entryId"] or row["runtimeId"] == runtime["runtimeId"]) and row["state"] in OPEN for row in rows):
            raise CenterError("OPEN_REQUEST_EXISTS", "This entry already has an open request", 409)
        if mode == "start_now" and any(row["state"] == "queued" for row in rows):
            raise CenterError("SLOT_BUSY", "An earlier waiting request must be dispatched first", 409)
        config = self._config(body, source["root"], tx)
        request_id = request_id or uid("request")
        request = {"requestId": request_id, "entryId": entry["entryId"], "sourceId": source["sourceId"], "runtimeId": runtime["runtimeId"],
                   "displayName": entry.get("displayName"), "kind": kind, "state": "queued", "executionMode": mode,
                   "startAuthorized": mode == "start_now", "createdAt": now(), "startedAt": None, "endedAt": None,
                   "dispatchId": None, "revision": 1, "order": self._next_order(tx),
                   "terminalReason": None, "attentionReason": None, "reasonDetail": None, "config": config,
                   "sourceRevision": source["sourceRevision"], "configFingerprint": config_fingerprint(source["root"]),
                   "frameworkRevision": runtime.get("frameworkRevision"), "previousRequestId": body.get("previousRequestId"),
                   "executionScope": "managed_runtime", "budgetConfigRevision": digest({key: os.environ.get(key) for key in sorted(RUNTIME_ENV_NAMES) if key.startswith("USAGE_")}),
                   "ownershipProtocol": read_json(Path(source["root"]) / MARKER).get("protocolVersion", 1),
                   "permissionConfigRevision": digest({key: os.environ.get(key) for key in ("CODEX_SANDBOX_MODE", "CLAUDE_PERMISSION_MODE", "CURSOR_SANDBOX_MODE")})}
        tx.put("requests", request_id, request)
        self._event(tx, request, None, "local_operator_intent", "request_created", body)
        return request

    def create_request(self, body):
        with self._mutex:
            with self.store.transaction() as tx:
                key, body_hash, previous = self._idempotent(tx, "request", body)
                if previous:
                    return self._request_view(tx, tx.get("requests", previous["requestId"]))
                self._expected(body)
                expected_source = self._revision_value(body, "expectedSourceRevision")
                self._revision_value(body, "configRevision")
                for field in ("entryId", "sourceId", "runtimeId"):
                    value = body.get(field)
                    if value is not None and not isinstance(value, str):
                        raise CenterError("INVALID_REQUEST", f"{field} must be a string")
            entry, source, runtime = self._source(body.get("entryId"), body.get("sourceId"))
            if body.get("runtimeId") not in {None, runtime["runtimeId"]} or expected_source != source["sourceRevision"]:
                raise CenterError("SOURCE_CHANGED", "Source revision changed", 409)
            if not self.adapter.available:
                raise CenterError("EXECUTION_DOMAIN_UNCONFIGURED", "Execution domain is not configured", 409)
            check = self.adapter.query("preflight", root=source["root"], expected_product_id=source.get("productId"))
            if not check.get("quiescent"):
                raise CenterError(str(check.get("reason", "CONTEXT_UNAVAILABLE")).upper(), "Source cannot start until its current protection or owner is resolved", 409)
            with self.store.transaction() as tx:
                request = self._new_request(tx, entry, source, runtime, body)
                profiles.remember(tx, request["config"])
                self._remember(tx, key, body_hash, {"requestId": request["requestId"]})
                return self._request_view(tx, request)

    def _stop_tx(self, tx, request, body, actor="local_operator_intent", reason="user_stop"):
        if request["state"] not in {"starting", "running", "stopping", "attention"} or not request.get("dispatchId"):
            raise CenterError("NOT_STARTED", "Only an owned dispatch can be stopped", 409)
        expected_dispatch = body.get("expectedDispatchId")
        if expected_dispatch is not None and not isinstance(expected_dispatch, str):
            raise CenterError("INVALID_REQUEST", "expectedDispatchId must be a string")
        if expected_dispatch not in {None, request["dispatchId"]}:
            raise CenterError("DISPATCH_CONFLICT", "Dispatch identity changed", 409)
        request["stopRequested"] = True
        request["stopReason"] = reason
        self._transition(tx, request, "stopping", actor, reason, body)
        tx.put("controls", request["dispatchId"], {"stop": True, "reason": reason, "requestId": request["requestId"], "dispatchId": request["dispatchId"]})
        return request

    def request_action(self, request_id, action, body):
        with self._mutex:
            with self.store.transaction() as tx:
                key, body_hash, previous = self._idempotent(tx, request_id + "/" + action, body)
                if previous:
                    return tx.get("requests", request_id)
                request = tx.get("requests", request_id)
                if not request:
                    raise CenterError("NOT_FOUND", "Request not found", 404)
                self._expected(body, request)
                if action == "cancel":
                    if request["state"] != "queued":
                        raise CenterError("ALREADY_STARTED", "This request can no longer be canceled; use Stop", 409)
                    self._transition(tx, request, "canceled", "local_operator_intent", "user_cancel", body, terminalReason="user_cancel")
                elif action == "stop":
                    self._stop_tx(tx, request, body)
                elif action != "reconcile":
                    raise CenterError("INVALID_ACTION", "Unknown request action")
                self._remember(tx, key, body_hash, {"requestId": request_id})
            if action == "reconcile":
                self._reconcile(request)
            else:
                self._write_controls()
            return self.get_request(request_id)

    @staticmethod
    def _busy_operation(tx, source_id=None):
        return any(row.get("kind") not in {"exploration", "batch"} and row.get("state") in {"running", "preparing", "attention"}
                   and (source_id is None or row.get("sourceId") == source_id) for row in tx.list("operations"))

    @staticmethod
    def _stop_media_tx(tx):
        for operation in tx.list("operations"):
            if operation.get("kind") in {"capture", "preview_start", "preview_stop"} and operation.get("state") == "running":
                operation["stopRequested"] = True
                tx.put("operations", operation["operationId"], operation)

    def queue_action(self, action, body):
        with self._mutex:
            with self.store.transaction() as tx:
                key, body_hash, previous = self._idempotent(tx, "queue/" + action, body)
                if previous:
                    return tx.get("controls", "queue")
                queue = tx.get("controls", "queue")
                self._expected(body, queue)
                requests = tx.list("requests")
                if action == "resume":
                    if not self.adapter.available:
                        raise CenterError("EXECUTION_DOMAIN_UNCONFIGURED", "Select an execution domain first", 409)
                    queue.update(dispatchEnabled=True, reason=None)
                elif action == "capacity":
                    value = body.get("maxConcurrentProjects")
                    if value is not None and (type(value) is not int or value < 1):
                        raise CenterError("INVALID_CAPACITY", "Concurrency must be a positive integer or null for unlimited")
                    queue["maxConcurrentProjects"] = value
                elif action in {"pause", "stop-all"}:
                    self._revoke_start_authorizations(tx)
                    queue.update(dispatchEnabled=False, reason="user_pause" if action == "pause" else "stop_all")
                    if action == "stop-all":
                        self._stop_media_tx(tx)
                        for request in requests:
                            if request["state"] in ACTIVE and request.get("dispatchId"):
                                self._stop_tx(tx, request, body, reason="user_stop")
                elif action == "order":
                    ordered = body.get("requestIds")
                    waiting = {row["requestId"] for row in requests if row["state"] == "queued"}
                    if not isinstance(ordered, list) or any(not isinstance(value, str) for value in ordered):
                        raise CenterError("INVALID_REQUEST", "Queue order must be a list of request IDs")
                    if len(ordered) != len(set(ordered)) or set(ordered) != waiting:
                        raise CenterError("REVISION_CONFLICT", "Queue order must contain every waiting request exactly once", 409)
                    for index, request_id in enumerate(ordered):
                        request = tx.get("requests", request_id)
                        request.update(order=index, revision=request["revision"] + 1)
                        tx.put("requests", request_id, request)
                else:
                    raise CenterError("INVALID_ACTION", "Unknown queue action")
                queue["revision"] += 1
                tx.put("controls", "queue", queue)
                event_id = uid("event")
                tx.put("events", event_id, {"eventId": event_id, "actorKind": "local_operator_intent", "authenticatedUserId": None,
                                           "provenance": body.get("_provenance", {"channel": "local_api"}), "action": "queue/" + action, "recordedAt": now()})
                self._remember(tx, key, body_hash, queue)
            self._write_controls()
            return queue

    def preferences(self, body=None):
        with self.store.transaction() as tx:
            preferences = tx.get("preferences", "main")
            if body is None:
                defaults, origin = profiles.defaults(tx, preferences)
                return {**preferences, "defaults": defaults, "defaultsOrigin": origin,
                        "templates": tx.list("templates"), "executionDomain": self.domain, "executionAvailable": self.adapter.available}
            key, body_hash, previous = self._idempotent(tx, "preferences", body)
            if previous:
                return previous
            self._expected(body, preferences)
            updates = body.get("preferences", {key: value for key, value in body.items() if key in preferences and key != "revision"})
            if not isinstance(updates, dict) or set(updates) - {"language", "productLanguage", "engine", "model", "effort"}:
                raise CenterError("INVALID_PREFERENCE", "Unknown preference")
            candidate = {**preferences, **updates}
            if (any(not isinstance(candidate[field], str) for field in ("language", "productLanguage", "engine", "effort"))
                    or candidate["language"] not in {"zh-CN", "en"} or candidate["productLanguage"] not in {"zh-CN", "en"}
                    or candidate["engine"] not in ENGINES or candidate["effort"] not in EFFORTS):
                raise CenterError("INVALID_PREFERENCE", "Invalid preference")
            if not isinstance(candidate["model"], str) or len(candidate["model"]) > 200 or any(ord(c) < 32 for c in candidate["model"]):
                raise CenterError("INVALID_PREFERENCE", "Invalid model name")
            candidate["revision"] += 1
            if set(updates) & set(profiles.FIELDS):
                candidate["lastConfig"] = {key: candidate[key] for key in profiles.FIELDS}
            tx.put("preferences", "main", candidate)
            self._remember(tx, key, body_hash, candidate)
            return candidate

    def template_action(self, body):
        with self.store.transaction() as tx:
            key, body_hash, previous = self._idempotent(tx, "templates", body)
            if previous:
                return previous
            preferences = tx.get("preferences", "main")
            self._expected(body, preferences)
            action, template_id = body.get("action", "save"), body.get("templateId")
            template = tx.get("templates", template_id) if template_id else None
            if template_id and not template:
                raise CenterError("TEMPLATE_NOT_FOUND", "The selected template is unavailable", 404)
            if action == "save":
                name = body.get("name")
                if not isinstance(name, str) or not name.strip() or len(name) > 80 or any(ord(c) < 32 for c in name):
                    raise CenterError("INVALID_TEMPLATE", "Give the template a name of 1 to 80 characters")
                profiles.validate_template_name(tx, name, template_id)
                config = profiles.validate(body.get("config"))
                template_id = template_id or uid("template")
                template = {"templateId": template_id, "name": name.strip(), "config": config,
                            "revision": (template or {}).get("revision", 0) + 1}
                tx.put("templates", template_id, template)
                if body.get("makeDefault") is True:
                    preferences["defaultTemplateId"] = template_id
            elif action == "default":
                preferences["defaultTemplateId"] = template_id
            elif action == "delete" and template:
                tx.delete("templates", template_id)
                if preferences.get("defaultTemplateId") == template_id:
                    preferences["defaultTemplateId"] = None
            else:
                raise CenterError("INVALID_ACTION", "Unknown template action")
            preferences["revision"] += 1
            tx.put("preferences", "main", preferences)
            result = {"template": template, "defaultTemplateId": preferences.get("defaultTemplateId")}
            self._remember(tx, key, body_hash, result)
            return result

    def list_operations(self, query=None):
        query = query or {}
        with self.store.transaction() as tx:
            operations = [row for row in tx.list("operations") if row.get("kind") == "exploration"]
            if query.get("state"):
                operations = [row for row in operations if row["state"] == query["state"]]
            operations.sort(key=lambda row: (row["createdAt"], row["operationId"]), reverse=True)
            items = []
            for operation in operations:
                item = {key: operation.get(key) for key in ("operationId", "kind", "state", "createdAt", "endedAt", "revision", "reason", "batchId", "archived")}
                mutable = operation["state"] in {"failed", "attention"} and not operation.get("result") and not operation.get("archived")
                item["canRetry"] = item["canCancel"] = mutable and not tx.get("requests", operation["reserved"]["requestId"])
                for field in ("reserved", "result"):
                    values = operation.get(field)
                    item[field] = {key: values[key] for key in ("entryId", "sourceId", "runtimeId", "requestId") if key in values} if isinstance(values, dict) else None
                items.append(item)
            return {"items": items}

    def operation(self, operation_id):
        with self.store.transaction() as tx:
            operation = tx.get("operations", operation_id)
            if not operation:
                raise CenterError("NOT_FOUND", "Operation not found", 404)
            return operation

    def operation_action(self, operation_id, action, body):
        if action not in {"cancel", "archive", "retry", "restore-draft"}:
            raise CenterError("INVALID_ACTION", "Unknown preparation action")
        with self._mutex, self._prepare_mutex:
            with self.store.transaction() as tx:
                operation = tx.get("operations", operation_id)
                if not operation or operation.get("kind") != "exploration":
                    raise CenterError("NOT_FOUND", "Preparation not found", 404)
                key, body_hash, previous = self._idempotent(tx, operation_id + "/" + action, body) if action != "restore-draft" else (None, None, None)
                if previous:
                    return {"items": [tx.get("operations", identity) for identity in previous["operationIds"]]}
                self._expected(body, operation)
                batch_id = operation.get("batchId")
                members = [row for row in tx.list("operations") if row.get("kind") == "exploration" and
                           (row.get("batchId") == batch_id if batch_id else row["operationId"] == operation_id)]
                failed = [row for row in members if row["state"] in {"failed", "attention"} and not row.get("result") and not row.get("archived")]
                if operation["state"] not in {"failed", "attention", "canceled"} or operation.get("result"):
                    raise CenterError("OPERATION_BUSY", "Only failed preparations can be changed", 409)
                if action in {"retry", "restore-draft"} and (operation.get("archived") or operation["state"] == "canceled"):
                    raise CenterError("OPERATION_BUSY", "Archived preparations cannot be retried", 409)
                failed = sorted((row for row in failed if not tx.get("requests", row["reserved"]["requestId"])), key=lambda row: row.get("order", 0))
                if action == "restore-draft":
                    if not failed:
                        raise CenterError("OPERATION_BUSY", "No failed preparations remain", 409)
                    groups = {}
                    for row in failed:
                        original = row["input"]
                        identity = str(row.get("groupIndex", digest({key: original[key] for key in ("direction", "config")})))
                        group = groups.setdefault(identity, {"count": 0, "direction": original["direction"],
                                                  "config": {key: value for key, value in original["config"].items() if key != "configRevision"}})
                        group["count"] += 1
                    return {"draft": {"groups": list(groups.values()), "executionMode": "enqueue"},
                            "operationIds": [row["operationId"] for row in failed], "batchId": batch_id,
                            "completedCount": sum(row["state"] == "succeeded" for row in members)}
                if action == "retry":
                    selected = failed
                else:
                    selected = [operation]
                if not selected or any(row["state"] not in {"failed", "attention", "canceled"} or row.get("result") for row in selected):
                    raise CenterError("OPERATION_BUSY", "Only failed preparations can be changed", 409)
                for row in selected:
                    if tx.get("requests", row["reserved"]["requestId"]):
                        raise CenterError("OPEN_REQUEST_EXISTS", "Resolve the existing request first", 409)
                    if action == "retry":
                        target = self.data_dir / "runtimes" / row["reserved"]["runtimeId"]
                        if target.exists() or target.is_symlink() or any(tx.get(kind, row["reserved"][identity]) for kind, identity in
                                (("entries", "entryId"), ("sources", "sourceId"), ("runtimes", "runtimeId"))):
                            raise CenterError("RECOVERY_REQUIRED", "Published preparation requires recovery", 409)
                        if row.get("frameworkRevision"):
                            revision = self._framework()
                            if revision != row["frameworkRevision"]:
                                staging = self._preparation_staging(row)
                                original = {"operationId": row["operationId"], "centerId": self.store.center_id,
                                            "reserved": row["reserved"], "frameworkRevision": row["frameworkRevision"], "target": str(target)}
                                if row.get("preparationAttempt"):
                                    original["preparationAttempt"] = row["preparationAttempt"]
                                if staging.exists():
                                    try:
                                        matches = read_json(staging / "intent.json") == original
                                    except (OSError, ValueError):
                                        matches = False
                                    if not matches:
                                        raise CenterError("RECOVERY_REQUIRED", "Preparation ownership manifest differs", 409)
                                row.setdefault("preparationHistory", []).append({"frameworkRevision": row["frameworkRevision"],
                                    "preparationAttempt": row.get("preparationAttempt"), "state": row["state"],
                                    "reason": row.get("reason"), "reasonDetail": row.get("reasonDetail"), "endedAt": row.get("endedAt")})
                                row.update(frameworkRevision=revision, preparationAttempt=uid("attempt"))
                        row.update(state="preparing", reason=None, endedAt=None, archived=False,
                                   authorizationRevoked=True, authorizationSession=None)
                    else:
                        row.update(archived=True, endedAt=now(), authorizationRevoked=True)
                        if action == "cancel":
                            row.update(state="canceled", canceledReason="user_cancel")
                    row["revision"] += 1
                    tx.put("operations", row["operationId"], row)
                ids = [row["operationId"] for row in selected]
                self._remember(tx, key, body_hash, {"operationIds": ids})
            if action == "retry":
                self._worker(self._prepare_batch, ids)
            return {"items": selected}

    def _worker(self, function, *args):
        if self._closing.is_set():
            raise CenterError("CENTER_CLOSING", "Center is shutting down", 503)
        def target():
            try:
                function(*args)
            finally:
                self._workers.discard(threading.current_thread())
        worker = threading.Thread(target=target, daemon=True)
        self._workers.add(worker)
        worker.start()

    @staticmethod
    def _next_order(tx):
        return max([row.get("order", 0) for kind in ("requests", "operations") for row in tx.list(kind)] + [0]) + 1

    def _exploration_record(self, tx, body, batch_id=None):
        direction = body.get("direction", "")
        mode = body.get("executionMode", "enqueue")
        if not isinstance(direction, str) or len(direction) > 5000:
            raise CenterError("INVALID_DIRECTION", "Direction must be bounded text")
        if not isinstance(mode, str) or mode not in {"enqueue", "start_now"}:
            raise CenterError("INVALID_REQUEST", "Invalid execution mode")
        operation_id = uid("operation")
        reserved = {key: uid(prefix) for key, prefix in (("entryId", "entry"), ("sourceId", "source"), ("runtimeId", "runtime"), ("requestId", "request"))}
        operation = {"operationId": operation_id, "kind": "exploration", "state": "preparing", "createdAt": now(),
                     "reserved": reserved, "input": {"direction": direction, "executionMode": mode, "config": self._config(body, tx=tx)},
                     "authorizationSession": self._session_id, "queueRevision": tx.get("controls", "queue")["revision"],
                     "order": self._next_order(tx), "batchId": batch_id,
                     "revision": 1, "actorKind": "local_operator_intent", "authenticatedUserId": None,
                     "provenance": body.get("_provenance", {"channel": "local_api"})}
        tx.put("operations", operation_id, operation)
        return operation

    def _prepare_batch(self, operation_ids):
        for operation_id in operation_ids:
            if self._closing.is_set():
                return
            self._prepare_exploration(operation_id)

    def create_exploration(self, body):
        with self._mutex:
            with self.store.transaction() as tx:
                key, body_hash, previous = self._idempotent(tx, "exploration", body)
                if previous:
                    operation = tx.get("operations", previous["operationId"])
                    if operation["state"] == "attention" and operation.get("reason") == "recovery_required":
                        self._worker(self._prepare_exploration, operation["operationId"])
                    return operation
                self._expected(body)
                self._expected_environment(tx, body)
                if not self.adapter.available:
                    raise CenterError("EXECUTION_DOMAIN_UNCONFIGURED", "Execution domain is not configured", 409)
                operation = self._exploration_record(tx, body)
                profiles.remember(tx, operation["input"]["config"])
                self._remember(tx, key, body_hash, {"operationId": operation["operationId"]})
            self._worker(self._prepare_exploration, operation["operationId"])
            return operation

    def create_batch(self, body):
        with self._mutex:
            with self.store.transaction() as tx:
                key, body_hash, previous = self._idempotent(tx, "exploration-batch", body)
                if previous:
                    return {"items": [tx.get("operations", identity) for identity in previous["operationIds"]]}
                self._expected(body)
                self._expected_environment(tx, body)
                if not self.adapter.available:
                    raise CenterError("EXECUTION_DOMAIN_UNCONFIGURED", "Execution domain is not configured", 409)
                groups = body.get("groups")
                if not isinstance(groups, list) or not groups or any(not isinstance(group, dict) for group in groups):
                    raise CenterError("INVALID_BATCH", "Provide at least one configuration group")
                if any(type(group.get("count")) is not int or group["count"] < 1 for group in groups) or sum(group["count"] for group in groups) > 100:
                    raise CenterError("INVALID_BATCH", "Submit 1 to 100 projects per batch")
                batch_id, operations = uid("batch"), []
                for group_index, group in enumerate(groups):
                    for _ in range(group["count"]):
                        operation = self._exploration_record(tx, {**group, "executionMode": body.get("executionMode", "enqueue"),
                                          "_provenance": body.get("_provenance", {"channel": "local_api"})}, batch_id)
                        operation["groupIndex"] = group_index
                        tx.put("operations", operation["operationId"], operation)
                        operations.append(operation)
                profiles.remember(tx, operations[-1]["input"]["config"])
                ids = [operation["operationId"] for operation in operations]
                self._remember(tx, key, body_hash, {"operationIds": ids})
            self._worker(self._prepare_batch, ids)
            return {"items": operations}

    def _framework(self):
        status = subprocess.run(["git", "-C", str(self.framework_root), "status", "--porcelain", "--untracked-files=all"], stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True, timeout=15).stdout
        if status.strip():
            raise CenterError("FRAMEWORK_UNVERIFIED", "New contexts require a clean committed compatible framework", 409)
        revision = subprocess.run(["git", "-C", str(self.framework_root), "rev-parse", "HEAD"], stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True, timeout=15).stdout.strip()
        if not re.fullmatch(r"[0-9a-f]{40,64}", revision):
            raise CenterError("FRAMEWORK_UNVERIFIED", "Framework revision cannot be verified", 409)
        return revision

    def _preparation_staging(self, operation):
        staging = self.data_dir / "staging" / operation["operationId"]
        attempt = operation.get("preparationAttempt")
        if attempt:
            if not re.fullmatch(r"attempt_[0-9a-f]{32}", attempt):
                raise CenterError("RECOVERY_REQUIRED", "Preparation attempt identity differs", 409)
            staging = staging / "attempts" / attempt
        if any(path.is_symlink() for path in (staging, *staging.parents) if path != self.data_dir and self.data_dir in path.parents):
            raise CenterError("RECOVERY_REQUIRED", "Preparation staging ownership differs", 409)
        return staging

    def _prepare_exploration(self, operation_id):
        # Preparation may safely resume from the manifest, but never grants a
        # fresh execution authorization after restart or queue pause.
        with self._prepare_mutex:
            operation = self.operation(operation_id)
            if operation["state"] in {"succeeded", "canceled"} or operation.get("archived"):
                return
            reserved = operation["reserved"]
            staging = self._preparation_staging(operation)
            target = self.data_dir / "runtimes" / reserved["runtimeId"]
            try:
                revision = operation.get("frameworkRevision") or self._framework()
                staging.mkdir(parents=True, exist_ok=True)
                intent = staging / "intent.json"
                manifest = {"operationId": operation_id, "centerId": self.store.center_id, "reserved": reserved, "frameworkRevision": revision, "target": str(target)}
                attempt_identity = {"preparationAttempt": operation["preparationAttempt"]} if operation.get("preparationAttempt") else {}
                manifest.update(attempt_identity)
                if intent.exists() and read_json(intent) != manifest:
                    raise CenterError("RECOVERY_REQUIRED", "Preparation ownership manifest differs", 409)
                atomic_json(intent, manifest)
                with self.store.transaction() as tx:
                    operation = tx.get("operations", operation_id)
                    operation.update(frameworkRevision=revision, state="preparing", reason=None)
                    tx.put("operations", operation_id, operation)
                prepared = staging / "runtime"
                if not target.exists():
                    if not prepared.exists():
                        self.adapter.clone(self.framework_root, prepared, revision, staging)
                    actual = subprocess.run(["git", "-C", str(prepared), "rev-parse", "HEAD"], stdin=subprocess.DEVNULL, check=True, capture_output=True, text=True, timeout=15).stdout.strip()
                    if actual != revision or not (prepared / "scripts/core/center_runner.py").is_file():
                        raise CenterError("RUNTIME_INCOMPATIBLE", "Prepared framework identity differs", 409)
                    configuration = operation["input"]["config"]
                    harness = harness_capability(prepared, configuration['engine'])['supported']
                    (prepared / ".autonomous-company.local").write_text("AUTONOMOUS_COMPANY_LANGUAGE=" + configuration["productLanguage"] +
                        "\nCOMPANY_HARNESS_ENABLED=" + ('1' if harness else '0') + "\n", encoding="utf-8")
                    if operation["input"]["direction"]:
                        consensus = prepared / "memories/consensus.md"
                        if not consensus.exists():
                            shutil.copyfile(prepared / "memories/consensus.template.md", consensus)
                        text = consensus.read_text(encoding="utf-8")
                        heading = "## Human Overrides"
                        if heading not in text:
                            raise CenterError("RUNTIME_INCOMPATIBLE", "Framework has no human direction section", 409)
                        text = text.replace(heading, heading + "\n\n" + operation["input"]["direction"], 1)
                        consensus.write_text(text, encoding="utf-8")
                    atomic_json(prepared / MARKER, {"protocolVersion": 2, "centerId": self.store.center_id, **{key: reserved[key] for key in ("entryId", "sourceId", "runtimeId")}, "operationId": operation_id, **attempt_identity})
                    target.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(prepared, target)
                marker = read_json(target / MARKER)
                if marker.get("operationId") != operation_id or marker.get("centerId") != self.store.center_id or any(
                        marker.get(key) != reserved[key] for key in ("entryId", "sourceId", "runtimeId")):
                    raise CenterError("RECOVERY_REQUIRED", "Prepared target ownership cannot be verified", 409)
                if marker.get("preparationAttempt") != operation.get("preparationAttempt"):
                    raise CenterError("RECOVERY_REQUIRED", "Prepared attempt ownership cannot be verified", 409)
                entry = {"entryId": reserved["entryId"], "kind": "exploration", "productId": None, "explorationId": None,
                         "preferredSourceId": reserved["sourceId"], "archived": False, "detached": False, "revision": 1,
                         "displayName": None, "description": None, "direction": operation["input"]["direction"]}
                source = {"sourceId": reserved["sourceId"], "entryId": reserved["entryId"], "runtimeId": reserved["runtimeId"], "root": str(target),
                          "project": None, "productId": None, "explorationId": None, "kind": "exploration", "availability": "available",
                          "sourceRevision": 1, "revision": 1, "fingerprint": None, "identityFingerprint": None,
                          "capabilities": {"readJournal": True, "readMedia": True, "execute": True, "preview": False, "capture": False,
                                           "harness": harness_capability(target, operation['input']['config']['engine'])}}
                runtime = {"runtimeId": reserved["runtimeId"], "root": str(target), "entryId": reserved["entryId"], "sourceId": reserved["sourceId"],
                           "centerId": self.store.center_id, "protocolVersion": 2, "managed": True, "executionDomain": self.domain, "frameworkRevision": revision, **attempt_identity}
                with self.store.transaction() as tx:
                    operation = tx.get("operations", operation_id)
                    tx.put("entries", entry["entryId"], entry)
                    tx.put("sources", source["sourceId"], source)
                    tx.put("runtimes", runtime["runtimeId"], runtime)
                    config = {key: value for key, value in operation["input"]["config"].items() if key != "configRevision"}
                    request_body = {"kind": "explore", "executionMode": "enqueue", "config": config, "_provenance": operation["provenance"]}
                    request = tx.get("requests", reserved["requestId"])
                    if request is None:
                        request = self._new_request(tx, entry, source, runtime, request_body, reserved["requestId"])
                    elif request["state"] != "queued" or request["runtimeId"] != runtime["runtimeId"]:
                        raise CenterError("RECOVERY_REQUIRED", "Prepared request already changed state", 409)
                    request["config"] = operation["input"]["config"]
                    request["order"] = operation.get("order", request["order"])
                    request["batchId"] = operation.get("batchId")
                    request["preparationPending"] = True
                    tx.put("requests", request["requestId"], request)
                    if (operation["input"]["executionMode"] == "start_now" and operation.get("authorizationSession") == self._session_id
                            and not operation.get("authorizationRevoked") and not self._closing.is_set()):
                        request.update(startAuthorized=True, executionMode="start_now")
                        tx.put("requests", request["requestId"], request)
                    operation.update(state="succeeded", endedAt=now(), result=reserved, revision=operation["revision"] + 1)
                    tx.put("operations", operation_id, operation)
                # Source discovery owns product/exploration identities, never us.
                self._refresh_source(source["sourceId"], update_waiting=True)
                with self.store.transaction() as tx:
                    request = tx.get("requests", reserved["requestId"])
                    request["preparationPending"] = False
                    tx.put("requests", request["requestId"], request)
            except Exception as exc:
                with self.store.transaction() as tx:
                    operation = tx.get("operations", operation_id)
                    operation.update(state="attention" if target.exists() or (staging / "runtime").exists() else "failed",
                                     reason=getattr(exc, "code", "preparation_failed"), endedAt=now(), revision=operation["revision"] + 1)
                    tx.put("operations", operation_id, operation)

    def _refresh_source(self, source_id, update_waiting=False):
        source = self.catalog.refresh_source(source_id)
        if update_waiting:
            with self.store.transaction() as tx:
                for request in tx.list("requests"):
                    if request["sourceId"] == source_id and request["state"] == "queued":
                        request["sourceRevision"] = source["sourceRevision"]
                        tx.put("requests", request["requestId"], request)
        return source

    def source_action(self, source_id, action, body):
        if action in {"review-recovery", "confirm-recovery"}:
            return self._recovery_action(source_id, action, body)
        if action in {"review-product-lock", "confirm-product-lock"}:
            return self._product_lock_action(source_id, action, body)
        if action not in {"takeover", "release"}:
            raise CenterError("INVALID_ACTION", "Source action is not supported by runtime")
        with self._mutex:
            with self.store.transaction() as tx:
                _, _, previous_result = self._idempotent(tx, source_id + "/" + action, body)
                previous_operation = tx.get("operations", previous_result["operationId"]) if previous_result else None
            if previous_operation:
                return self._recover_binding(previous_operation) if previous_operation.get("state") == "attention" else previous_operation
            with self.store.transaction() as tx:
                key, body_hash, previous = self._idempotent(tx, source_id + "/" + action, body)
                if previous:
                    return tx.get("operations", previous["operationId"])
                source = tx.get("sources", source_id)
                if not source:
                    raise CenterError("NOT_FOUND", "Source not found", 404)
                self._expected(body, source)
                if any(row["state"] in OPEN and row["sourceId"] == source_id for row in tx.list("requests")):
                    raise CenterError("OPEN_REQUEST_EXISTS", "Resolve open requests before changing ownership", 409)
                entry = tx.get("entries", source["entryId"])
                if action == "takeover":
                    matching_entries = {row["entryId"] for row in tx.list("entries") if row["entryId"] == entry["entryId"] or
                                        entry.get("productId") and row.get("productId") == entry["productId"]}
                    if any(row.get("managed") and row.get("entryId") in matching_entries and row.get("sourceId") != source_id for row in tx.list("runtimes")):
                        raise CenterError("OWNER_CONFLICT", "Another managed source owns this product; release it first", 409)
            self.catalog.resolve_source(source["entryId"], source_id)
            if source.get("kind") in {"archive", "reference", "legacy"} or entry.get("kind") in {"legacy", "reference"}:
                raise CenterError("READ_ONLY_SOURCE", "This source cannot be taken over", 403)
            check = self.adapter.query("preflight", root=source["root"], center_id=self.store.center_id, allow_protected="1" if action == "release" else "0",
                                       require_context="0" if action == "release" else "1", expected_product_id=source.get("productId"))
            if not check.get("quiescent"):
                raise CenterError(str(check.get("reason", "CONTEXT_UNAVAILABLE")).upper(), "Source is not safely available for ownership change", 409)
            root = Path(source["root"])
            marker_path = root / MARKER
            existing = read_json(marker_path) if marker_path.exists() else None
            if existing and (existing.get("centerId") != self.store.center_id or existing.get("sourceId") != source_id):
                raise CenterError("OWNER_CONFLICT", "Another center or source owns this root", 409)
            operation_id = uid("operation")
            runtime_id = (existing or {}).get("runtimeId") or source.get("runtimeId") or uid("runtime")
            marker = {"protocolVersion": 2, "centerId": self.store.center_id, "runtimeId": runtime_id, "entryId": source["entryId"], "sourceId": source_id}
            operation = {"operationId": operation_id, "kind": action, "state": "running", "entryId": source["entryId"], "sourceId": source_id, "createdAt": now(), "revision": 1,
                         "actorKind": "local_operator_intent", "authenticatedUserId": None, "provenance": body.get("_provenance", {"channel": "local_api"})}
            with self.store.transaction() as tx:
                current_source = tx.get("sources", source_id)
                current_entry = tx.get("entries", source["entryId"])
                if (not current_source or current_source.get("revision") != source.get("revision") or current_source.get("sourceRevision") != source.get("sourceRevision") or current_source.get("root") != source.get("root")
                        or not current_entry or current_entry.get("detached") or current_entry.get("archived")
                        or current_entry.get("revision") != entry.get("revision")):
                    raise CenterError("SOURCE_CHANGED", "Source changed during ownership preflight", 409)
                if any(row.get("sourceId") == source_id and row.get("state") in {"running", "preparing", "attention"} for row in tx.list("operations")):
                    raise CenterError("OPERATION_BUSY", "Source has an unresolved operation", 409)
                tx.put("operations", operation_id, operation)
                tx.put("bindings", operation_id, {"operationId": operation_id, "sourceId": source_id, "oldMarker": existing, "marker": marker,
                                                    "root": str(root), "sourceRevision": source["sourceRevision"], "entryId": entry["entryId"],
                                                    "configFingerprint": config_fingerprint(root), "state": "prepared"})
                self._remember(tx, key, body_hash, {"operationId": operation_id})
            try:
                binding_path = self.data_dir / "operations" / operation_id / "binding.json"
                atomic_json(binding_path, {"action": action, "root": self.adapter.path(root), "oldMarker": existing, "marker": marker, "productId": source.get("productId")})
                self.adapter.query("bind", manifest=binding_path)
                with self.store.transaction() as tx:
                    if action == "takeover":
                        runtime = {**marker, "root": str(root), "managed": True, "executionDomain": self.domain, "frameworkRevision": body.get("frameworkRevision")}
                        tx.put("runtimes", runtime_id, runtime)
                        source.update(runtimeId=runtime_id, revision=source["revision"] + 1)
                        source["capabilities"].update(execute=True, preview=bool(source.get("productId")), capture=bool(source.get("productId")))
                        tx.put("sources", source_id, source)
                    else:
                        runtime = tx.get("runtimes", runtime_id)
                        if runtime:
                            runtime["managed"] = False
                            tx.put("runtimes", runtime_id, runtime)
                        source["capabilities"].update(execute=False, preview=False, capture=False)
                        source["revision"] += 1
                        tx.put("sources", source_id, source)
                    binding = tx.get("bindings", operation_id)
                    binding["state"] = "committed"
                    tx.put("bindings", operation_id, binding)
                    operation.update(state="succeeded", endedAt=now(), runtimeId=runtime_id)
                    tx.put("operations", operation_id, operation)
                return operation
            except Exception:
                with self.store.transaction() as tx:
                    operation.update(state="attention", reason="recovery_required")
                    tx.put("operations", operation_id, operation)
                raise

    def _recover_binding(self, operation):
        """Reconcile the existing intent only; never repeat uncertain OS writes."""
        operation_id, action = operation["operationId"], operation["kind"]
        with self.store.transaction() as tx:
            binding = tx.get("bindings", operation_id)
            source = tx.get("sources", operation["sourceId"])
            entry = tx.get("entries", source["entryId"]) if source else None
        if (not binding or not source or not entry or entry.get("detached") or entry.get("archived")
                or source["root"] != binding.get("root") or config_fingerprint(source["root"]) != binding.get("configFingerprint")):
            raise CenterError("RECOVERY_REQUIRED", "Binding source no longer matches its preparation manifest", 409)
        check = self.adapter.query("preflight", root=source["root"], center_id=self.store.center_id,
                                   allow_protected="1" if action == "release" else "0", require_context="0" if action == "release" else "1",
                                   expected_product_id=source.get("productId"))
        if not check.get("quiescent"):
            raise CenterError("RECOVERY_REQUIRED", "Binding process ownership is not confirmed stopped", 409)
        target = Path(source["root"]) / MARKER
        actual = read_json(target) if target.exists() else None
        desired = binding["marker"] if action == "takeover" else None
        if actual != desired and actual != binding.get("oldMarker"):
            raise CenterError("OWNER_CONFLICT", "Binding marker belongs to an unknown owner", 409)
        with self.store.transaction() as tx:
            if actual == desired:
                runtime_id = binding["marker"]["runtimeId"]
                if action == "takeover":
                    if any(row.get("managed") and row.get("entryId") == entry["entryId"] and row.get("sourceId") != source["sourceId"] for row in tx.list("runtimes")):
                        raise CenterError("OWNER_CONFLICT", "Another managed source owns this entry", 409)
                    runtime = {**binding["marker"], "root": source["root"], "managed": True, "executionDomain": self.domain, "frameworkRevision": None}
                    tx.put("runtimes", runtime_id, runtime)
                    source.update(runtimeId=runtime_id, revision=source["revision"] + 1)
                    source["capabilities"].update(execute=True, preview=bool(source.get("productId")), capture=bool(source.get("productId")))
                    tx.put("sources", source["sourceId"], source)
                else:
                    runtime = tx.get("runtimes", runtime_id)
                    if runtime:
                        runtime["managed"] = False
                        tx.put("runtimes", runtime_id, runtime)
                    source["capabilities"].update(execute=False, preview=False, capture=False)
                    source["revision"] += 1
                    tx.put("sources", source["sourceId"], source)
                binding["state"] = "committed"
                operation.update(state="succeeded", reason=None, endedAt=now(), runtimeId=runtime_id, recovered=True)
            else:
                binding["state"] = "not_started"
                operation.update(state="failed", reason="binding_not_applied", endedAt=now(), recovered=True)
            operation["revision"] += 1
            tx.put("bindings", operation_id, binding)
            tx.put("operations", operation_id, operation)
            event_id = uid("event")
            tx.put("events", event_id, {"eventId": event_id, "operationId": operation_id, "actorKind": "recovery",
                                       "authenticatedUserId": None, "provenance": {"channel": "binding_receipt"}, "recordedAt": now(), "state": operation["state"]})
        return operation

    def media_action(self, entry_id, action, body):
        action = {"preview/start": "preview_start", "preview/stop": "preview_stop", "media/capture": "capture"}.get(action, action)
        if action not in {"capture", "preview_start", "preview_stop"}:
            raise CenterError("INVALID_ACTION", "Unknown media action")
        with self._mutex:
            with self.store.transaction() as tx:
                _, _, previous_result = self._idempotent(tx, entry_id + "/" + action, body)
                previous_operation = tx.get("operations", previous_result["operationId"]) if previous_result else None
            if previous_operation:
                return self._recover_media(previous_operation) if previous_operation.get("state") == "attention" else previous_operation
            with self.store.transaction() as tx:
                key, body_hash, previous = self._idempotent(tx, entry_id + "/" + action, body)
                if previous:
                    return tx.get("operations", previous["operationId"])
                if any(row["state"] in ACTIVE and (row["entryId"] == entry_id or row.get("ownershipProtocol", 1) < 2)
                       for row in tx.list("requests")) or self._busy_operation(tx, body.get("sourceId")):
                    raise CenterError("SLOT_BUSY", "Media and managed execution are serialized", 409)
            entry, source, runtime = self._source(entry_id, body.get("sourceId"))
            self._expected(body, source)
            if not source.get("productId") or not source.get("project"):
                raise CenterError("UNSUPPORTED", "Media requires a current product", 422)
            operation_id = uid("operation")
            operation = {"operationId": operation_id, "kind": action, "state": "running", "entryId": entry_id, "sourceId": source["sourceId"], "createdAt": now(), "revision": 1}
            manifest = {"operationId": operation_id, "centerId": self.store.center_id, "runtimeId": runtime["runtimeId"], "entryId": entry_id, "sourceId": source["sourceId"],
                        "root": self.adapter.path(source["root"]), "project": source["project"], "productId": source["productId"], "action": action}
            path = self.data_dir / "operations" / operation_id / "manifest.json"
            atomic_json(path, manifest)
            with self.store.transaction() as tx:
                tx.put("operations", operation_id, operation)
                self._remember(tx, key, body_hash, {"operationId": operation_id})
            self._write_controls()
            self._worker(self._run_media, operation_id, path)
            return operation

    def _run_media(self, operation_id, path):
        try:
            result = self.adapter.media(path)
            state, reason = ("succeeded", None) if result.get("ok") else ("failed", result.get("reason", "media_failed"))
        except Exception:
            state, reason = "attention", "media_cleanup_unconfirmed"
        with self.store.transaction() as tx:
            operation = tx.get("operations", operation_id)
            operation.update(state=state, reason=reason, endedAt=now(), revision=operation["revision"] + 1)
            tx.put("operations", operation_id, operation)

    def _recover_media(self, operation):
        path = self.data_dir / "operations" / operation["operationId"] / "manifest.json"
        observed = self.adapter.query("media-status", manifest=path)
        receipt = observed.get("receipt")
        if observed.get("slotFree") and receipt and receipt.get("cleanupConfirmed") and receipt.get("state") == "terminal":
            result = receipt.get("result", {})
            with self.store.transaction() as tx:
                operation.update(state="succeeded" if result.get("ok") else "failed", reason=result.get("reason"), recovered=True,
                                 endedAt=receipt.get("endedAt"), revision=operation["revision"] + 1)
                tx.put("operations", operation["operationId"], operation)
        return operation

    def _control(self, request):
        path = self.data_dir / "runner" / request["dispatchId"]
        return path

    def _write_controls(self):
        with self._controls_mutex:
            self._publish_controls()

    def _publish_controls(self):
        with self.store.transaction() as tx:
            requests = [row for row in tx.list("requests") if row["state"] in ACTIVE and row.get("dispatchId")]
            operations = [row for row in tx.list("operations") if row.get("kind") in {"capture", "preview_start", "preview_stop"} and row.get("state") == "running"]
        for operation in operations:
            atomic_json(self.data_dir / "operations" / operation["operationId"] / "control.json",
                        {"operationId": operation["operationId"], "heartbeat": time.time(), "stop": bool(operation.get("stopRequested"))})
        for request in requests:
            if not request.get("nonce"):
                continue
            atomic_json(self._control(request) / "control.json", {"centerId": self.store.center_id, "requestId": request["requestId"],
                        "dispatchId": request["dispatchId"], "nonce": request["nonce"], "heartbeat": time.time(),
                        "stop": bool(request.get("stopRequested")), "reason": request.get("stopReason")})

    def _dispatch(self):
        with self.store.transaction() as tx:
            requests = tx.list("requests")
            active = [row for row in requests if row["state"] in ACTIVE and row.get("dispatchId")]
            limit = tx.get("controls", "queue")["maxConcurrentProjects"]
            if (limit is not None and len(active) >= limit) or any(row.get("ownershipProtocol", 1) < 2 for row in active):
                return
            queued = sorted([row for row in requests if row["state"] == "queued"], key=lambda row: (row["order"], row["createdAt"]))
            if not queued:
                return
            request = next((row for row in queued if not self._busy_operation(tx, row["sourceId"])), None)
            if request is None:
                return
            if request.get("ownershipProtocol", 1) < 2 and (active or self._busy_operation(tx)):
                return
            if any(row.get("kind") == "exploration" and row.get("state") == "preparing"
                   and row.get("order", float("inf")) < request["order"] for row in tx.list("operations")):
                return
            if request.get("preparationPending"):
                pending = request
            else:
                pending = None
            if not tx.get("controls", "queue")["dispatchEnabled"] and not request.get("startAuthorized"):
                if pending is None:
                    return
        if pending:
            self._refresh_source(pending["sourceId"], update_waiting=True)
            with self.store.transaction() as tx:
                pending = tx.get("requests", pending["requestId"])
                pending["preparationPending"] = False
                tx.put("requests", pending["requestId"], pending)
            return
        try:
            entry, source, runtime = self._source(request["entryId"], request["sourceId"])
            fresh = self.catalog.refresh_source(source["sourceId"])
            if fresh["sourceRevision"] != request["sourceRevision"] or config_fingerprint(source["root"]) != request["configFingerprint"]:
                raise CenterError("SOURCE_CHANGED", "Source or configuration changed while waiting", 409)
            if request.get("budgetConfigRevision") != digest({key: os.environ.get(key) for key in sorted(RUNTIME_ENV_NAMES) if key.startswith("USAGE_")}):
                raise CenterError("CONFIG_CHANGED", "Budget configuration changed while waiting", 409)
            if request.get("permissionConfigRevision") != digest({key: os.environ.get(key) for key in ("CODEX_SANDBOX_MODE", "CLAUDE_PERMISSION_MODE", "CURSOR_SANDBOX_MODE")}):
                raise CenterError("CONFIG_CHANGED", "Permission configuration changed while waiting", 409)
            probe = self.adapter.query("probe", center_id=self.store.center_id,
                                       runtime_id=request["runtimeId"] if request.get("ownershipProtocol", 1) >= 2 else None)
            check = self.adapter.query("preflight", root=source["root"], expected_product_id=source.get("productId"))
            previous_owner = probe.get("owner")
            if (not probe["slotFree"] or not check["quiescent"] or
                    previous_owner and (previous_owner.get("state") != "terminal" or not previous_owner.get("cleanupConfirmed"))):
                raise CenterError(str(check.get("reason") or "owner_conflict").upper(), "Slot or source ownership requires attention", 409)
        except Exception as exc:
            with self.store.transaction() as tx:
                self._transition(tx, request, "attention", "center", getattr(exc, "code", "preflight_failed"), attentionReason="preflight", reasonDetail=getattr(exc, "code", "preflight_failed"))
                self._pause_request(tx, request, "preflight_failed")
            return
        with self.store.transaction() as tx:
            request = tx.get("requests", request["requestId"])
            if request["state"] != "queued":
                return
            self._transition(tx, request, "starting", "center", "dispatch_reserved", dispatchId=uid("dispatch"), nonce=uuid.uuid4().hex,
                             startAuthorized=False, launchIssued=False)
        try:
            control_dir = self._control(request)
            configuration = request["config"]
            environment = {"ENGINE": configuration["engine"], "MODEL": configuration["model"], "AUTONOMOUS_COMPANY_LANGUAGE": configuration["productLanguage"]}
            if configuration['engine'] != 'codex':
                environment['COMPANY_HARNESS_ENABLED'] = '0'
            if configuration["engine"] == "codex":
                environment["CODEX_REASONING_EFFORT"] = configuration["effort"]
            manifest = {key: request[key] for key in ("requestId", "dispatchId", "nonce", "runtimeId", "entryId", "sourceId")}
            manifest.update(centerId=self.store.center_id, root=self.adapter.path(source["root"]), controlDir=self.adapter.path(control_dir), environment=environment,
                            productId=source.get("productId"))
            atomic_json(control_dir / "manifest.json", manifest)
            self._write_controls()
            # Durable launch intent precedes Popen. A crash at this boundary is
            # ambiguous and must never produce a second dispatch automatically.
            with self.store.transaction() as tx:
                request = tx.get("requests", request["requestId"])
                if request.get("stopRequested"):
                    self._transition(tx, request, "ended", "center", "user_stop", terminalReason="user_stop")
                    return
                request["launchIssued"] = True
                tx.put("requests", request["requestId"], request)
            self._children[request["dispatchId"]] = self.adapter.launch(control_dir / "manifest.json")
        except Exception as exc:
            with self.store.transaction() as tx:
                current = tx.get("requests", request["requestId"])
                if current.get("launchIssued"):
                    self._transition(tx, current, "attention", "center", "dispatch_uncertain", attentionReason="dispatch_uncertain", reasonDetail=type(exc).__name__)
                else:
                    self._transition(tx, current, "failed", "center", "pre_start", terminalReason="pre_start", reasonDetail=type(exc).__name__)
                self._pause_request(tx, current, "dispatch_uncertain")

    def _reconcile(self, request):
        if not request.get("dispatchId"):
            if request["state"] == "attention" and request.get("attentionReason") == "preflight":
                with self.store.transaction() as tx:
                    current = tx.get("requests", request["requestId"])
                    self._transition(tx, current, "failed", "recovery", "pre_start", terminalReason="pre_start", reasonDetail=current.get("reasonDetail"))
            return
        path = self._control(request) / "manifest.json"
        try:
            probe = self.adapter.query("probe", center_id=self.store.center_id, manifest=path if path.exists() else None)
        except Exception:
            with self.store.transaction() as tx:
                current = tx.get("requests", request["requestId"])
                if current["state"] in OPEN and current["state"] != "attention":
                    self._transition(tx, current, "attention", "recovery", "runner_unavailable", attentionReason="recovery_required", reasonDetail="runner_unavailable")
                self._pause_request(tx, current, "runner_unavailable")
            return
        receipt = probe.get("receipt")
        with self.store.transaction() as tx:
            current = tx.get("requests", request["requestId"])
            if current["state"] in TERMINAL:
                if not probe["slotFree"] and probe.get("owner", {}).get("dispatchId") == current["dispatchId"]:
                    self._pause_request(tx, current, "terminal_owner_conflict")
                return
            if receipt and receipt.get("state") == "terminal" and receipt.get("cleanupConfirmed") and probe["slotFree"]:
                reason = receipt.get("reason")
                if reason in {"budget_pause", "governance_pause"}:
                    state, terminal = "ended", reason
                    self._pause_request(tx, current, reason)
                elif reason in {"user_stop", "center_shutdown"} or current.get("stopRequested"):
                    state, terminal = "ended", "user_stop"
                    if reason != "user_stop":
                        self._pause_request(tx, current, reason)
                elif reason == "natural" and receipt.get("launched"):
                    state, terminal = "ended", "natural"
                else:
                    state, terminal = "failed", "runtime" if receipt.get("launched") else "pre_start"
                    self._pause_request(tx, current, reason or "runtime_failed")
                self._transition(tx, current, state, "runner", reason, terminalReason=terminal, reasonDetail=reason, receipt=receipt)
                child = self._children.get(current["dispatchId"])
                if child is not None and child.poll() is not None:
                    self._children.pop(current["dispatchId"], None)
            elif receipt and probe.get("ownerAlive") and (probe.get("owner") or {}).get("dispatchId") == current["dispatchId"] and not probe["slotFree"]:
                current["liveConfirmedAt"] = now()
                observed_block = receipt.get("executionBlockedReason") if receipt.get("state") == "running" else None
                if observed_block == "unresolved_p1":
                    self._pause_request(tx, current, "unresolved_p1")
                blocked = observed_block if observed_block == "unresolved_p1" and not current.get("stopRequested") else None
                if current.get("executionBlockedReason") != blocked:
                    current.update(executionBlockedReason=blocked, executionBlockedAt=receipt.get("executionBlockedAt") if blocked else None)
                    self._event(tx, current, current["state"], "runner", blocked or "governance_observation_changed")
                tx.put("requests", current["requestId"], current)
                receipt_state = receipt.get("state")
                if receipt_state in {"accepted", "terminal"}:
                    return  # accepted is not a launched loop; terminal still owns cleanup lock
                state = "stopping" if current.get("stopRequested") or receipt_state == "stopping" else "running"
                if receipt_state == "attention":
                    state = "attention"
                    if current["state"] != state:
                        self._transition(tx, current, state, "runner", "stop_unconfirmed", attentionReason="stop_unconfirmed", reasonDetail=receipt.get("reason"))
                    self._pause_request(tx, current, "stop_unconfirmed")
                elif current["state"] != state:
                    self._transition(tx, current, state, "runner", receipt.get("reason"), startedAt=receipt.get("startedAt"), attentionReason=None)
                    if state == "stopping" and receipt.get("reason") in {"budget_pause", "governance_pause", "provider_pause"}:
                        self._pause_request(tx, current, receipt["reason"])
            elif not current.get("launchIssued") and probe["slotFree"]:
                self._transition(tx, current, "failed", "recovery", "pre_start", terminalReason="pre_start", reasonDetail="runner_not_issued")
            else:
                child = self._children.get(current["dispatchId"])
                if child is not None and child.poll() is None and current["state"] == "starting":
                    return  # launch bridge has not published its first receipt yet
                reason = "stop_unconfirmed" if current.get("stopRequested") else "dispatch_uncertain"
                if current["state"] != "attention":
                    self._transition(tx, current, "attention", "recovery", reason, attentionReason=reason)
                self._pause_request(tx, current, reason)
        if receipt and (time.monotonic() - self._last_refresh.get(request["sourceId"], 0) > 5 or receipt.get("state") == "terminal"):
            try:
                self._refresh_source(request["sourceId"])
                self._last_refresh[request["sourceId"]] = time.monotonic()
            except Exception:
                pass  # read projection failure cannot fabricate an execution outcome

    def tick(self):
        with self._mutex:
            for dispatch_id, child in list(self._children.items()):
                if child.poll() is not None:
                    self._children.pop(dispatch_id, None)
            self._write_controls()
            with self.store.transaction() as tx:
                requests = [row for row in tx.list("requests") if row["state"] in ACTIVE and row.get("dispatchId")]
            for request in requests:
                self._reconcile(request)
            if not self._closing.is_set() and self.adapter.available:
                self._dispatch()

    def _supervise(self):
        while not self._closing.is_set():
            try:
                self.tick()
            except Exception:
                # A failed DB write or heartbeat stops further dispatch; runner
                # independently detects lost control and performs cleanup.
                try:
                    with self.store.transaction() as tx:
                        self._pause(tx, "center_error")
                except Exception:
                    pass
            self._closing.wait(0.5)

    def _heartbeat(self):
        # WSL probes and catalog reads can take longer as concurrency increases.
        # They must not starve the independent liveness channel of healthy owners.
        while not self._closing.is_set():
            try:
                self._write_controls()
            except Exception:
                with self.store.transaction() as tx:
                    self._pause(tx, "center_error")
            self._closing.wait(1)
