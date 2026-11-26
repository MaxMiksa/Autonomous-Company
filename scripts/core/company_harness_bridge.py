"""Attempt-bound Unix socket bridge. No host control methods cross this API."""
import argparse
import base64
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import math
import mimetypes
import os
from pathlib import Path
import secrets
import signal
import socket
import socketserver
import threading

from company_harness import HarnessError, HarnessStore
from product_identity import atomic_write, safe_path

MAX_REQUEST = 64 * 1024


class Bridge(socketserver.ThreadingMixIn, getattr(socketserver, "UnixStreamServer", socketserver.TCPServer)):
    daemon_threads = True
    block_on_close = False

    def __init__(self, path, store, context, token):
        if not hasattr(socketserver, "UnixStreamServer") or not hasattr(socket, "AF_UNIX"):
            raise HarnessError("UNSUPPORTED_PLATFORM", detail="Harness bridge requires Linux/WSL Unix sockets")
        self.store, self.context, self.token = store, context, token
        self.dispatch_lock = threading.Lock()
        self.requests = threading.BoundedSemaphore(4)
        self.client = store.client(context)
        super().__init__(str(path), Handler)
        os.chmod(path, 0o600)

    def process_request(self, request, address):
        if not self.requests.acquire(blocking=False):
            self.shutdown_request(request)
            return
        super().process_request(request, address)

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.requests.release()

    def _time_status(self, cycle, attempt):
        if not cycle:
            return {"remainingSeconds": None, "timePhase": "unknown"}
        recovery = next((r for r in cycle["recoveries"] if attempt and r["recoveryId"] == attempt["recoveryId"]), None)
        timer = recovery["timer"] if recovery else cycle["budgetTimer"]
        if not timer:
            return {"remainingSeconds": None, "timePhase": "unknown"}
        consumed, reliability = self.store._elapsed(timer)
        if reliability != "reliable":
            return {"remainingSeconds": None, "timePhase": "unknown"}
        remaining = max(0, math.floor(timer["limitSeconds"] - consumed))
        target = (cycle.get("contract") or {}).get("targetSeconds")
        limit = timer.get("limitSeconds")
        if remaining <= 60:
            phase = "critical"
        elif remaining <= 120:
            phase = "wrap_up_now"
        elif isinstance(target, (int, float)) and isinstance(limit, (int, float)) and remaining <= max(120, limit - target):
            phase = "approaching_target"
        else:
            phase = "ok"
        return {"remainingSeconds": remaining, "timePhase": phase}

    def dispatch(self, request):
        from company_harness_quality import artifact_state
        if not isinstance(request, dict) or set(request) - {"token", "action", "id", "payload"}:
            raise HarnessError("INVALID_REQUEST")
        token = request.get("token")
        if not isinstance(token, str) or not secrets.compare_digest(token, self.token):
            raise HarnessError("UNAUTHORIZED")
        action, payload = request.get("action"), request.get("payload", {})
        if not isinstance(payload, dict):
            raise HarnessError("INVALID_REQUEST", "payload")
        if action == "status":
            # The bridge keeps the capability context server-side. A fenced
            # client may retrieve its own receipt/history but never another root.
            status = self.client.status()
            cycle = status["cycle"]
            attempt = next((a for a in cycle["attempts"] if a["attemptId"] == self.context["attemptId"]), None) if cycle else None
            status.update(self._time_status(cycle, attempt))
            status["recovery"] = bool(attempt and attempt["recoveryId"])
            status["attempt"] = {key: attempt.get(key) for key in
                ("attemptId", "status", "recoveryId", "acceptedSubmissionId")} if attempt else None
            try:
                with self.store._transaction() as tx:
                    self.store._context(tx, self.context)
                status["writeAllowed"] = True
            except HarnessError:
                status["writeAllowed"] = False
            if cycle:
                status["artifactHeads"] = artifact_state(
                    self.store,
                    {"productId": cycle.get("productId"), "explorationId": cycle.get("explorationId")},
                )
            status["cycle"] = {key: cycle.get(key) for key in ("cycleId", "contract", "objective", "workKind", "protocolState", "outcome", "time", "activeAttemptId", "report")} if cycle else None
            return status
        if action == "publish_progress":
            result = self.client.publish_progress(request.get("id"), payload)
            return self._with_timer(result)
        if action == "submit":
            from company_harness_quality import close_review, prepare_contract
            from company_harness_runner import evidence_path, validate_recovery_submission
            from company_harness_client import PROTOCOL_LIMIT, PROTOCOL_ROOT, protocol_handoff_path
            from isolation_workspace import regular_bytes
            with self.store._transaction() as tx:
                cycle, _ = self.store._context(tx, self.context, business=False)
            base_snapshot = self.store.snapshot()
            def capture(attempt):
                workspace = self.live_workspace()
                def protocol(ref):
                    if workspace is None:
                        raise HarnessError("COLLECTION_UNCONFIRMED")
                    candidate = safe_path(workspace, ref["path"])
                    if candidate.stat().st_size > PROTOCOL_LIMIT:
                        raise HarnessError("PROTOCOL_MATERIAL_TOO_LARGE", "handoffRef")
                    return regular_bytes(candidate, PROTOCOL_LIMIT + 1)
                validate_recovery_submission(attempt, payload, protocol)
                view = workspace or self.store.root
                receipt = {"attemptId": attempt["attemptId"], "docsRoot": str(view / "docs")}
                if attempt["recoveryId"]:
                    receipt["protocolRoot"] = str(view / Path(protocol_handoff_path(attempt["attemptId"])).parent)
                refs = payload.get("evidenceRefs", [])
                for ref in refs:
                    evidence_path(view, cycle, receipt, ref.get("path"))
                if payload.get("handoffRef") or (cycle.get("contract") or {}).get("workKind") == "review":
                    live_evidence = {}
                    for ref in refs:
                        path = evidence_path(view, cycle, receipt, ref.get("path"))
                        is_proto = str(ref.get("path", "")).startswith(PROTOCOL_ROOT + "/")
                        data = regular_bytes(path, PROTOCOL_LIMIT if is_proto else 1024 * 1024)
                        if hashlib.sha256(data).hexdigest() != ref.get("sha256"):
                            raise HarnessError("EVIDENCE_VERSION_MISMATCH", ref["evidenceId"])
                        try:
                            content, encoding = data.decode("utf-8"), None
                        except UnicodeDecodeError:
                            content, encoding = base64.b64encode(data).decode("ascii"), "base64"
                        entry = {
                            "evidenceId": ref["evidenceId"],
                            "cycleId": cycle["cycleId"],
                            "content": content,
                            "sha256": ref["sha256"],
                            "mediaType": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                            "source": {
                                "type": "isolated_collect",
                                "attemptId": attempt["attemptId"],
                                "workKind": cycle["workKind"],
                                "project": cycle["contract"].get("project"),
                                "path": ref["path"],
                            },
                        }
                        if encoding:
                            entry["contentEncoding"] = encoding
                        live_evidence[ref["evidenceId"]] = entry
                    overlay = _LiveOverlayStore(self.store, base_snapshot, live_evidence)
                    pending_sub = {"attemptId": attempt["attemptId"], "payload": deepcopy(payload)}
                    pending_cycle = {
                        **deepcopy(cycle),
                        "activeAttemptId": None,
                        "attempts": [{**deepcopy(item), "writersStopped": True} for item in cycle.get("attempts", [])],
                        "outcome": payload.get("result"),
                        "submissions": [*deepcopy(cycle.get("submissions", [])), pending_sub],
                    }
                    quality = close_review(overlay, pending_cycle, pending_sub)
                    handoff = payload.get("handoffRef")
                    if handoff and payload.get("result") in ("completed", "partial"):
                        if handoff not in refs:
                            raise HarnessError("HANDOFF_UNBOUND", "handoffRef")
                        try:
                            proposal = json.loads(overlay.read_evidence(handoff["evidenceId"])["content"])["nextContract"]
                        except (ValueError, KeyError, TypeError):
                            raise HarnessError("HANDOFF_INVALID", "nextContract")
                        prepare_contract(
                            overlay,
                            proposal,
                            {"productId": cycle.get("productId"), "explorationId": cycle.get("explorationId")},
                            pending_cycle=pending_cycle,
                            pending_quality=quality,
                        )
                return self.capture_versions(attempt, workspace)
            return self.store.submit_with_versions(self.context, request.get("id"), payload, capture)
        if action == "request_extension":
            if set(payload) != {"reason", "remainingSeconds"}:
                raise HarnessError("INVALID_REQUEST", "payload")
            result = self.client.request_extension(request.get("id"), payload["reason"], payload["remainingSeconds"])
            return self._with_timer(result)
        if action == "checkpoint":
            materials = payload.pop("materials", [])
            if not isinstance(materials, list) or len(materials) > 8:
                raise HarnessError("INVALID_REQUEST", "materials")
            # Bytes are untrusted worker-authored material, never host paths.
            # Validate current ownership before persisting this historical input.
            with self.store._transaction() as tx:
                self.store._context(tx, self.context)
            for material in materials:
                if not isinstance(material, dict) or set(material) != {"evidenceId", "content"}:
                    raise HarnessError("INVALID_REQUEST", "materials")
                self.store.bind_evidence(self.context["cycleId"], material["evidenceId"], material["content"],
                    source={"type": "worker_checkpoint", "attemptId": self.context["attemptId"]})
            result = self.client.checkpoint(request.get("id"), payload)
            return self._with_timer(result)
        raise HarnessError("UNSUPPORTED_ACTION", "action")

    def _with_timer(self, result):
        try:
            cycle = self.client.status().get("cycle")
            attempt = next((a for a in cycle["attempts"] if a["attemptId"] == self.context["attemptId"]), None) if cycle else None
            return {**result, **self._time_status(cycle, attempt)}
        except Exception:
            return result

    def live_workspace(self):
        """Host observes the live private view; model paths never select a root."""
        from isolation_workspace import regular_bytes
        from product_identity import read_state
        state = read_state(self.store.root)
        cycle = state["cycles"].get(self.context["cycleId"])
        if not cycle:
            return None
        active = safe_path(self.store.root, ".autonomous-company/isolation/" + cycle["identityId"] + "/active-run.json")
        if not active.exists():
            return None
        record = json.loads(regular_bytes(active))
        if record.get("cycle") != self.context["cycleId"] or record.get("attemptId") != self.context["attemptId"]:
            raise HarnessError("OWNER_MISMATCH", "isolatedView")
        pid = record.get("pid")
        current = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
        if current != record.get("processStart"):
            raise HarnessError("OWNER_MISMATCH", "isolatedView")
        return Path(record["view"]) / "workspace"

    def capture_versions(self, attempt, workspace):
        from isolation_workspace import fingerprint, protocol_version
        if workspace is None:
            return None
        versions = {name: fingerprint(workspace / name) for name in ("projects", "docs", "memories")}
        if attempt["recoveryId"]:
            try:
                versions["protocol"] = protocol_version(workspace, self.context["attemptId"])
            except ValueError as error:
                code, _, detail = str(error).partition(": ")
                raise HarnessError(code, "protocol", detail or None)
        return versions


