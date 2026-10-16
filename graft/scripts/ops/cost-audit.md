# scripts/ops/cost-audit.py · [[context7-tool-surface-auditing]] [[cost-budget-accounting]]

Deterministic daily cost-audit script that reads spend/loop/jcode logs from disk and writes a markdown report so the Opportunity Analyst interprets measured numbers instead of computing them.

- utc_day · function · L42-L43 — Converts an epoch timestamp to a UTC date string for bucketing ledger rows by day.
- read_ledger · function · L46-L67 — Parses the spend-total ledger into per-day cycle rows, filtering to the last N days and counting malformed lines.
- read_loop_log · function · L70-L111 — Extracts today's cycle cost/provenance, timeout, and turn-audit facts from the auto-loop log, tagging each cycle as estimated/hinted.
- read_jcode_log · function · L114-L131 — Parses the jcode session log for prompt-prefix token counts, tool-list lock sizes, and per-tool call tallies.
- read_tool_inventory · function · L134-L141 — Loads the MCP schema cache into a map of server name to advertised tool names.
- read_disabled_tools · function · L144-L171 — Resolves the JCODE_TOOLS_DENY denylist from process env, runtime.env, then auto-loop.sh default so §5 can subtract already-hidden tools from the advertised inventory and avoid false trim findings.
- fmt_money · function · L174-L175 — Formats a float as a two-decimal USD currency string.
- build_report · function · L178-L339 — Assembles the full cost-audit markdown report, reporting §§2-4 on the previous completed UTC day (not the still-open current day) and classifying findings as company-fixable vs infra for the analyst to route.
- main · function · L342-L360 — Parses CLI args, builds the report, and atomically writes it to the output file via a temp file and os.replace.
