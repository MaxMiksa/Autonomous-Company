#!/usr/bin/env python3
"""Tests for scripts/ops/work-item.py — work-item card schema, transitions, active count.

Run: python3 tests/test_work_item.py   (no pytest dependency)
"""
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "ops" / "work-item.py"
spec = importlib.util.spec_from_file_location("work_item", SCRIPT)
wi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wi)

_failures = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        _failures.append(name)


SHA = "a" * 64
BASE = {
    "id": "P1-KB09-KARAR004",
    "version": 1,
    "gate": "G0",
    "status_proposal": "DEFINED",
    "define": {"success_criteria": ["KB-09 cites KARAR-004 PD/LGD values"], "assumptions": [], "out_of_scope": []},
}


def card(**kw):
    c = copy.deepcopy(BASE)
    c.update(kw)
    return c


PLANNED = card(status_proposal="PLANNED", plan={"steps": ["edit KB-09"]},
               acceptance_tests=[{"id": "T1", "check": "grep -c KARAR-004 KB-09 >= 1"}])


def test_validate():
    check("minimal DEFINED card is valid", wi.validate(card()) == [])
    check("PLANNED without acceptance tests is invalid",
          any("acceptance_tests" in m for m in wi.validate(card(status_proposal="PLANNED", plan={"steps": ["x"]}))))
    check("PLANNED with tests + steps is valid", wi.validate(PLANNED) == [])
    check("bad gate rejected", wi.validate(card(gate="G9")) != [])
    check("bad id rejected", wi.validate(card(id="p1 lower")) != [])
    check("version 0 rejected", wi.validate(card(version=0)) != [])
    check("bool version rejected", wi.validate(card(version=True)) != [])
    for bad in ("../secrets/runtime.env", "/app/logs/runtime.env", "docs\\x.md"):
        check(f"evidence path rejected: {bad}",
              wi.validate(card(evidence=[{"path": bad, "sha256": SHA}])) != [])
    check("evidence path without sha rejected", wi.validate(card(evidence=[{"path": "docs/ceo/a.md"}])) != [])
    check("evidence with two kinds rejected",
          wi.validate(card(evidence=[{"path": "docs/a.md", "sha256": SHA, "record": "MERSIS-1"}])) != [])
    check("record-only evidence accepted", wi.validate(card(evidence=[{"record": "KARAR-004"}])) == [])
    verified = dict(PLANNED, status_proposal="VERIFIED")
    check("VERIFIED without evidence rejected", any("evidence" in m for m in wi.validate(verified)))
    check("BLOCKED without blocked{} rejected", wi.validate(card(status_proposal="BLOCKED")) != [])
    check("BLOCKED with reason/owner/since accepted",
          wi.validate(card(status_proposal="BLOCKED",
                           blocked={"reason": "sponsor Gate 0 frame decision", "owner": "sponsor", "since": "2026-10-16"})) == [])
    check("non-object card rejected", wi.validate([1, 2]) != [])


def test_transition():
    ip = dict(PLANNED, status_proposal="IN_PROGRESS")
    check("DEFINED -> PLANNED legal", wi.transition(card(), PLANNED) == [])
    check("PLANNED -> IN_PROGRESS legal", wi.transition(PLANNED, ip) == [])
    check("DEFINED -> IN_PROGRESS skips a phase",
          any("skipped" in m for m in wi.transition(card(), dict(ip))))
    changed = copy.deepcopy(ip)
    changed["acceptance_tests"] = [{"id": "T1", "check": "weaker check"}]
    check("loosening frozen tests without version bump is illegal", wi.transition(PLANNED, changed) != [])
    bumped = copy.deepcopy(changed); bumped["version"] = 2
    check("changing tests with version+1 is legal", wi.transition(PLANNED, bumped) == [])
    closed = dict(PLANNED, status_proposal="CLOSED", evidence=[{"record": "R"}])
    check("CLOSED -> BLOCKED illegal",
          wi.transition(closed, dict(closed, status_proposal="BLOCKED",
                                     blocked={"reason": "r", "owner": "o", "since": "s"})) != [])
    reopened = dict(closed, status_proposal="IN_PROGRESS", version=2)
    check("CLOSED -> IN_PROGRESS with version+1 legal (rework)", wi.transition(closed, reopened) == [])
    check("CLOSED -> IN_PROGRESS without bump illegal",
          wi.transition(closed, dict(closed, status_proposal="IN_PROGRESS")) != [])
    check("version decrease illegal", wi.transition(dict(PLANNED, version=3), PLANNED) != [])
    blocked = dict(PLANNED, status_proposal="BLOCKED", blocked={"reason": "r", "owner": "o", "since": "s"})
    check("BLOCKED -> IN_PROGRESS legal", wi.transition(blocked, ip) == [])
    check("BLOCKED -> CLOSED illegal", wi.transition(blocked, closed) != [])
    check("id change illegal", wi.transition(PLANNED, dict(PLANNED, id="OTHER-ID")) != [])


