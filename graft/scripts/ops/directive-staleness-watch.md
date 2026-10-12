# scripts/ops/directive-staleness-watch.py · [[human-directive-lifecycle]]

Cron watcher that alerts when the human directive has been PENDING too long, escalating once at the warn threshold then every repeat interval, while surfacing the audit-log reasons it is stuck.

- read_directive · function · L40-L56 — Parses the directive file to extract its current status and the timestamp of its last ## Updated line.
- last_line_matching · function · L59-L66 — Returns the last audit-log line containing a given needle so the watcher can quote the operator's own words.
- main · function · L69-L165 — Orchestrates the staleness check: clears state when not pending, computes age, and notifies on schedule with audit-log context.
