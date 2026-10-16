# tests/test_compact_anchor_sync.py · [[compact-ritual]]

Test that the four corners of the compact ritual (postcheck ANKORLAR, resume-lint ZORUNLU, template, hardening fixture) stay in sync with each other and with a known anchor set, failing via exit code on drift.

- _load · function · L41-L45 — Loads a Python module from a file path by spec so the test can import the two scripts under test without adding them to sys.path.
- check · function · L48-L53 — Records a named pass/fail assertion, appending the name to the global FAILURES list when the actual value does not equal the expected one.
- test_hepsi_gecti · function · L88-L89 — Pytest entry point that fails the test run if any earlier check recorded a failure.
