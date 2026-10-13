---
name: Cycle Cost & Bloat Governance
slug: cycle-cost-bloat-governance
type: system
sources:
  - path: scripts/ops/tool-usage-audit.py
    hash: 73a75d68bab3e0b42e31ad3d268b44a8c7ac168b91c6a8d1b2f1b3cd4cdba975
  - path: scripts/ops/turn-audit.py
    hash: 11d7f3bda3ad3eafbc2874669f8bb2169288e01cba152cc213fd28d51f8cf77f
  - path: scripts/ops/turn-bloat-brake.py
    hash: c4d72b732830311e89db486abb41c8a13a5760ffa043354c953b99a155ff96fb
  - path: scripts/ops/web-research-cost.py
    hash: 24d7735b6dc6defa0f80e75aeee37a13a40d4df43e9b38539be02df6fe23cbf2
sources_digest: a90b641f17f3253d99815a2210874e8b1983c4d33d3d297fb02a708f8b04a006
links:
  - to: harness-loop-core
    relation: uses
    description: >-
      All read cycle ndjson/log output produced by the auto-loop harness;
      turn-bloat-brake is wired into auto-loop.sh as a pre-cycle feedback and
      post-cycle record hook.
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
  - symbol: _app
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L25-L26'
  - symbol: _streak_len
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L29-L34'
  - symbol: _load
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L37-L41'
  - symbol: _save
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L44-L51'
  - symbol: main
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L63-L104'
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

A set of per-cycle and cross-cycle auditors that measure and police LLM agent session cost and bloat. turn-audit.py classifies sessions as ok/CHATTY/BLOATED anchored to risk (duration and cost) rather than chattiness, deliberately understating cost because in/out tokens are redacted in the log. turn-bloat-brake.py escalates consecutive BLOATED cycles into a hard mandate once a streak crosses a threshold. web-research-cost.py corrects the naive assumption that a fetch costs once by scoring residual re-read cost across turns, scoring all tools (not just web) because pre-filtering hid Airtable dumps as the largest context source. tool-usage-audit.py maintains a durable per-cycle ledger for the cockpit's Tool Analytics panel, deduping on filename+size+mtime because the cycle counter restarts on container restart.

## Related

- uses [[harness-loop-core]] — All read cycle ndjson/log output produced by the auto-loop harness; turn-bloat-brake is wired into auto-loop.sh as a pre-cycle feedback and post-cycle record hook.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
