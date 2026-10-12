---
name: Cycle cost & risk audit
slug: cycle-cost-risk-audit
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
  - to: turn-bloat-brake-py-escalation
    relation: produces
    description: >-
      turn-audit.py's BLOATED verdict feeds the consecutive-streak counter in
      turn-bloat-brake.py.
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

A set of per-cycle cost and risk auditors that parse jcode NDJSON event streams from logs/cycle-ndjson to produce durable ledgers and verdicts. turn-audit.py classifies sessions as ok/CHATTY/BLOATED anchored to risk (duration and cost) rather than chattiness, deliberately understating cost because in/out tokens are redacted; tool-usage-audit.py powers the cockpit's Tool Analytics panel, deduping on filename+size+mtime (not name alone, since the cycle counter restarts on container restart); web-research-cost.py corrects the naive assumption that a fetch costs once by scoring residual cost as output_tokens × turns_after_it, scoring all tools not just web ones because pre-filtering hid Airtable dumps as the largest context source. All use only the standard library and always exit 0.

## Related

- produces [[turn-bloat-brake-py-escalation]] — turn-audit.py's BLOATED verdict feeds the consecutive-streak counter in turn-bloat-brake.py.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
