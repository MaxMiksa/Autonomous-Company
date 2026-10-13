# scripts/ops/web-research-cost.py · [[cycle-cost-risk-audits]] [[cycle-ndjson-logs]]

Measures the real token cost of web research cycles by computing residual re-read cost (output tokens x turns remaining) from kept ndjson streams.

- is_web · function · L43-L44 — Classifies a tool name as external-content-pulling (webfetch/websearch or browseros-prefixed) so cost analysis can separate web from local tools.
- analyse · function · L47-L76 — Parses one cycle ndjson stream into a turn count and per-call tool name/output-byte/turn records, skipping malformed lines.
- main · function · L79-L161 — Aggregates all cycles into per-tool and per-call residual re-read cost estimates and prints the rankings that justify the cost argument.
