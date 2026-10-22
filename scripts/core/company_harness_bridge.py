"""Attempt-bound Unix socket bridge. No host control methods cross this API."""
import argparse
from contextlib import contextmanager
import json
import math
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

    def dispatch(self, request):
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
            recovery = next((r for r in cycle["recoveries"] if attempt and r["recoveryId"] == attempt["recoveryId"]), None) if cycle else None
            timer = recovery["timer"] if recovery else cycle["budgetTimer"] if cycle else None
            if timer:
                consumed, reliability = self.store._elapsed(timer)
                status["remainingSeconds"] = max(0, math.floor(timer["limitSeconds"] - consumed)) if reliability == "reliable" else None
            status["recovery"] = bool(attempt and attempt["recoveryId"])
            status["cycle"] = {key: cycle.get(key) for key in ("cycleId", "contract", "objective", "workKind", "protocolState", "outcome", "time", "activeAttemptId", "report")} if cycle else None
            return status
        if action == "publish_progress":
            return self.client.publish_progress(request.get("id"), payload)
        if action == "submit":
            from company_harness_runner import validate_recovery_submission
            from company_harness_client import PROTOCOL_LIMIT
            from isolation_workspace import regular_bytes
            with self.store._transaction() as tx:
                cycle, attempt = self.store._context(tx, self.context, business=False)
            workspace = self.live_workspace()
            def protocol(ref):
                if workspace is None:
                    raise HarnessError("COLLECTION_UNCONFIRMED")
                candidate = safe_path(workspace, ref["path"])
                if candidate.stat().st_size > PROTOCOL_LIMIT:
                    raise HarnessError("PROTOCOL_MATERIAL_TOO_LARGE", "handoffRef")
                return regular_bytes(candidate, PROTOCOL_LIMIT + 1)
            validate_recovery_submission(attempt, payload, protocol)
            snapshot = self.capture_versions()
            receipt = self.client.submit(request.get("id"), payload)
            if receipt.get("status") == "accepted" and snapshot:
                proof_path = safe_path(self.store.root, ".autonomous-company/harness/" + self.context["attemptId"] + ".acceptance.json")
                if not proof_path.exists():
                    atomic_write(proof_path, {"submissionId": request.get("id"), "versions": snapshot})
            return receipt
        if action == "request_extension":
            if set(payload) != {"reason", "remainingSeconds"}:
                raise HarnessError("INVALID_REQUEST", "payload")
            return self.client.request_extension(request.get("id"), payload["reason"], payload["remainingSeconds"])
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
            return self.client.checkpoint(request.get("id"), payload)
        raise HarnessError("UNSUPPORTED_ACTION", "action")

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

    def capture_versions(self):
        from isolation_workspace import fingerprint, protocol_version
        workspace = self.live_workspace()
        if workspace is None:
            return None
        versions = {name: fingerprint(workspace / name) for name in ("projects", "docs", "memories")}
        cycle = self.store.snapshot()["cycles"]
        attempt = next(a for c in cycle for a in c["attempts"] if a["attemptId"] == self.context["attemptId"])
        if attempt["recoveryId"]:
            try:
                versions["protocol"] = protocol_version(workspace, self.context["attemptId"])
            except ValueError as error:
                raise HarnessError(str(error), "protocol")
        return versions


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(3)
        try:
            raw = self.rfile.readline(MAX_REQUEST + 1)
            if len(raw) > MAX_REQUEST or not raw.endswith(b"\n"):
                raise HarnessError("REQUEST_TOO_LARGE")
            if not self.server.dispatch_lock.acquire(timeout=3):
                raise HarnessError("REQUEST_BUSY")
            try:
                result = self.server.dispatch(json.loads(raw))
            finally:
                self.server.dispatch_lock.release()
        except HarnessError as error:
            result = {"status": "rejected", "errorCode": error.code, "field": error.field}
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
        Path(manifest["ready"]).write_text("ready\n")
        done.wait()


if __name__ == "__main__":
    main()
