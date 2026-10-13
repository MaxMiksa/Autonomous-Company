---
name: Cycle Cost & Turn Auditing
slug: cycle-cost-turn-auditing
type: system
sources:
  - path: scripts/ops/tool-usage-audit.py
    hash: 73a75d68bab3e0b42e31ad3d268b44a8c7ac168b91c6a8d1b2f1b3cd4cdba975
  - path: scripts/ops/turn-audit.py
    hash: 11d7f3bda3ad3eafbc2874669f8bb2169288e01cba152cc213fd28d51f8cf77f
  - path: scripts/ops/web-research-cost.py
    hash: 24d7735b6dc6defa0f80e75aeee37a13a40d4df43e9b38539be02df6fe23cbf2
sources_digest: c8968d4a92fb954bba97ab7bc59ff4bf56c500b805d69ebac4254f883b78a6f3
links:
  - to: cycle-escalation-brakes
    relation: uses
    description: turn-audit.py's BLOATED verdict feeds turn-bloat-brake.py's streak counter
generator:
  version: 1
covers:
  - symbol: calls_from_ndjson
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L43-L65'
  - symbol: categorize
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L68-L121'
  - symbol: main
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L124-L251'
  - symbol: dump
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L177-L190'
  - symbol: ts_of
    kind: function
    at: 'scripts/ops/turn-audit.py:L74-L78'
  - symbol: scan
    kind: function
    at: 'scripts/ops/turn-audit.py:L81-L112'
  - symbol: floor_usd
    kind: function
    at: 'scripts/ops/turn-audit.py:L115-L121'
  - symbol: summary_line
    kind: function
    at: 'scripts/ops/turn-audit.py:L124-L142'
  - symbol: main
    kind: function
    at: 'scripts/ops/turn-audit.py:L145-L158'
  - symbol: is_web
    kind: function
    at: 'scripts/ops/web-research-cost.py:L43-L44'
  - symbol: analyse
    kind: function
    at: 'scripts/ops/web-research-cost.py:L47-L76'
  - symbol: main
    kind: function
    at: 'scripts/ops/web-research-cost.py:L79-L161'
---
<!-- context:generated:start -->
## Summary

A set of per-cycle and per-session cost/risk auditors that parse jcode NDJSON event streams and logs to measure true spend and detect bloated sessions. web-research-cost.py corrects the naive 'a fetch costs once' assumption by scoring residual cost as output_tokens × turns_after × cache-read tariff, deliberately scoring all tools (not just web) because pre-filtering hid Airtable dumps as the largest context source. turn-audit.py classifies sessions as ok/CHATTY/BLOATED anchored to risk (duration and cost) rather than chattiness, since msgs_max was a redundant signal that doubled false alarms. tool-usage-audit.py maintains a durable per-cycle ledger for the cockpit's Tool Analytics panel, deduping on filename+size+mtime (not name alone, because the cycle counter restarts on container restart).

## Related

- uses [[cycle-escalation-brakes]] — turn-audit.py's BLOATED verdict feeds turn-bloat-brake.py's streak counter
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
