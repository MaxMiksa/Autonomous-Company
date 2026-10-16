# scripts/ops/context7-check.py · [[compliance-evidence-checks]] [[context7-tool-surface-auditing]]

CLI check that audits cycle ndjson logs to flag cycles that wrote code importing an external library without calling Context7, reporting to the log rather than blocking.

- externals · function · L59-L75 — Extracts the set of external (non-stdlib, non-relative) modules a file imports, filtering out standard-library and local imports so only library dependencies count.
- scan · function · L78-L108 — Parses one cycle's ndjson to count MCP/Context7 calls and collect external-library imports from every write/edit to a source file.
- walk_calls · function · L111-L122 — Recursively finds write/edit tool-call objects wherever the harness nested them in a record.
- verdict · function · L125-L138 — Decides whether a cycle passed the Context7 rule, returning OK when no external imports or Context7 was called, else NO-CHECK with evidence.
- main · function · L141-L170 — Selects which cycle ndjson files to audit from CLI args and prints a per-cycle verdict line plus a report summary.