class _LiveOverlayStore:
    def __init__(self, store, snap, live_evidence):
        self._store = store
        self._snapshot = snap
        self._live_evidence = live_evidence

    def snapshot(self):
        return self._snapshot

    def read_evidence(self, evidence_id):
        if evidence_id in self._live_evidence:
            return self._live_evidence[evidence_id]
        return self._store.read_evidence(evidence_id)

    def __getattr__(self, name):
        return getattr(self._store, name)


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(30)
        try:
            raw = self.rfile.readline(MAX_REQUEST + 1)
            if len(raw) > MAX_REQUEST or not raw.endswith(b"\n"):
                raise HarnessError("REQUEST_TOO_LARGE")
            if not self.server.dispatch_lock.acquire(timeout=30):
                raise HarnessError("REQUEST_BUSY")
            try:
                result = self.server.dispatch(json.loads(raw))
            finally:
                self.server.dispatch_lock.release()
        except HarnessError as error:
            result = {"status": "rejected", "errorCode": error.code, "field": error.field}
            if getattr(error, "detail", None):
                result["detail"] = error.detail
        except (ValueError, TypeError, OSError, RecursionError):
            result = {"status": "rejected", "errorCode": "INVALID_REQUEST"}
        try:
            self.wfile.write((json.dumps(result, ensure_ascii=False) + "\n").encode())
        except OSError:
            pass  # Lost ACK is recovered by the same message ID.


@contextmanager
def running_bridge(path, store, context, token):
    server = Bridge(path, store, context, token)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=4)
        Path(path).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    done = threading.Event()
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda *_: done.set())
    with running_bridge(manifest["socket"], HarnessStore(args.root, create=True), manifest["context"], manifest["token"]):
        atomic_write(Path(manifest['ready']), {'pid': os.getpid(), 'loopPid': os.getppid(),
            'processStart': Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
            'attemptId': manifest['context']['attemptId']})
        done.wait()


if __name__ == "__main__":
    main()
