# scripts/analyst/promote_directive.py

Deterministic fail-closed gate that decides whether the Opportunity Analyst's report may auto-promote into human-directive.md, blocking on any risk keyword, missing field, or escalation near the active validation.

- sha256 · function · L91-L92 — Computes a hex digest of a file's bytes for hashing directive content before/after promotion.
- audit · function · L95-L98 — Appends a UTC-timestamped line to the promotion audit log for traceability of every decision.
- blocked · function · L101-L104 — Records a BLOCKED outcome in the audit log, prints the reason to stdout, and exits with code 0 so the caller never fails.
- notify · function · L107-L113 — Best-effort Telegram notification of promotion events, silently ignoring missing script or failures.
- main · function · L116-L225 — Runs the full promotion gate: validates inputs, scans for risk/escalation language, backs up, writes, and read-back verifies the new directive.
