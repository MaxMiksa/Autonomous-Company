# scripts/ops/turn-audit.py · [[cycle-cost-risk-auditing]] [[ledger-audit-guards]]

Turn-level waste accounting classifier that reads a jcode daily log and reports per-session turn count, context growth, cache traffic, a priced cost floor, tool census, and a wait-share estimate, with advisory CHATTY/BLOATED verdicts calibrated to measured risk (tail duration and cost) rather than chattiness.

- ts_of · function · L74-L78 — Parses a log line's bracketed timestamp into a float epoch seconds for duration/gap math.
- scan · function · L81-L112 — Aggregates per-session turn counts, cache tokens, tool wall times, and message maxima from the daily log lines.
- floor_usd · function · L115-L121 — Computes a conservative dollar floor for a session from cache-write (2x input = $4/M) and cache-read ($0.10/M) token counts, deliberately understating cost because in/out tokens are redacted in the log.
- summary_line · function · L124-L142 — Builds the machine-readable audit line, computing duration, fast-gap count, tool wall share, and the risk-anchored verdict from turn/duration/cost thresholds.
- main · function · L145-L158 — Entry point that scans the log and prints either one summary line for the newest session (post-cycle hook) or all sessions with a tool census.
