# scripts/ops/staleness-report.py · [[memory-ledger-files]] [[memory-staleness-snapshot-probes]] [[staleness-reporting]]

Read-only stdlib script that measures staleness/rot across the Program Auditor's memory surfaces and writes a deterministic markdown report the auditor interprets.

- _bytes · function · L37-L38 — Returns the UTF-8 byte length of a string, used for size measurements.
- _read · function · L41-L45 — Reads a file as UTF-8 with replacement errors, returning empty string on OSError so missing files don't crash the report.
- _sections · function · L48-L55 — Splits markdown text into (heading, body) sections keyed on '## ' lines, preserving each section's joined text.
- _heading_date · function · L58-L65 — Extracts a YYYY-MM-DD date from a section heading, returning None when absent or invalid.
- directive_rows · function · L68-L86 — Measures the human-directive body and each section for size, age, and standing-rule vocabulary, flagging archive candidates for old sections with standing language.
- opreq_rows · function · L89-L99 — Counts operator-request statuses and bytes of RESOLVED text, flagging when resolved content bloats the body.
- decisions_rows · function · L102-L107 — Counts operator decisions and those predating the re-charter date, flagging when too many old decisions should be archived.
- consensus_rows · function · L110-L117 — Reports consensus.md total size and flags any section exceeding the prune ceiling as a large section.
- ledger_rows · function · L120-L142 — Builds the ledger staleness row by comparing the header's section codes against the last section's code to detect a stale version line.
- prompt_rows · function · L145-L152 — Measures PROMPT.md size and legacy-vocabulary hits, flagging oversized sections and total size for shrinking.
- weekly_rows · function · L155-L168 — Builds the weekly-reports row, flagging ISO weeks missing from the expected range while honoring sponsor-accepted gaps.
- _accepted_weekly_gaps · function · L175-L191 — Collects weeks whose missing report the sponsor accepted by finding week ranges in the directive/archive with an acceptance word within 200 chars.
- backup_rows · function · L197-L213 — Builds backup/receipt rows flagging files whose mtime is older than 30 days (real age test, not file count).
- build · function · L216-L224 — Assembles all surface rows into the final markdown report with a header and a count of flagged lines.
- main · function · L227-L244 — Parses CLI args, computes the report, and writes it to the output file or stdout, returning an exit code.
