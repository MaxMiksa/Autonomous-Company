# tests/test_cost_audit_tool_surface.py · [[context7-tool-surface-auditing]]

Integration test that verifies cost-audit §5 subtracts loop-hidden tools from the advertised tool count so trimmed tools are never re-flagged as trim candidates.

- ok · function · L24-L25 — Prints a PASS line for a passing assertion.
- no · function · L28-L31 — Prints a FAIL line and sets the global failure flag so the test exits non-zero.
