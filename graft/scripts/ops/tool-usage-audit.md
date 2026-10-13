# scripts/ops/tool-usage-audit.py · [[cycle-cost-risk-audits]] [[cycle-ndjson-logs]] [[tool-usage-audit]]

Durable per-cycle ledger of tool-consultation counts (ctx7/Airtable/Linear/Browser/graft) appended from finished cycle ndjson, idempotent via a state file, with read-only report and per-MCP-name modes.

- calls_from_ndjson · function · L43-L65 — Reassembles tool calls from jcode's event stream by pairing tool_start with streamed tool_input deltas, since tool_exec carries no input.
- categorize · function · L68-L121 — Classifies each reassembled tool call into category counters by matching bash command substrings or MCP tool names, keeping separate browser and browser_mcp denominators.
- main · function · L124-L251 — Orchestrates the audit: handles --report/--names read-only modes, and otherwise appends one JSON row per newly-changed cycle ndjson to the durable ledger while tracking processed files by size+mtime.
- dump · function · L177-L190 — Prints a sorted per-tool-name and per-server breakdown for a given name-count source in the --names report.
