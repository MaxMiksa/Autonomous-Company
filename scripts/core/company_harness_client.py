"""Read-only worker tool for the five attempt-scoped Company Harness actions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
from company_harness_contract import MATERIAL_LIMIT

LIMIT = 64 * 1024
PROTOCOL_LIMIT = 16 * 1024
PROTOCOL_ROOT = ".company-harness-protocol"


def protocol_handoff_path(attempt_id):
    return f"{PROTOCOL_ROOT}/{attempt_id}/handoff.json"


def validate_protocol_handoff(data):
    if len(data) > PROTOCOL_LIMIT:
        raise ValueError("PROTOCOL_MATERIAL_TOO_LARGE")
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError):
        raise ValueError("PROTOCOL_PURPOSE")
    allowed = {"objective", "workKind", "timeClass", "scope", "inputRefs", "prerequisiteRefs",
               "completionOrHandoff", "reviewRequirement", "revisesKind"}
    if (not isinstance(value, dict) or set(value) != {"nextContract"} or
            not isinstance(value["nextContract"], dict) or set(value["nextContract"]) - allowed):
        raise ValueError("PROTOCOL_PURPOSE")
    return value


def request(action, message_id=None, payload=None, *, socket_path=None, token=None):
    raw = (json.dumps({"token": token or os.environ["COMPANY_HARNESS_TOKEN"], "action": action,
                       "id": message_id, "payload": payload or {}}, ensure_ascii=False) + "\n").encode()
    if len(raw) > LIMIT:
        raise ValueError("Request exceeds 64 KiB")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(35)
        connection.connect(str(socket_path or os.environ["COMPANY_HARNESS_SOCKET"]))
        connection.sendall(raw)
        with connection.makefile("rb") as source:
            response = source.readline(2 * 1024 * 1024 + 1)
    return json.loads(response)


def material(path, checkpoint=False):
    root = Path(os.environ.get("AUTONOMOUS_COMPANY_ROOT", "/workspace")).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    relative = candidate.resolve(strict=True).relative_to(root).as_posix()
    data = candidate.read_bytes()
    if len(data) > MATERIAL_LIMIT:
        raise ValueError("Key material exceeds 1 MiB")
    digest = hashlib.sha256(data).hexdigest()
    ref = {"evidenceId": ("checkpoint-" if checkpoint else "evidence-") + os.environ["AUTONOMOUS_COMPANY_ATTEMPT_ID"] + "-" + digest,
           "sha256": digest, "path": relative}
    return ref, {"evidenceId": ref["evidenceId"], "content": data.decode("utf-8")} if checkpoint else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "publish_progress", "checkpoint", "request_extension", "submit"))
    parser.add_argument("--id")
    parser.add_argument("--payload", type=Path, help="JSON object containing the action payload")
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--handoff", help="JSON evidence containing the proposed nextContract")
    parser.add_argument("--primary", help="Primary result path or evidence ID when multiple results are submitted")
    parser.add_argument("--result", choices=("completed", "partial", "blocked", "failed"))
    args = parser.parse_args()
    payload = json.loads(args.payload.read_text()) if args.payload else {}
    if args.result:
        payload.update(result=args.result, unfinishedItems=payload.get("unfinishedItems", []))
    refs, materials = [], []
    for name in args.evidence + ([args.handoff] if args.handoff else []):
        ref, content = material(name, args.action == "checkpoint")
        refs.append(ref)
        if content:
            materials.append(content)
        if name == args.handoff:
            payload["handoffRef"] = ref
    if refs:
        payload["evidenceRefs"] = refs
        non_handoff = [ref for ref in refs if ref != payload.get("handoffRef")]
        if args.primary:
            payload["primaryEvidenceId"] = next((ref["evidenceId"] for ref in refs if ref["path"] == args.primary), args.primary)
        elif len(non_handoff) == 1:
            payload["primaryEvidenceId"] = non_handoff[0]["evidenceId"]
        elif len(refs) == 1:
            payload["primaryEvidenceId"] = refs[0]["evidenceId"]
        elif args.action == "submit" and not payload.get("primaryEvidenceId"):
            raise ValueError("Select one --primary result among the submitted materials")
    if materials:
        payload["materials"] = materials
    result = request(args.action, args.id, payload)
    rem = result.get("remainingSeconds")
    if isinstance(rem, int) and rem <= 120:
        phase = result.get("timePhase", "wrap_up_now")
        print(f"[harness-timer] WARNING: only {rem}s remaining ({phase}); finish handoff and submit now.", file=sys.stderr)
    print(json.dumps(result, ensure_ascii=False))
    return 2 if result.get("status") == "rejected" else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, OSError, ValueError) as error:
        print(json.dumps({"status": "rejected", "errorCode": "CLIENT_ERROR", "detail": str(error)}))
        sys.exit(2)
