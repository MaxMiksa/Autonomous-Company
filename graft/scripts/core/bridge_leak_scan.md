# scripts/core/bridge_leak_scan.py · [[value-sensitive-leak-scanner]]

Value-sensitive scanner that flags session/credential leaks in EKAP Bridge records only when a secret key appears with a real value, avoiding word-presence false positives.

- scan · function · L63-L69 — Runs every leak rule over the text and returns rule-name plus excerpt for each match.
- selftest · function · L98-L111 — Verifies negative fixtures stay clean and positive fixtures are caught, returning exit 3 if the scanner misbehaves so it is never trusted.
- main · function · L114-L127 — Dispatches selftest or reads a file/stdin, prints CLEAN or each leak finding, and maps results to exit codes.
