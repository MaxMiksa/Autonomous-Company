# scripts/ops/staleness-report.py · [[state-snapshot-staleness]] [[state-staleness-measurement]]

Read-only stdlib script that measures staleness/rot across the Program Auditor's memory surfaces (directive, requests, decisions, consensus, ledger, PROMPT, weekly reports, backups) and writes a deterministic markdown report the auditor interprets.

- _bytes · function · L42-L43 — Returns the UTF-8 byte length of a string, used for size measurements.
- _read · function · L46-L50 — Reads a file as UTF-8 with replacement errors, returning empty string on OSError so missing files don't crash the report.
- _sections · function · L53-L60 — Splits markdown text into (heading, body) sections keyed on '## ' lines, preserving each section's joined text.
- _heading_date · function · L63-L70 — Extracts a YYYY-MM-DD date from a section heading, returning None when absent or invalid.
- directive_rows · function · L73-L91 — Builds the D rows for the directive body and each section, flagging sections as archive candidates when they are older than 21 days with standing-rule vocabulary or oversized.
- opreq_rows · function · L94-L104 — Counts operator-request statuses and bytes of RESOLVED text, flagging when resolved content bloats the body.
- decisions_rows · function · L107-L112 — Counts operator decisions and those predating the re-charter date, flagging when too many old decisions should be archived.
- consensus_rows · function · L115-L122 — Reports consensus.md total size and flags any section exceeding the prune ceiling as a large section.
- ledger_rows · function · L125-L147 — Builds the ledger staleness row by comparing the header's section codes against the last section's code to detect a stale version line.
- prompt_rows · function · L150-L157 — Measures PROMPT.md size and legacy-vocabulary hits, flagging oversized sections and total size for shrinking.
- weekly_rows · function · L160-L173 — Builds the weekly-reports row, flagging ISO weeks missing from the expected range while honoring sponsor-accepted gaps.
- _accepted_weekly_gaps · function · L180-L196 — Collects weeks whose missing report the sponsor accepted by finding week ranges in the directive/archive with an acceptance word within 200 chars.
- backup_rows · function · L202-L218 — Builds backup/receipt rows flagging files whose mtime is older than 30 days (real age test, not file count).
- build · function · L221-L229 — Assembles all surface rows into the final markdown report with a header and a count of flagged lines.
- main · function · L232-L249 — Parses CLI args, computes the report, and writes it to the output file or stdout, returning an exit code.
