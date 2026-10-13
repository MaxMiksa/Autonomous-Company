# tests/test_operator_action_router.py · [[operator-action-router]]

Test suite that exercises the real operator-action-router functions (collect_items/render/should_notify) and a real main() run with notify monkeypatched, verifying digest content, priority ordering, staleness floor, dedup, state clearing, and fail-soft behavior.

- check · function · L27-L33 — Compares an actual value against an expected value and prints PASS/FAIL, setting a global failure flag on mismatch.
- check_true · function · L36-L37 — Convenience wrapper that asserts a condition is truthy by delegating to check with the boolean value.
- make_app · function · L40-L67 — Builds a throwaway --app directory tree with optional LOOP_HOLD, operator-requests ledger, and human-directive files (with mtime-based age) so tests can exercise the real code paths.
