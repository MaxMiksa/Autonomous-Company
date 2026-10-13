# tests/test_staleness_report.py · [[staleness-reporting]]

Integration test script that builds a synthetic app tree and runs staleness-report.py to verify its mechanical flags (archive candidates, gaps, stale headers, backups cleanup) and the --stdout mode.

- check · function · L17-L20 — Helper that prints PASS/FAIL for a condition and records the test name in FAILS when it fails.
- main · function · L23-L102 — Builds a synthetic app tree with crafted memory/docs files, runs the staleness-report script under several scenarios, and asserts each expected flag (and absence of false positives) via the check() helper.
