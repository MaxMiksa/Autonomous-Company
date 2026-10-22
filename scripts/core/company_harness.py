"""Trusted runtime protocol store; never copy this database into worker views.

Only the host receives HarnessStore. A bridge binds an AttemptClient to its
authenticated attempt context and exposes that client's five model actions.
This module records protocol facts, not process supervision or semantic review.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time
import uuid

from namespace_guard import check_root
from product_identity import safe_path
from cycle_reports import FIELDS as REPORT_FIELDS, PHASES

PROCESS_BOOT = uuid.uuid4().hex
RESULTS = {"completed", "partial", "blocked", "failed", "interrupted", "not_started", "unknown"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _boot():
    path = Path("/proc/sys/kernel/random/boot_id")
    # Platforms without a verifiable boot ID conservatively invalidate anchors
    # on a controller-process restart. The host may inject its verified boot ID.
    return path.read_text().strip() if path.is_file() else PROCESS_BOOT


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _id(value, field):
    if not isinstance(value, str) or not value or len(value) > 256:
        raise HarnessError("INVALID_FIELD", field)
    return value


class HarnessError(ValueError):
    def __init__(self, code, field="", detail=""):
        self.code, self.field, self.detail = code, field, detail
        super().__init__(": ".join(part for part in (code, field, detail) if part))


class _Transaction:
    def __init__(self, connection):
        self.connection, self.changed = connection, False

    def get(self, kind, key):
        row = self.connection.execute("SELECT payload FROM records WHERE kind=? AND id=?", (kind, key)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, kind, key, value):
        payload = _json(value)
        old = self.connection.execute("SELECT payload FROM records WHERE kind=? AND id=?", (kind, key)).fetchone()
        if not old or old[0] != payload:
            if old:
                self.connection.execute("UPDATE records SET payload=? WHERE kind=? AND id=?", (payload, kind, key))
            else:
                self.connection.execute("INSERT INTO records VALUES(?,?,?)", (kind, key, payload))
            self.changed = True


class HarnessStore:
    def __init__(self, root, create=False, *, clock=time.monotonic, boot_id=None, utc_now=_now):
        self.root = Path(root).resolve()
        self.writable, self.clock, self.utc_now = create, clock, utc_now
        self.boot_id = boot_id or _boot()
        check_root(self.root)
        self.path = safe_path(self.root, ".autonomous-company/company-harness.sqlite3")
        if create:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = self._connect(write=True, create=True)
            try:
                connection.execute("CREATE TABLE IF NOT EXISTS records(kind TEXT, id TEXT, payload TEXT NOT NULL, PRIMARY KEY(kind,id))")
                connection.execute("INSERT OR IGNORE INTO records VALUES('meta','state',?)", (_json({
                    "projectionEpoch": uuid.uuid4().hex, "snapshotRevision": 0,
                    "generation": uuid.uuid4().hex, "currentCycleId": None}),))
                connection.commit()
            finally:
                connection.close()

    def _connect(self, write=False, create=False):
        check_root(self.root)
        safe_path(self.root, ".autonomous-company/company-harness.sqlite3")
        mode = "rwc" if create else ("rw" if write else "ro")
        connection = sqlite3.connect(self.path.as_uri() + "?mode=" + mode, uri=True, timeout=10)
        if write:
            connection.execute("PRAGMA synchronous=FULL")
        return connection

    @contextmanager
    def _transaction(self):
        if not self.writable:
            raise HarnessError("READ_ONLY")
        connection = self._connect(write=True)
        try:
            connection.execute("BEGIN IMMEDIATE")
            tx = _Transaction(connection)
            yield tx
            if tx.changed:
                meta = tx.get("meta", "state")
                meta["snapshotRevision"] += 1
                tx.put("meta", "state", meta)
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _cycle(self, tx, cycle_id):
        cycle = tx.get("cycle", cycle_id)
        if cycle is None:
            raise HarnessError("UNKNOWN_CYCLE", "cycleId")
        return cycle

    def _open(self, cycle):
        if cycle["protocolState"] == "closed":
            raise HarnessError("CYCLE_CLOSED", "cycleId")

    def _elapsed(self, timer):
        spent = timer["consumedSeconds"]
        if timer.get("anchor") is None:
            return spent, timer.get("reliability", "reliable")
        if timer["bootId"] != self.boot_id or self.clock() < timer["anchor"]:
            return spent, "unknown"
        return spent + self.clock() - timer["anchor"], timer.get("reliability", "reliable")

    def _settle(self, timer, stop=False):
        active = timer.get("anchor") is not None
        spent, reliability = self._elapsed(timer)
        timer.update(consumedSeconds=spent, reliability=reliability)
        timer["anchor"] = None if stop or not active or reliability == "unknown" else self.clock()
        timer["bootId"] = self.boot_id

    def _timer(self, limit=None):
        return {"consumedSeconds": 0, "anchor": self.clock(), "bootId": self.boot_id,
                "reliability": "reliable", "limitSeconds": limit}

    def _save_cycle(self, tx, cycle):
        # Every existing cycle persistence boundary preserves all known elapsed
        # lower bounds, including recovery/total across an unverifiable reboot.
        for key in ("executionTimer", "budgetTimer", "totalTimer"):
            if cycle.get(key):
                self._settle(cycle[key])
        for recovery in cycle["recoveries"]:
            self._settle(recovery["timer"])
        tx.put("cycle", cycle["cycleId"], cycle)
        compact = json.loads(_json(cycle))
        for attempt in compact["attempts"]:
            attempt["usage"] = self._usage(attempt)
            attempt["report"] = attempt["reports"][-1] if attempt["reports"] else {"status": "missing"}
            attempt.pop("reports", None)
            attempt.pop("calls", None)
            attempt.pop("events", None)
            attempt.pop("context", None)
            attempt.pop("ownership", None)
            attempt.pop("checkpoints", None)
            attempt.pop("extensions", None)
        compact["usage"] = self._cycle_usage(compact)
        submission_id = ((cycle.get("closeReceipt") or {}).get("input") or {}).get("submissionId")
        submission = next((row for row in cycle["submissions"] if row["submissionId"] == submission_id), None)
        if submission:
            refs = submission["payload"].get("evidenceRefs", [])
            compact["primaryEvidenceId"] = submission["payload"].get("primaryEvidenceId") or (refs[0]["evidenceId"] if len(refs) == 1 else None)
        compact.pop("submissions", None)
        compact.pop("checkpoints", None)
        tx.put("cycle_index", cycle["cycleId"], compact)
        catalog = {key: value for key, value in compact.items() if key not in
                   {"attempts", "usage", "contract", "closeReceipt", "primaryEvidenceId"}}
        catalog["contract"] = {key: compact["contract"].get(key) for key in ("project", "capabilities", "runCycleNumber")}
        catalog["attempts"] = [{key: attempt.get(key) for key in
            ("attemptId", "status", "recoveryId", "writersStopped", "startedAt", "endedAt")}
            for attempt in compact["attempts"]]
        tx.put("cycle_catalog", cycle["cycleId"], catalog)

    def _budget(self, cycle, recovery=None):
        timer = recovery["timer"] if recovery else cycle["budgetTimer"]
        spent, reliability = self._elapsed(timer)
        if reliability != "reliable":
            raise HarnessError("TIME_UNCONFIRMED", "bootId")
        if spent >= timer["limitSeconds"]:
            raise HarnessError("BUDGET_EXHAUSTED", "time")

    def _context(self, tx, context, *, business=True):
        cycle = self._cycle(tx, context.get("cycleId"))
        self._open(cycle)
        attempt = next((a for a in cycle["attempts"] if a["attemptId"] == context.get("attemptId")), None)
        if not attempt or attempt["context"] != context:
            raise HarnessError("OWNER_MISMATCH", "context")
        if context["generation"] != tx.get("meta", "state")["generation"]:
            raise HarnessError("STALE_GENERATION", "generation")
        if cycle["activeAttemptId"] != attempt["attemptId"] or attempt["status"] != "running":
            raise HarnessError("STALE_ATTEMPT", "attemptId")
        if business and attempt.get("acceptedSubmissionId"):
            raise HarnessError("SUBMISSION_ALREADY_ACCEPTED", "submissionId")
        recovery = next((r for r in cycle["recoveries"] if r["recoveryId"] == attempt["recoveryId"]), None)
        if business:
            self._budget(cycle, recovery)
        return cycle, attempt

    def _replay(self, tx, context, action, key, payload):
        key = _id(key, action + "Id")
        receipt_id = _json([context.get("attemptId"), action, key])
        previous = tx.get("message", receipt_id)
        digest = hashlib.sha256(_json({"context": context, "payload": payload}).encode()).hexdigest()
        if previous and previous["digest"] != digest:
            raise HarnessError("ID_CONFLICT", action + "Id")
        return receipt_id, digest, previous

    def claim_controller(self, generation):
        """Host fencing only; does not authorize replay, takeover or dispatch."""
        _id(generation, "generation")
        with self._transaction() as tx:
            meta = tx.get("meta", "state")
            meta["generation"] = generation
            tx.put("meta", "state", meta)
        return generation

    def create_cycle(self, contract):
        """Identity and numbering must already have been reserved by the host."""
        for field in ("cycleId", "objective", "workKind"):
            _id(contract.get(field), field)
        if not (contract.get("productId") or contract.get("explorationId")):
            raise HarnessError("INVALID_FIELD", "productId/explorationId")
        if type(contract.get("sequenceNumber")) is not int or contract["sequenceNumber"] < 1:
            raise HarnessError("INVALID_FIELD", "sequenceNumber")
        if contract.get("timeClass", "regular") not in {"regular", "development"}:
            raise HarnessError("INVALID_FIELD", "timeClass")
        with self._transaction() as tx:
            existing = tx.get("cycle", contract["cycleId"])
            if existing:
                if existing["contract"] != contract:
                    raise HarnessError("ID_CONFLICT", "cycleId")
                return existing
            meta = tx.get("meta", "state")
            if meta["currentCycleId"]:
                prior = self._cycle(tx, meta["currentCycleId"])
                if prior["protocolState"] != "closed":
                    raise HarnessError("UNFINISHED_CYCLE", "currentCycleId")
            limit = 720 if contract.get("timeClass") == "development" else 480
            timer = self._timer(limit)
            timer["anchor"] = None
            cycle = {"contract": contract, "cycleId": contract["cycleId"],
                "productId": contract.get("productId"), "explorationId": contract.get("explorationId"),
                "sequenceNumber": contract["sequenceNumber"], "objective": contract["objective"],
                "workKind": contract["workKind"], "timeClass": contract.get("timeClass", "regular"),
                "createdAt": self.utc_now(), "startedAt": None, "endedAt": None, "deadline": None,
                "executionTimer": timer, "budgetTimer": dict(timer), "totalTimer": None, "protocolState": "allocated", "outcome": None,
                "activeAttemptId": None, "attempts": [], "recoveries": [], "submissions": [],
                "qualityApplicability": [], "continuationDecision": {"allowed": False, "reason": "not_evaluated"},
                "closeReceipt": None}
            meta["currentCycleId"] = cycle["cycleId"]
            self._save_cycle(tx, cycle)
            tx.put("meta", "state", meta)
            return cycle

    def begin_attempt(self, cycle_id, attempt_id, ownership, *, recovery_id=None, log_refs=None):
        _id(attempt_id, "attemptId")
        if not isinstance(ownership, dict) or not ownership:
            raise HarnessError("INVALID_FIELD", "ownership")
        with self._transaction() as tx:
            cycle = self._cycle(tx, cycle_id)
            self._open(cycle)
            generation = tx.get("meta", "state")["generation"]
            context = {"cycleId": cycle_id, "attemptId": attempt_id, "generation": generation, "ownership": ownership}
            index = tx.get("attempt", attempt_id)
            if index:
                previous = next((a for a in cycle["attempts"] if a["attemptId"] == attempt_id), None)
                if previous and previous["context"] == context and previous["recoveryId"] == recovery_id and previous["logRefs"] == (log_refs or []):
                    return previous
                raise HarnessError("ID_CONFLICT", "attemptId")
            if cycle["activeAttemptId"]:
                raise HarnessError("WRITERS_UNCONFIRMED", "activeAttemptId")
            recovery = next((r for r in cycle["recoveries"] if r["recoveryId"] == recovery_id), None)
            if recovery_id and (not recovery or recovery["status"] != "running"):
                raise HarnessError("UNKNOWN_RECOVERY", "recoveryId")
            if not recovery_id and cycle["recoveries"]:
                raise HarnessError("RECOVERY_ONLY", "recoveryId")
            if cycle["startedAt"] is None:
                cycle["startedAt"] = self.utc_now()
                cycle["deadline"] = (datetime.fromisoformat(cycle["startedAt"]) + timedelta(seconds=cycle["executionTimer"]["limitSeconds"])).isoformat()
                cycle["executionTimer"] = self._timer(cycle["executionTimer"]["limitSeconds"])
                cycle["budgetTimer"] = self._timer(cycle["budgetTimer"]["limitSeconds"])
                cycle["totalTimer"] = self._timer()
            self._budget(cycle, recovery)
            self._settle(recovery["timer"] if recovery else cycle["budgetTimer"])
            if not recovery:
                cycle["executionTimer"]["anchor"] = self.clock()
            attempt = {"attemptId": attempt_id, "cycleId": cycle_id, "generation": generation,
                "ownership": ownership, "context": context, "recoveryId": recovery_id, "status": "running",
                "startedAt": self.utc_now(), "endedAt": None, "actualResult": None, "writersStopped": False,
                "logRefs": log_refs or [], "reports": [], "checkpoints": [], "events": [], "calls": [],
                "extensions": [], "acceptedSubmissionId": None}
            cycle["attempts"].append(attempt)
            cycle.update(activeAttemptId=attempt_id, protocolState="recovering" if recovery else "executing")
            tx.put("attempt", attempt_id, {"cycleId": cycle_id, "generation": generation, "ownership": ownership})
            self._save_cycle(tx, cycle)
            return attempt

    def _model_message(self, context, action, message_id, payload, *, capture_acceptance=None):
        with self._transaction() as tx:
            receipt_id, digest, previous = self._replay(tx, context, action, message_id, payload)
            if previous:
                return previous["receipt"]
            try:
                cycle, attempt = self._context(tx, context)
                if action == "progress":
                    if set(payload) - {"reportRevision", "title", "summary", "reportedPhase", "blocker"}:
                        raise HarnessError("UNKNOWN_FIELD", "report")
                    revision = payload.get("reportRevision")
                    if type(revision) is not int or revision < 1 or (attempt["reports"] and revision <= attempt["reports"][-1]["reportRevision"]):
                        raise HarnessError("STALE_REPORT", "reportRevision")
                    for field, maximum in REPORT_FIELDS.items():
                        value = payload.get(field, "" if field == "blocker" else None)
                        if not isinstance(value, str) or len(value) > maximum or value != value.strip() or any(ord(char) < 32 for char in value):
                            raise HarnessError("INVALID_FIELD", field)
                    if not payload["title"] or not payload["summary"] or payload.get("reportedPhase") not in PHASES:
                        raise HarnessError("INVALID_FIELD", "reportedPhase/title/summary")
                    if (payload["reportedPhase"] == "blocked") != bool(payload.get("blocker")):
                        raise HarnessError("INVALID_FIELD", "blocker")
                    report = {**payload, "reporterAttemptId": attempt["attemptId"], "reportedAt": self.utc_now(), "source": "model"}
                    attempt["reports"].append(report)
                elif action == "checkpoint":
                    self._verify_refs(tx, cycle, payload.get("evidenceRefs", []))
                    if not payload.get("evidenceRefs"):
                        raise HarnessError("EVIDENCE_MISSING", "evidenceRefs")
                    attempt["checkpoints"].append({**payload, "checkpointId": message_id, "recordedAt": self.utc_now()})
                elif action == "extension":
                    _id(payload.get("reason"), "reason")
                    remaining = payload.get("remainingSeconds")
                    if not isinstance(remaining, (float, int)) or isinstance(remaining, bool) or not math.isfinite(remaining) or remaining < 0:
                        raise HarnessError("INVALID_FIELD", "remainingSeconds")
                    attempt["extensions"].append({**payload, "requestedAt": self.utc_now()})
                elif action == "submit":
                    if any(s["submissionId"] == message_id for s in cycle["submissions"]):
                        raise HarnessError("ID_CONFLICT", "submissionId")
                    if payload.get("result") not in RESULTS - {"interrupted", "not_started", "unknown"}:
                        raise HarnessError("INVALID_FIELD", "result")
                    if not isinstance(payload.get("unfinishedItems"), list):
                        raise HarnessError("INVALID_FIELD", "unfinishedItems")
                    # Worker material may only become visible after collect.
                    # Reception acknowledges its requested immutable version;
                    # final closure requires that exact readable binding.
                    self._verify_refs(tx, cycle, payload.get("evidenceRefs", []), allow_pending=True)
                    if payload["result"] in {"completed", "partial"} and not payload.get("evidenceRefs"):
                        raise HarnessError("EVIDENCE_MISSING", "evidenceRefs")
                    # The host baseline and accepted receipt commit together.
                    # Replays return above before observing the workspace again.
                    acceptance = capture_acceptance(attempt) if capture_acceptance is not None else None
                    attempt["acceptedSubmissionId"] = message_id
                    cycle["submissions"].append({"submissionId": message_id, "attemptId": attempt["attemptId"], "payload": payload,
                        "acceptedAt": self.utc_now(), "acceptanceVersions": acceptance})
                    cycle["protocolState"] = "submitted"
                else:
                    raise HarnessError("UNKNOWN_ACTION")
                self._settle(cycle["executionTimer"])
                self._settle(cycle["budgetTimer"])
                self._save_cycle(tx, cycle)
                receipt = {"status": "accepted", "action": action, "messageId": message_id,
                           "cycleId": cycle["cycleId"], "attemptId": attempt["attemptId"], "receivedAt": self.utc_now()}
            except HarnessError as error:
                receipt = {"status": "rejected", "action": action, "messageId": message_id,
                    "errorCode": error.code, "field": error.field, "receivedAt": self.utc_now()}
            tx.put("message", receipt_id, {"digest": digest, "receipt": receipt})
            return receipt

    def publish_progress(self, context, message_id, report):
        return self._model_message(context, "progress", message_id, report)

    def checkpoint(self, context, checkpoint_id, payload):
        return self._model_message(context, "checkpoint", checkpoint_id, payload)

    def request_extension(self, context, request_id, reason, remaining_seconds):
        return self._model_message(context, "extension", request_id, {"reason": reason, "remainingSeconds": remaining_seconds})

    def submit(self, context, submission_id, payload):
        return self._model_message(context, "submit", submission_id, payload)

    def submit_with_versions(self, context, submission_id, payload, capture_versions):
        """Host-only reception; capture runs once inside the acceptance transaction."""
        return self._model_message(context, "submit", submission_id, payload, capture_acceptance=capture_versions)

    def bind_evidence(self, cycle_id, evidence_id, content, *, media_type="text/plain", source=None):
        """Host collector supplies readable immutable key material, never a path hash."""
        _id(evidence_id, "evidenceId")
        if not isinstance(content, (str, bytes)):
            raise HarnessError("INVALID_FIELD", "content")
        data = content.encode("utf-8") if isinstance(content, str) else content
        if len(data) > 1048576:
            raise HarnessError("INVALID_FIELD", "content")
        with self._transaction() as tx:
            self._open(self._cycle(tx, cycle_id))
            evidence = {"evidenceId": evidence_id, "cycleId": cycle_id,
                "content": content if isinstance(content, str) else base64.b64encode(content).decode("ascii"),
                "sha256": hashlib.sha256(data).hexdigest(), "mediaType": media_type, "source": source}
            if isinstance(content, bytes):
                evidence["contentEncoding"] = "base64"
            previous = tx.get("evidence", evidence_id)
            if previous and previous != evidence:
                raise HarnessError("ID_CONFLICT", "evidenceId")
            tx.put("evidence", evidence_id, evidence)
            return {key: value for key, value in evidence.items() if key != "content"}

    def _verify_refs(self, tx, cycle, refs, allow_pending=False):
        if not isinstance(refs, list):
            raise HarnessError("INVALID_FIELD", "evidenceRefs")
        for ref in refs:
            if not isinstance(ref, dict) or not ref.get("evidenceId") or not ref.get("sha256"):
                raise HarnessError("INVALID_FIELD", "evidenceRefs")
            evidence = tx.get("evidence", ref["evidenceId"])
            if not evidence and allow_pending:
                continue
            if not evidence or evidence["cycleId"] != cycle["cycleId"]:
                raise HarnessError("EVIDENCE_MISSING", ref["evidenceId"])
            if evidence["sha256"] != ref["sha256"]:
                raise HarnessError("EVIDENCE_VERSION_MISMATCH", ref["evidenceId"])

    def finish_attempt(self, context, actual_result, *, writers_stopped, observation):
        """Host supervisor must authenticate the execution tree, not just its PID."""
        if writers_stopped is not True or not observation:
            raise HarnessError("WRITERS_UNCONFIRMED", "writersStopped")
        if not isinstance(actual_result, dict) or actual_result.get("outcome") not in RESULTS:
            raise HarnessError("INVALID_FIELD", "actualResult")
        with self._transaction() as tx:
            cycle = self._cycle(tx, context.get("cycleId"))
            attempt = next((a for a in cycle["attempts"] if a["context"] == context), None)
            if not attempt:
                raise HarnessError("OWNER_MISMATCH", "context")
            final = {"actualResult": actual_result, "writerObservation": observation}
            if attempt["status"] == "finished":
                if any(attempt.get(key) != value for key, value in final.items()):
                    raise HarnessError("ID_CONFLICT", "actualResult")
                return attempt
            self._open(cycle)
            # This is an explicit host reconciliation fact; model callbacks never
            # receive this method, including after controller-generation changes.
            attempt.update(final, status="finished", writersStopped=True, endedAt=self.utc_now())
            cycle["activeAttemptId"] = None
            cycle["protocolState"] = "validating" if attempt["acceptedSubmissionId"] else "awaiting_recovery"
            self._settle(cycle["executionTimer"], stop=True)
            self._settle(cycle["budgetTimer"])
            if attempt["recoveryId"]:
                recovery = next(r for r in cycle["recoveries"] if r["recoveryId"] == attempt["recoveryId"])
                self._settle(recovery["timer"])
            self._save_cycle(tx, cycle)
            return attempt

    def begin_recovery(self, cycle_id, recovery_id, *, budget_seconds, reason):
        _id(recovery_id, "recoveryId")
        if not isinstance(budget_seconds, (int, float)) or isinstance(budget_seconds, bool) or not math.isfinite(budget_seconds) or budget_seconds <= 0:
            raise HarnessError("INVALID_FIELD", "budgetSeconds")
        with self._transaction() as tx:
            cycle = self._cycle(tx, cycle_id)
            self._open(cycle)
            prior = tx.get("recovery", recovery_id)
            if prior:
                match = next((r for r in cycle["recoveries"] if r["recoveryId"] == recovery_id), None)
                if match and match["budgetSeconds"] == budget_seconds and match["reason"] == reason:
                    return match
                raise HarnessError("ID_CONFLICT", "recoveryId")
            if cycle["activeAttemptId"]:
                raise HarnessError("WRITERS_UNCONFIRMED", "activeAttemptId")
            if cycle["recoveries"]:
                raise HarnessError("RECOVERY_ALREADY_ALLOCATED", "recoveryId", "No budget reset by creating another recovery")
            self._settle(cycle["executionTimer"], stop=True)
            self._settle(cycle["budgetTimer"], stop=True)
            if cycle["totalTimer"] is None:
                cycle["startedAt"] = self.utc_now()
                cycle["totalTimer"] = self._timer()
            recovery = {"recoveryId": recovery_id, "cycleId": cycle_id, "budgetSeconds": budget_seconds,
                "reason": reason, "startedAt": self.utc_now(), "endedAt": None,
                "status": "running", "timer": self._timer(budget_seconds)}
            cycle["recoveries"].append(recovery)
            cycle["protocolState"] = "recovering"
            tx.put("recovery", recovery_id, {"cycleId": cycle_id})
            self._save_cycle(tx, cycle)
            return recovery

    def record_event(self, context, sequence, event):
        if type(sequence) is not int or sequence < 1:
            raise HarnessError("INVALID_FIELD", "sequence")
        with self._transaction() as tx:
            cycle, attempt = self._context(tx, context, business=False)
            existing = next((e for e in attempt["events"] if e["sequence"] == sequence), None)
            if existing:
                if existing["event"] != event:
                    raise HarnessError("ID_CONFLICT", "sequence")
                return existing
            row = {"sequence": sequence, "event": event, "observedAt": self.utc_now()}
            attempt["events"].append(row)
            attempt["events"].sort(key=lambda e: e["sequence"])
            self._save_cycle(tx, cycle)
            return row

    def record_usage(self, cycle_id, attempt_id, call):
        """Host metering can append late historical calls, never relabel closure."""
        _id(call.get("callId"), "callId")
        if call.get("coverage") not in {"self", "subtree", "unknown"}:
            raise HarnessError("INVALID_FIELD", "coverage")
        for field in ("cost", "inputTokens", "outputTokens"):
            value = call.get(field)
            if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0):
                raise HarnessError("INVALID_FIELD", field)
        with self._transaction() as tx:
            cycle = self._cycle(tx, cycle_id)
            attempt = next((a for a in cycle["attempts"] if a["attemptId"] == attempt_id), None)
            if not attempt:
                raise HarnessError("OWNER_MISMATCH", "attemptId")
            existing = tx.get("call", call["callId"])
            bound = {"cycleId": cycle_id, "attemptId": attempt_id, "call": call}
            if existing:
                if existing != bound:
                    raise HarnessError("ID_CONFLICT", "callId")
                return existing
            ancestors = {row["callId"]: row.get("parentCallId") for row in attempt["calls"]}
            ancestors[call["callId"]] = call.get("parentCallId")
            for key in ancestors:
                seen, current = set(), key
                while current in ancestors:
                    if current in seen:
                        raise HarnessError("CALL_CYCLE", "parentCallId")
                    seen.add(current)
                    current = ancestors[current]
            attempt["calls"].append(call)
            tx.put("call", call["callId"], bound)
            self._save_cycle(tx, cycle)
            return bound

    def confirm_usage(self, cycle_id, attempt_id, call_ids, *, source, observation):
        """Host confirms the complete call set using trusted settlement evidence.

        This is deliberately independent of closure. A later new call makes the
        old confirmation inapplicable without discarding its historical basis.
        """
        _id(source, "source")
        if not isinstance(call_ids, list) or any(not isinstance(value, str) for value in call_ids) or len(set(call_ids)) != len(call_ids):
            raise HarnessError("INVALID_FIELD", "callIds")
        if not observation:
            raise HarnessError("USAGE_UNCONFIRMED", "observation")
        with self._transaction() as tx:
            cycle = self._cycle(tx, cycle_id)
            attempt = next((a for a in cycle["attempts"] if a["attemptId"] == attempt_id), None)
            if not attempt:
                raise HarnessError("OWNER_MISMATCH", "attemptId")
            if attempt["status"] != "finished" or attempt["writersStopped"] is not True:
                raise HarnessError("WRITERS_UNCONFIRMED", "attemptId")
            if set(call_ids) != {call["callId"] for call in attempt["calls"]}:
                raise HarnessError("USAGE_CALL_SET_MISMATCH", "callIds")
            confirmation = {"callIds": sorted(call_ids), "source": source, "observation": observation}
            existing = attempt.get("usageConfirmation")
            if existing and all(existing.get(key) == value for key, value in confirmation.items()):
                return existing
            confirmation["confirmedAt"] = self.utc_now()
            attempt["usageConfirmation"] = confirmation
            attempt.setdefault("usageConfirmations", []).append(confirmation)
            self._save_cycle(tx, cycle)
            return confirmation

    @staticmethod
    def _usage(attempt):
        calls = {call["callId"]: call for call in attempt["calls"]}
        selected, ambiguous = [], False
        for call in calls.values():
            parent, covered = call.get("parentCallId"), False
            while parent:
                ancestor = calls.get(parent)
                if not ancestor:
                    ambiguous = True
                    break
                if ancestor["coverage"] == "subtree":
                    covered = True
                    break
                if ancestor["coverage"] == "unknown":
                    ambiguous = True
                    covered = True
                    break
                parent = ancestor.get("parentCallId")
            if not covered:
                selected.append(call)
        unknown = ambiguous or any(c["coverage"] == "unknown" for c in selected)
        confirmation = attempt.get("usageConfirmation")
        confirmed = bool(confirmation and attempt["status"] == "finished" and attempt["writersStopped"]
                         and set(confirmation["callIds"]) == set(calls))
        result = {"status": "available", "callCount": len(calls), "countedCallIds": [c["callId"] for c in selected],
            "observedFieldsComplete": {}, "coverage": {"scope": "attempt", "callSetConfirmed": confirmed,
                "callIds": sorted(calls), "confirmation": confirmation}}
        for field in ("cost", "inputTokens", "outputTokens"):
            known = [c[field] for c in selected if c.get(field) is not None]
            result[field] = sum(known) if known or (confirmed and not calls) else None
            observed_complete = not unknown and len(known) == len(selected) and bool(selected or confirmed)
            result["observedFieldsComplete"][field] = observed_complete
            result[field + "Complete"] = confirmed and observed_complete
            if not result[field + "Complete"]:
                result["status"] = "partial"
        result["totalTokens"] = (result["inputTokens"] + result["outputTokens"]
                                 if result["inputTokens"] is not None and result["outputTokens"] is not None else None)
        result["totalTokensComplete"] = result["inputTokensComplete"] and result["outputTokensComplete"]
        result["observedFieldsComplete"]["totalTokens"] = result["observedFieldsComplete"]["inputTokens"] and result["observedFieldsComplete"]["outputTokens"]
        return result

    @staticmethod
    def _cycle_usage(cycle):
        attempts = cycle["attempts"]
        closed = cycle["protocolState"] == "closed"
        confirmed = bool(attempts) and closed and all(a["usage"]["coverage"]["callSetConfirmed"] for a in attempts)
        result = {"status": "available", "attemptCount": len(attempts), "observedFieldsComplete": {},
            "coverage": {"scope": "cycle", "cycleClosed": closed, "callSetConfirmed": confirmed,
                "attemptIds": [a["attemptId"] for a in attempts],
                "completeAttemptIds": [a["attemptId"] for a in attempts if a["usage"]["coverage"]["callSetConfirmed"]]}}
        for field in ("cost", "inputTokens", "outputTokens", "totalTokens"):
            known = [a["usage"][field] for a in attempts if a["usage"][field] is not None]
            result[field] = sum(known) if known else None
            result[field + "Complete"] = bool(attempts) and closed and all(a["usage"][field + "Complete"] for a in attempts)
            result["observedFieldsComplete"][field] = bool(attempts) and all(a["usage"]["observedFieldsComplete"][field] for a in attempts)
            if not result[field + "Complete"]:
                result["status"] = "partial"
        return result

    def close_cycle(self, cycle_id, close_id, *, outcome, verification, continuation_decision=None,
                    quality_applicability=None, submission_id=None):
        """Protocol closure is neither quality approval nor dispatch authorization.

        verification is a host fact: writersStopped, attemptResults (all IDs),
        evidenceRefs (immutable bindings), checkedAt, plus actual observations.
        A failure without a model submission is a system termination record.
        """
        _id(close_id, "closeId")
        payload = {"outcome": outcome, "verification": verification, "continuationDecision": continuation_decision,
                   "qualityApplicability": quality_applicability, "submissionId": submission_id}
        with self._transaction() as tx:
            cycle = self._cycle(tx, cycle_id)
            previous = cycle["closeReceipt"]
            if previous:
                if previous["closeId"] != close_id or previous["input"] != payload:
                    raise HarnessError("CYCLE_CLOSED", "closeId")
                return previous
            if outcome not in RESULTS:
                raise HarnessError("INVALID_FIELD", "outcome")
            if cycle["activeAttemptId"] or any(not a["writersStopped"] for a in cycle["attempts"]) or verification.get("writersStopped") is not True:
                raise HarnessError("WRITERS_UNCONFIRMED", "writersStopped")
            if not verification.get("checkedAt") or set(verification.get("attemptResults", [])) != {a["attemptId"] for a in cycle["attempts"]}:
                raise HarnessError("RESULTS_UNCONFIRMED", "attemptResults")
            submission = next((s for s in cycle["submissions"] if s["submissionId"] == submission_id), None)
            if submission_id and not submission:
                raise HarnessError("SUBMISSION_MISSING", "submissionId")
            if outcome in {"completed", "partial"} and not submission:
                raise HarnessError("SUBMISSION_MISSING", "submissionId")
            if submission and verification.get("submittedVersionUnchanged") is not True:
                raise HarnessError("EVIDENCE_UNCONFIRMED", "submittedVersionUnchanged")
            if outcome in {"completed", "partial"}:
                if submission["payload"]["result"] != outcome:
                    raise HarnessError("RESULT_MISMATCH", "submission.result")
                if not submission["payload"].get("evidenceRefs"):
                    raise HarnessError("EVIDENCE_MISSING", "evidenceRefs")
            if outcome == "completed":
                submitting_attempt = next(a for a in cycle["attempts"] if a["attemptId"] == submission["attemptId"])
                if submitting_attempt["actualResult"]["outcome"] != "completed":
                    raise HarnessError("RESULT_MISMATCH", "actualResult")
            self._verify_refs(tx, cycle, verification.get("evidenceRefs", []))
            if submission:
                required = submission["payload"].get("evidenceRefs", [])
                if any(ref not in verification.get("evidenceRefs", []) for ref in required):
                    raise HarnessError("EVIDENCE_UNCONFIRMED", "evidenceRefs")
            decision = continuation_decision or {"allowed": False, "reason": "not_evaluated"}
            if decision.get("allowed") and (outcome not in {"completed", "partial"} or not decision.get("basis") or not decision.get("checkedAt")):
                raise HarnessError("CONTINUATION_UNCONFIRMED", "continuationDecision")
            cycle.update(protocolState="closed", outcome=outcome, endedAt=self.utc_now(),
                         qualityApplicability=quality_applicability or [], continuationDecision=decision)
            self._settle(cycle["executionTimer"], stop=True)
            self._settle(cycle["budgetTimer"], stop=True)
            if cycle["totalTimer"]:
                self._settle(cycle["totalTimer"], stop=True)
            for recovery in cycle["recoveries"]:
                self._settle(recovery["timer"], stop=True)
                recovery.update(status="closed", endedAt=cycle["endedAt"])
            receipt = {"closeId": close_id, "cycleId": cycle_id, "outcome": outcome, "closedAt": cycle["endedAt"],
                       "source": "runtime" if submission else "system_termination", "input": payload}
            cycle["closeReceipt"] = receipt
            self._save_cycle(tx, cycle)
            return receipt

    def set_continuation_decision(self, cycle_id, decision):
        """Host control-path recheck; preserve the immutable closing decision."""
        if not isinstance(decision, dict) or type(decision.get("allowed")) is not bool:
            raise HarnessError("INVALID_FIELD", "continuationDecision")
        _id(decision.get("reason"), "reason")
        if not decision.get("checkedAt"):
            raise HarnessError("CONTINUATION_UNCONFIRMED", "checkedAt")
        with self._transaction() as tx:
            cycle = self._cycle(tx, cycle_id)
            if cycle["protocolState"] != "closed" or not cycle["closeReceipt"]:
                raise HarnessError("CYCLE_NOT_CLOSED")
            if cycle["activeAttemptId"] or any(not a["writersStopped"] for a in cycle["attempts"]):
                raise HarnessError("WRITERS_UNCONFIRMED")
            if decision["allowed"] and (cycle["outcome"] not in {"completed", "partial"} or
                    cycle["closeReceipt"]["source"] != "runtime" or not decision.get("basis")):
                raise HarnessError("CONTINUATION_UNCONFIRMED")
            previous = tx.get("continuation", cycle_id)
            if previous and previous["decision"] == decision:
                return previous
            value = {"decision": decision, "revision": (previous["revision"] if previous else 0) + 1}
            tx.put("continuation", cycle_id, value)
            return value

    def snapshot(self, cycle_ids=None, *, compact=False, catalog=False):
        if not self.path.exists():
            return {"projectionVersion": 2, "projectionEpoch": None, "snapshotRevision": 0,
                    "generation": None, "currentCycleId": None, "cycles": []}
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            tx = _Transaction(connection)
            meta = tx.get("meta", "state")
            kind = "cycle_catalog" if catalog else "cycle_index" if compact else "cycle"
            if (compact or catalog) and connection.execute("SELECT COUNT(*) FROM records WHERE kind='cycle'").fetchone()[0] != connection.execute("SELECT COUNT(*) FROM records WHERE kind=?", (kind,)).fetchone()[0]:
                raise HarnessError("INDEX_UNAVAILABLE")
            if cycle_ids is None:
                rows = connection.execute("SELECT payload FROM records WHERE kind=? ORDER BY rowid", (kind,))
            else:
                ids = list(dict.fromkeys(cycle_ids))
                rows = connection.execute("SELECT payload FROM records WHERE kind=? AND id IN (" +
                    ",".join("?" for _ in ids) + ") ORDER BY rowid", [kind, *ids]) if ids else []
            cycles = [json.loads(row[0]) for row in rows]
            decisions = {row[0]: json.loads(row[1]) for row in connection.execute("SELECT id,payload FROM records WHERE kind='continuation'")}
        finally:
            connection.close()
        for cycle in cycles:
            if cycle["cycleId"] in decisions:
                decision = decisions[cycle["cycleId"]]
                cycle.update(continuationDecision=decision["decision"], continuationDecisionRevision=decision["revision"])
            execution, reliability = self._elapsed(cycle["executionTimer"])
            recovery_seconds = 0
            for recovery in cycle["recoveries"]:
                elapsed, reliable = self._elapsed(recovery["timer"])
                recovery_seconds += elapsed
                if reliable != "reliable":
                    reliability = "unknown"
            total, total_reliability = self._elapsed(cycle["totalTimer"]) if cycle["totalTimer"] else (0, "reliable")
            if total_reliability != "reliable":
                reliability = "unknown"
            cycle["time"] = {"startedAt": cycle["startedAt"], "endedAt": cycle["endedAt"],
                "executionSeconds": execution, "recoverySeconds": recovery_seconds, "totalSeconds": total,
                "reliability": reliability, "deadline": cycle["deadline"], "timeClass": cycle["timeClass"],
                "hardLimitSeconds": cycle["executionTimer"]["limitSeconds"]}
            active = next((a for a in cycle["attempts"] if a["attemptId"] == cycle["activeAttemptId"]), None)
            selected = active or (cycle["attempts"][-1] if cycle["attempts"] else None)
            cycle["report"] = (selected.get("report", {"status": "missing"}) if (compact or catalog) and selected else
                selected["reports"][-1] if selected and selected["reports"] else
                {"status": "missing", "reporterAttemptId": selected["attemptId"] if selected else None})
            for attempt in cycle["attempts"]:
                if not compact and not catalog:
                    attempt["usage"] = self._usage(attempt)
                    attempt["report"] = attempt["reports"][-1] if attempt["reports"] else {"status": "missing"}
            if not compact and not catalog:
                cycle["usage"] = self._cycle_usage(cycle)
        return {"projectionVersion": 2, **meta, "cycles": cycles}

    def read_evidence(self, evidence_id):
        if not self.path.exists():
            return None
        connection = self._connect()
        try:
            return _Transaction(connection).get("evidence", evidence_id)
        finally:
            connection.close()

    def read_attempt_ownership(self, attempt_id):
        """Trusted read-side process join; callers must not expose capabilities."""
        if not self.path.exists():
            return None
        connection = self._connect()
        try:
            return _Transaction(connection).get('attempt', attempt_id)
        finally:
            connection.close()

    def read_metadata(self):
        if not self.path.exists():
            return {'projectionEpoch': None, 'snapshotRevision': 0}
        connection = self._connect()
        try:
            return _Transaction(connection).get('meta', 'state')
        finally:
            connection.close()

    def client(self, context):
        return AttemptClient(self, json.loads(_json(context)))


class AttemptClient:
    """Bind server-side context; never accept model-supplied replacement context."""
    def __init__(self, store, context):
        self._store, self._context = store, context

    def publish_progress(self, message_id, report):
        return self._store.publish_progress(self._context, message_id, report)

    def checkpoint(self, message_id, payload):
        return self._store.checkpoint(self._context, message_id, payload)

    def request_extension(self, message_id, reason, remaining_seconds):
        return self._store.request_extension(self._context, message_id, reason, remaining_seconds)

    def submit(self, submission_id, payload):
        return self._store.submit(self._context, submission_id, payload)

    def status(self):
        snapshot = self._store.snapshot()
        cycle = next((c for c in snapshot["cycles"] if c["cycleId"] == self._context["cycleId"]), None)
        return {"projectionEpoch": snapshot["projectionEpoch"], "snapshotRevision": snapshot["snapshotRevision"], "cycle": cycle}
