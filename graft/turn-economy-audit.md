---
name: turn economy & audit
slug: turn-economy-audit
type: system
sources:
  - path: scripts/ops/tool-usage-audit.py
    hash: 73a75d68bab3e0b42e31ad3d268b44a8c7ac168b91c6a8d1b2f1b3cd4cdba975
  - path: scripts/ops/turn-audit.py
    hash: 11d7f3bda3ad3eafbc2874669f8bb2169288e01cba152cc213fd28d51f8cf77f
  - path: scripts/ops/turn-bloat-brake.py
    hash: c4d72b732830311e89db486abb41c8a13a5760ffa043354c953b99a155ff96fb
  - path: tests/test_tool_usage_audit.sh
    hash: 4bdf9378fc2af04ed89fc9559aa1fcc8520846c6847f13302f613ec896bfde6d
  - path: tests/test_turn_audit.sh
    hash: ce3eb2af3fea266a763a0ca266f3c658f8498b604570c229141654d685f6c9e8
  - path: tests/test_turn_bloat_brake.py
    hash: 9599b12fa9480d0058872f2facb8d329c5deac8177df794c41982d955d887a74
sources_digest: a6ea2c373eba08799b2435e54c9e4566f93a6796ebc44a8ccb672166fd23c9f2
links:
  - to: auto-loop-core-engine
    relation: uses
    description: consumes cycle NDJSON event streams produced by the loop
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
  - symbol: newapp
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L15-L18'
  - symbol: rec
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L21-L27'
  - symbol: fb
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L30-L36'
  - symbol: consecutive
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L39-L40'
  - symbol: check
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L43-L46'
---
<!-- context:generated:start -->
## Summary

turn-audit.py implements the turn-economy policy (section 4): session parsing, turn/message counting, cache accounting, verdict thresholds (CHATTY/BLOATED/ok) with boundary values pinned to prevent silent recalibration drift. turn-bloat-brake.py tracks consecutive BLOATED verdicts per app and triggers an alarm and hard feedback after a configurable streak threshold (default K=3), resetting on ok/CHATTY, with TURN_BLOAT_ENABLED kill switch. tool-usage-audit.py categorizes jcode NDJSON tool events with ledger idempotence, re-auditing rewritten cycle files (cycle counter resets on container restart) rather than deduping by filename.

## Related

- uses [[auto-loop-core-engine]] — consumes cycle NDJSON event streams produced by the loop
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
