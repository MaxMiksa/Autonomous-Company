# scripts/ops/budget-calibration-report.py · [[cost-budget-accounting]]

Generates a budget calibration report over a UTC observation window, explicitly separating pre/post-cutover data so the retired 5h gate and the live daily/weekly gates are never blended into one misleading percentile.

- split_by_cutover · function · L72-L76 — Partitions spend entries into pre-cutover and post-cutover lists so the retired 5h gate is measured only against the regime that actually used it.
- pct · function · L79-L84 — Computes a percentile of a value list using linear-interpolation-free nearest-rank selection, returning 0 for empty input.
- load_claude · function · L87-L102 — Reads claude spend rows from spend-total.log, keeping only rows within the observation window.
- load_codex · function · L105-L138 — Loads codex session spend via ccusage, excluding analyst sessions and rows outside the window, and reports missing data as a gap rather than zero.
- sliding · function · L141-L157 — Computes sliding-window spend sums sampled at a fixed step, optionally bounded so the series stops at the cutover instead of trailing into zero-filled post-cutover samples.
- daily_buckets · function · L160-L166 — Aggregates spend into complete UTC calendar-day buckets, excluding the current incomplete day.
- stats_line · function · L169-L173 — Formats a percentile/max summary line for a named metric, or reports no data when empty.
- main · function · L176-L289 — Orchestrates the full report: warns about regime change, prints per-engine 5h/daily, combined daily, weekly, gate-block/pause, and operator-impact sections without changing any threshold.
