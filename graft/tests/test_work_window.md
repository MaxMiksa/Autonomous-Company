# tests/test_work_window.py · [[work-window-watchdog]]

Test suite for the work-window brake script, exercising open/closed window behavior across changed/none deltas, TTL expiry, restart, corrupt state, kill switch, and env TTL.

- run · function · L21-L42 — Helper that invokes the work-window script in a temp app dir with a given delta line and cycle, returning exit code, stdout, and the resulting state file contents.
- check · function · L45-L48 — Records a named pass/fail assertion and accumulates failures for the final exit status.
