#!/usr/bin/env python3
"""Tests for scripts/ops/work-window.py — the empty-cycle work-window brake.

Run: python3 tests/test_work_window.py   (no pytest dependency)
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "ops" / "work-window.py"

OPEN = 10
CLOSED = 0
_failures = []


def run(delta_line, cycle, *, state=None, ttl=None, env=None, app=None):
    """Invoke the brake; return (exit_code, stdout, state_dict_after)."""
    tmp = app or tempfile.mkdtemp()
    logs = Path(tmp) / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    state_path = logs / "work-window.json"
    if state is not None:
        state_path.write_text(state if isinstance(state, str) else json.dumps(state), encoding="utf-8")
    cmd = [sys.executable, str(SCRIPT), "--cycle", str(cycle), "--app", str(tmp)]
    if ttl is not None:
        cmd += ["--ttl", str(ttl)]
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(cmd, input=delta_line, capture_output=True, text=True, env=e)
    after = None
    if state_path.is_file():
        try:
            after = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            after = "CORRUPT"
    return p.returncode, p.stdout, after


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        _failures.append(name)


# 1. DELTA changed -> window OPENS (exit 10), line emitted, state written.
rc, out, st = run("DELTA: changed=opreq_open — foo\n", 340)
check("changed opens window (exit 10)", rc == OPEN)
check("changed emits injection line", "WORK-WINDOW OPEN" in out)
check("changed writes state opened_at=340", st and st.get("opened_at_cycle") == 340)
check("changed records reason", st and "opreq_open" in st.get("reason_fields", ""))

# 2. DELTA none, no prior state -> CLOSED, no line.
rc, out, st = run("DELTA: none — nothing moved\n", 341)
check("none+no-state is closed (exit 0)", rc == CLOSED)
check("none+no-state emits no line", out.strip() == "")

# 3. DELTA none, fresh window (age 2 < ttl 5) -> OPEN.
rc, out, st = run("DELTA: none\n", 342, state={"opened_at_cycle": 340, "ttl_cycles": 5, "reason_fields": "opreq_open"})
check("none within window is open (exit 10)", rc == OPEN)
check("open line shows age", "2 cycle(s) ago" in out)

# 4. DELTA none, expired window (age 5 >= ttl 5) -> CLOSED.
rc, out, st = run("DELTA: none\n", 345, state={"opened_at_cycle": 340, "ttl_cycles": 5, "reason_fields": "x"})
check("none past window is closed (exit 0)", rc == CLOSED)

# 5. Restart guard: stored opened_at > cycle (negative age) -> CLOSED, not stuck-open.
rc, out, st = run("DELTA: none\n", 1, state={"opened_at_cycle": 340, "ttl_cycles": 5, "reason_fields": "x"})
check("restart negative-age is closed (exit 0)", rc == CLOSED)

# 6. Corrupt state file -> fail-closed OPEN.
rc, out, st = run("DELTA: none\n", 400, state="{not json")
check("corrupt state fails closed (exit 10)", rc == OPEN)
check("corrupt state emits a line", "WORK-WINDOW OPEN" in out)

# 7. Unparseable DELTA (no DELTA line) -> fail-closed OPEN.
rc, out, st = run("some snapshot without a delta line\n", 401)
check("missing DELTA fails closed (exit 10)", rc == OPEN)

# 8. First snapshot, no state -> CLOSED (cold start is a full cycle already).
rc, out, st = run("DELTA: first snapshot — baseline\n", 1)
check("first snapshot is closed (exit 0)", rc == CLOSED)

# 9. Kill switch WORK_WINDOW_ENABLED=0 -> CLOSED even on changed.
rc, out, st = run("DELTA: changed=opreq_open\n", 500, env={"WORK_WINDOW_ENABLED": "0"})
check("kill switch disables brake (exit 0)", rc == CLOSED)
check("kill switch emits no line", out.strip() == "")

# 10. TTL via env var honored (age 6 < ttl 8 -> OPEN).
rc, out, st = run("DELTA: none\n", 346, state={"opened_at_cycle": 340, "ttl_cycles": 8, "reason_fields": "x"},
                  env={"WORK_WINDOW_TTL_CYCLES": "8"})
check("stored ttl 8 keeps window open at age 6 (exit 10)", rc == OPEN)

# 11. changed refreshes an existing window to the new cycle.
rc, out, st = run("DELTA: changed=wowcar_sources\n", 350,
                  state={"opened_at_cycle": 340, "ttl_cycles": 5, "reason_fields": "opreq_open"})
check("changed refreshes opened_at to 350", st and st.get("opened_at_cycle") == 350)
check("changed refreshes reason", st and "wowcar_sources" in st.get("reason_fields", ""))

# 12-17. Directive-closed rule (2026-10-13): DONE pull / archive does not open the window.
DONE_SNAP = "directive: status=DONE sha16=f3854a5fc46262d7\n"
PEND_SNAP = "directive: status=PENDING sha16=753b0f09b4d3c0f1\n"
rc, out, st = run(DONE_SNAP + "DELTA: changed=directive_status,directive_sha16\n", 1003)
check("DONE pull does not open (exit 0)", rc == CLOSED and out == "")
check("DONE pull stores a closed window", st and st.get("ttl_cycles") == 0)
rc, out, st = run(DONE_SNAP + "DELTA: changed=directive_sha16\n", 1004,
                  state={"opened_at_cycle": 1001, "ttl_cycles": 5, "reason_fields": "directive_sha16"})
check("archive while DONE closes a still-open window", rc == CLOSED)
rc, out, st = run("DELTA: none\n", 1005, state=st)
check("next idle cycle after DONE stays closed", rc == CLOSED)
rc, out, st = run(PEND_SNAP + "DELTA: changed=directive_status,directive_sha16\n", 1010)
check("new PENDING append still opens", rc == OPEN)
rc, out, st = run(DONE_SNAP + "DELTA: changed=directive_status,opreq_open\n", 1011)
check("DONE plus another field still opens", rc == OPEN)
rc, out, st = run("DELTA: changed=directive_sha16\n", 1012)
check("directive change without status line fails closed (opens)", rc == OPEN)

# 19-24. Auditor rule (2026-10-13): a new auditor report alone carries no company work.
rc, out, st = run(DONE_SNAP + "DELTA: changed=auditor_hash\n", 1004)
check("auditor-only change does not open (exit 0)", rc == CLOSED and out == "")
check("auditor-only change writes no window state", st is None)
live_win = {"opened_at_cycle": 1010, "ttl_cycles": 5, "reason_fields": "directive_status,directive_sha16"}
rc, out, st = run(PEND_SNAP + "DELTA: changed=auditor_hash\n", 1012, state=live_win)
check("auditor-only change keeps an open directive window open", rc == OPEN)
check("auditor-only change leaves the stored window untouched", st == live_win)
rc, out, st = run(DONE_SNAP + "DELTA: changed=directive_status,auditor_hash\n", 1013, state=live_win)
check("DONE pull together with auditor change closes", rc == CLOSED and st.get("ttl_cycles") == 0)
rc, out, st = run(PEND_SNAP + "DELTA: changed=directive_sha16,auditor_hash\n", 1020)
check("PENDING append together with auditor change still opens", rc == OPEN)
rc, out, st = run(DONE_SNAP + "DELTA: changed=auditor_hash,opreq_open\n", 1021)
check("auditor plus OPREQ change still opens", rc == OPEN)

print()
if _failures:
    print(f"{len(_failures)} FAILURE(S): " + ", ".join(_failures))
    sys.exit(1)
print("ALL TESTS PASSED")
