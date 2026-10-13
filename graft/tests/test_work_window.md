# tests/test_work_window.py · [[work-window-watchdog]]

Test suite for the work-window brake script, covering open/closed window logic, TTL expiry, restart guard, fail-closed behavior, kill switch, and the directive DONE-closed rule.

- run · function · L21-L42 — Helper that invokes the work-window script in a temp app dir with a given delta line and cycle, returning exit code, stdout, and the resulting state file contents.
- check · function · L45-L48 — Records a named pass/fail assertion and accumulates failures for the final exit status.