def _app_with(cards):
    app = Path(tempfile.mkdtemp())
    d = app / "memories" / "work-items"
    d.mkdir(parents=True)
    for name, body in cards.items():
        (d / name).write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")
    return app


def test_active_count():
    app = _app_with({
        "a.json": PLANNED,
        "b.json": dict(PLANNED, id="B-CARD", status_proposal="IN_PROGRESS"),
        "c.json": dict(PLANNED, id="C-CARD", status_proposal="BLOCKED",
                       blocked={"reason": "r", "owner": "o", "since": "s"}),
        "d.json": "{not json",
        "e.json": dict(PLANNED, id="E-CARD", gate="G9"),  # invalid card never counts
        "f.json": card(id="F-CARD"),  # DEFINED is not active
    })
    check("active-count counts only valid PLANNED/IN_PROGRESS", wi.active_count(app) == 2)
    check("active-count with no card dir is 0", wi.active_count(Path(tempfile.mkdtemp())) == 0)
    r = subprocess.run([sys.executable, str(SCRIPT), "active-count", "--app", "/nonexistent/x"],
                       capture_output=True, text=True)
    check("active-count CLI fail-safe: exit 0 and prints 0", r.returncode == 0 and r.stdout.strip() == "0")


def test_verify_evidence():
    app = Path(tempfile.mkdtemp())
    (app / "docs").mkdir()
    (app / "docs" / "kb09.md").write_text("KARAR-004\n", encoding="utf-8")
    good = hashlib.sha256(b"KARAR-004\n").hexdigest()
    outside = Path(tempfile.mkdtemp()) / "secret.env"
    outside.write_text("X=1\n", encoding="utf-8")
    os.symlink(outside, app / "docs" / "link.env")
    c = card(evidence=[{"path": "docs/kb09.md", "sha256": good},
                       {"path": "docs/kb09.md", "sha256": SHA},
                       {"path": "docs/link.env", "sha256": SHA}])
    res = dict(enumerate(s for _, s in wi.verify_evidence(app, c)))
    check("matching sha -> OK", res[0] == "OK")
    check("changed content -> DRIFT", res[1] == "DRIFT")
    check("symlink escaping the root -> MISSING_OR_OUTSIDE", res[2] == "MISSING_OR_OUTSIDE")


def test_cli_validate_exit_codes():
    d = Path(tempfile.mkdtemp())
    ok, bad = d / "ok.json", d / "bad.json"
    ok.write_text(json.dumps(PLANNED), encoding="utf-8")
    bad.write_text(json.dumps(card(gate="G9")), encoding="utf-8")
    r1 = subprocess.run([sys.executable, str(SCRIPT), "validate", str(ok)], capture_output=True, text=True)
    r2 = subprocess.run([sys.executable, str(SCRIPT), "validate", str(ok), str(bad)], capture_output=True, text=True)
    check("validate CLI exit 0 on valid card", r1.returncode == 0)
    check("validate CLI exit 2 when any card invalid", r2.returncode == 2 and "INVALID" in r2.stdout)


if __name__ == "__main__":
    test_validate()
    test_transition()
    test_active_count()
    test_verify_evidence()
    test_cli_validate_exit_codes()
    print(f"\n{len(_failures)} failure(s)")
    sys.exit(1 if _failures else 0)
