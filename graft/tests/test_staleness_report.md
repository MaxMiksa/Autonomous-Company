# tests/test_staleness_report.py · [[state-snapshot-staleness]]

Integration test script that builds a synthetic app tree and runs staleness-report.py to verify its mechanical flags (archive candidates, stale headers, weekly gaps, backup cleanup, etc.) across multiple scenarios.

- check · function · L17-L20 — Helper that prints PASS/FAIL for a condition and records the test name in FAILS when it fails.
- main · function · L23-L123 — Builds a synthetic app tree, runs the staleness-report script under several scenarios (Turkish/English directives, ledger versions, backup ages), and asserts each expected flag via the check() helper.
