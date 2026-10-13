---
name: Cycle Cost & Risk Audits
slug: cycle-cost-risk-audits
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
  - to: cycle-ndjson-logs
    relation: uses
    description: >-
      All three parse logs/cycle-ndjson event streams with type fields
      tokens/tool_start/tool_done
  - to: turn-bloat-brake
    relation: produces
    description: turn-audit.py's BLOATED verdict feeds the bloat brake's streak counter
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

A set of per-cycle cost/risk measurement tools that parse jcode NDJSON/log streams. turn-audit.py classifies sessions as ok/CHATTY/BLOATED anchored to risk (duration and cost) rather than chattiness, using a conservative cost floor because in/out tokens are redacted. web-research-cost.py corrects the naive assumption that a fetch costs once — each tool result is re-read every subsequent turn, so cost scales with output size times remaining turns, and it deliberately scores all tools because pre-filtering hid Airtable dumps as the largest context source. tool-usage-audit.py is a durable ledger powering the cockpit's Tool Analytics panel.

## Related

- uses [[cycle-ndjson-logs]] — All three parse logs/cycle-ndjson event streams with type fields tokens/tool_start/tool_done
- produces [[turn-bloat-brake]] — turn-audit.py's BLOATED verdict feeds the bloat brake's streak counter
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
