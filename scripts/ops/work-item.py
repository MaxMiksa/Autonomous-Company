#!/usr/bin/env python3
"""work-item.py — schema + invariant checks for the company's work-item cards.

A work item is one deliverable or gate claim, kept as `memories/work-items/<id>.json`.
The card written inside the container is only a PROPOSAL: the official state of a card
lives in the host-side gate-state (written by the independent reviewer wrapper, which
the loop cannot write). This script never decides "closed"; it only refuses malformed
cards and illegal transitions, and counts active cards for the IDLE-SKIP gate.

Subcommands:
  validate <card.json>...          schema + invariants; exit 0 ok, 2 invalid
  transition <old.json> <new.json> legal status move? exit 0 ok, 2 illegal
  active-count --app <root>        cards in PLANNED/IN_PROGRESS (not BLOCKED); prints an
                                   integer and exits 0 ALWAYS — unreadable → 0 (fail-safe:
                                   never suppresses IDLE-SKIP on error)
  verify-evidence --app <root> <card.json>  recompute sha256 of evidence paths (informational)
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

STATUSES = ["DEFINED", "PLANNED", "IN_PROGRESS", "VERIFIED", "CLOSED"]
BLOCKED = "BLOCKED"
ACTIVE = {"PLANNED", "IN_PROGRESS"}
GATES = {f"G{i}" for i in range(8)}
ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
ROLE_RE = re.compile(r"^[a-z][a-z0-9-]{1,40}$")
CARD_DIR = Path("memories") / "work-items"


def _err(errors, msg):
    errors.append(msg)


def _safe_rel(path):
    """Evidence paths are volume-relative POSIX paths: no absolute, no '..', no backslash."""
    if not isinstance(path, str) or not path or "\\" in path:
        return False
    p = PurePosixPath(path)
    return not p.is_absolute() and ".." not in p.parts


def validate(card):
    """Return a list of human-readable errors (empty = valid)."""
    e = []
    if not isinstance(card, dict):
        return ["card is not a JSON object"]
    if not ID_RE.match(str(card.get("id", ""))):
        _err(e, "id: required, A-Z/0-9/'-', 3-64 chars")
    v = card.get("version")
    if not isinstance(v, int) or isinstance(v, bool) or v < 1:
        _err(e, "version: integer >= 1")
    if card.get("gate") not in GATES:
        _err(e, "gate: one of G0..G7")
    status = card.get("status_proposal")
    if status not in STATUSES and status != BLOCKED:
        _err(e, f"status_proposal: one of {STATUSES + [BLOCKED]}")
    d = card.get("define")
    if not isinstance(d, dict) or not d.get("success_criteria"):
        _err(e, "define.success_criteria: non-empty list required")
    else:
        for k in ("success_criteria", "assumptions", "out_of_scope"):
            if k in d and not isinstance(d[k], list):
                _err(e, f"define.{k}: list")
    tests = card.get("acceptance_tests", [])
    if not isinstance(tests, list) or not all(isinstance(t, dict) and t.get("id") and t.get("check") for t in tests):
        _err(e, "acceptance_tests: list of {id, check}")
        tests = []
    reached = STATUSES.index(status) if status in STATUSES else None
    if reached is not None and reached >= STATUSES.index("PLANNED") and not tests:
        _err(e, "acceptance_tests: required before PLANNED (written before the work starts)")
    plan = card.get("plan", {})
    if reached is not None and reached >= STATUSES.index("PLANNED") and not (isinstance(plan, dict) and plan.get("steps")):
        _err(e, "plan.steps: required before PLANNED")
    for i, ev in enumerate(card.get("evidence", []) or []):
        if not isinstance(ev, dict):
            _err(e, f"evidence[{i}]: object"); continue
        kinds = [k for k in ("path", "record", "clause") if ev.get(k)]
        if len(kinds) != 1:
            _err(e, f"evidence[{i}]: exactly one of path / record / clause")
        if ev.get("path"):
            if not _safe_rel(ev["path"]):
                _err(e, f"evidence[{i}].path: volume-relative, no absolute path, no '..'")
            if not SHA_RE.match(str(ev.get("sha256", ""))):
                _err(e, f"evidence[{i}].sha256: 64 lowercase hex required with a path")
    if reached is not None and reached >= STATUSES.index("VERIFIED") and not card.get("evidence"):
        _err(e, "evidence: required at VERIFIED and later")
    if status == BLOCKED:
        b = card.get("blocked")
        if not isinstance(b, dict) or not all(b.get(k) for k in ("reason", "owner", "since")):
            _err(e, "blocked: {reason, owner, since} required when BLOCKED")
    if "lessons" in card and not isinstance(card["lessons"], list):
        _err(e, "lessons: list")
    # Optional explicit role list for the injected checklist (role-checklist.py render
    # --card); absent = the gate map applies. Existence is checked there, not here.
    roles = card.get("roles")
    if roles is not None and not (isinstance(roles, list) and 1 <= len(roles) <= 5
                                  and all(isinstance(r, str) and ROLE_RE.match(r) for r in roles)):
        _err(e, "roles: list of 1-5 role file names (kebab-case)")
    return e


def transition(old, new):
    """Errors for an old→new card change (both must already validate)."""
    e = []
    if old.get("id") != new.get("id"):
        return ["id changed"]
    ov, nv = old.get("version", 1), new.get("version", 1)
    if nv < ov:
        _err(e, "version decreased")
    so, sn = old.get("status_proposal"), new.get("status_proposal")
    if sn == BLOCKED:
        if so == "CLOSED":
            _err(e, "CLOSED cannot become BLOCKED")
    elif so == BLOCKED:
        if sn not in ACTIVE:
            _err(e, "BLOCKED may only return to PLANNED or IN_PROGRESS")
    else:
        io, inn = STATUSES.index(so), STATUSES.index(sn)
        if inn > io + 1:
            _err(e, f"skipped a phase: {so} -> {sn}")
        if inn < io and not (sn == "IN_PROGRESS" and nv == ov + 1):
            _err(e, f"backward move {so} -> {sn} only to IN_PROGRESS with version+1")
    planned = so in STATUSES and STATUSES.index(so) >= STATUSES.index("PLANNED") or so == BLOCKED
    frozen_changed = (old.get("acceptance_tests") != new.get("acceptance_tests")
                      or (old.get("define") or {}).get("success_criteria") != (new.get("define") or {}).get("success_criteria"))
    if planned and frozen_changed and nv != ov + 1:
        _err(e, "acceptance_tests / success_criteria are frozen after PLANNED: change = new version (version+1)")
    return e


def active_count(app):
    try:
        n = 0
        for p in sorted((Path(app) / CARD_DIR).glob("*.json")):
            try:
                c = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(c, dict) and not validate(c) and c.get("status_proposal") in ACTIVE:
                n += 1
        return n
    except Exception:
        return 0


def verify_evidence(app, card):
    out = []
    root = Path(app).resolve()
    for ev in card.get("evidence", []) or []:
        if not ev.get("path"):
            continue
        target = (root / ev["path"]).resolve()
        if root not in target.parents or not target.is_file():
            out.append((ev["path"], "MISSING_OR_OUTSIDE"))
            continue
        h = hashlib.sha256(target.read_bytes()).hexdigest()
        out.append((ev["path"], "OK" if h == ev.get("sha256") else "DRIFT"))
    return out


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("cards", nargs="+")
    t = sub.add_parser("transition"); t.add_argument("old"); t.add_argument("new")
    a = sub.add_parser("active-count"); a.add_argument("--app", default="/app")
    ve = sub.add_parser("verify-evidence"); ve.add_argument("--app", default="/app"); ve.add_argument("card")
    args = ap.parse_args(argv)

    if args.cmd == "active-count":
        print(active_count(args.app))
        return 0
    if args.cmd == "validate":
        bad = 0
        for c in args.cards:
            try:
                errs = validate(_load(c))
            except Exception as ex:  # unreadable / not JSON
                errs = [f"unreadable: {ex.__class__.__name__}"]
            for m in errs:
                print(f"INVALID {c}: {m}")
            bad += bool(errs)
        return 2 if bad else 0
    if args.cmd == "transition":
        old, new = _load(args.old), _load(args.new)
        errs = validate(old) + validate(new)
        errs = errs or transition(old, new)
        for m in errs:
            print(f"ILLEGAL: {m}")
        return 2 if errs else 0
    if args.cmd == "verify-evidence":
        res = verify_evidence(args.app, _load(args.card))
        for path, state in res:
            print(f"{state} {path}")
        return 0 if all(s == "OK" for _, s in res) else 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
