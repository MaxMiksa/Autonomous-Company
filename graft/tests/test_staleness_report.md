# tests/test_staleness_report.py · [[staleness-report]]

Integration test that runs the staleness-report script against a synthetic app tree and asserts each mechanical flag is produced.

- check · function · L15-L18 — Helper that prints PASS/FAIL for a condition and records the test name in FAILS when it fails.
- main · function · L21-L69 — Builds a synthetic app tree with crafted edge cases, runs the staleness-report script, and verifies every expected flag appears in the report.
