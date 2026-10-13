# scripts/compact-postcheck.py · [[compact-ritual-tooling]]

Post-compact audit hook that records whether the real compact_summary carried the required resume anchor sections into a history log and prints a canary warning when any are missing.

- main · function · L39-L79 — Reads the hook payload, checks which required anchors survived in compact_summary, appends an audit line to the log, and prints a canary warning when anchors are missing.
