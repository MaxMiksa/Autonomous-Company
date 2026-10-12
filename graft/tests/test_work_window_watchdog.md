# tests/test_work_window_watchdog.py · [[work-window-watchdog]]

Integration test suite for the work-window watchdog script, verifying alarm behavior across real work, empty cycles, failed cycles, thresholds, and escape clauses.

- run · function · L18-L29 — Helper that invokes the watchdog script in a temp app dir with given cycle text and flags, returning exit code, stdout, and parsed state JSON.
- check · function · L32-L35 — Records a named pass/fail assertion and appends failures to the global list for the final summary.
