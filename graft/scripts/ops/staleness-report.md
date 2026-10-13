# scripts/ops/staleness-report.py · [[state-staleness-probes]] [[wowcar-source-modules]]

Read-only stdlib script that measures staleness/rot across Program Auditor memory surfaces and writes a deterministic markdown report for the auditor to interpret.

- _bytes · function · L37-L38 — Returns the UTF-8 byte length of a string, used for size measurements.
- _read · function · L41-L45 — Reads a file as UTF-8 with replacement errors, returning empty string on OSError so missing files don't crash the report.
- _sections · function · L48-L55 — Splits markdown text into (heading, body) sections keyed on '## ' lines, preserving each section's joined text.
- _heading_date · function · L58-L65 — Extracts a YYYY-MM-DD date from a section heading, returning None when absent or invalid.
- directive_rows · function · L68-L86 — Measures the human-directive body and each section for size, age, and standing-rule vocabulary, flagging archive candidates for old sections with standing language.
- opreq_rows · function · L89-L99 — Counts operator-request statuses and bytes of RESOLVED text, flagging when resolved content bloats the body.
- decisions_rows · function · L102-L107 — Counts operator decisions and those predating the re-charter date, flagging when too many old decisions should be archived.
- consensus_rows · function · L110-L117 — Reports consensus.md total size and flags any section exceeding the prune ceiling as a large section.
- ledger_rows · function · L120-L132 — Reads the conflict ledger and flags when the Version header line no longer reflects the last section's cycle.
- prompt_rows · function · L135-L142 — Measures PROMPT.md size and legacy-vocabulary hits, flagging oversized sections and total size for shrinking.
- weekly_rows · function · L145-L155 — Compares present ISO weekly report weeks against the expected range since the first report, flagging gaps that must be closed via directive.
- backup_rows · function · L158-L168 — Counts files and total bytes in backup/receipts directories, flagging cleanup when a directory holds too many files.
- build · function · L171-L179 — Assembles all surface rows into the final markdown report with a header and a count of flagged lines.
- main · function · L182-L199 — Parses CLI args, computes the report, and writes it to the output file or stdout, returning an exit code.
