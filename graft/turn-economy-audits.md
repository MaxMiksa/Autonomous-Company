---
name: turn economy audits
slug: turn-economy-audits
type: system
sources:
  - path: scripts/ops/turn-audit.py
    hash: 11d7f3bda3ad3eafbc2874669f8bb2169288e01cba152cc213fd28d51f8cf77f
  - path: scripts/ops/turn-bloat-brake.py
    hash: c4d72b732830311e89db486abb41c8a13a5760ffa043354c953b99a155ff96fb
  - path: tests/test_turn_audit.sh
    hash: ce3eb2af3fea266a763a0ca266f3c658f8498b604570c229141654d685f6c9e8
  - path: tests/test_turn_bloat_brake.py
    hash: 9599b12fa9480d0058872f2facb8d329c5deac8177df794c41982d955d887a74
sources_digest: 9e8497d1deda9227e77694cabbf89f9413eaae2cf3f10f900481f9a2dd878a1a
links:
  - to: auto-loop-core-engine
    relation: uses
    description: auto-loop feeds daily-log lines to turn-audit and consumes bloat feedback
generator:
  version: 1
covers:
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

The turn-economy policy (section 4) implemented by turn-audit.py and turn-bloat-brake.py. turn-audit.py parses daily-log lines to count turns/messages, account for cache, and apply verdict thresholds (CHATTY, BLOATED, ok) with boundary values pinned (55 vs 56 turns, 66 turns, duration-based bloating) to prevent silent recalibration drift. turn-bloat-brake.py tracks consecutive BLOATED verdicts per app and triggers an alarm and hard feedback after a configurable streak threshold (default K=3, overridable via TURN_BLOAT_STREAK), resetting on ok/CHATTY, suppressing repeat alarms, and honoring TURN_BLOAT_ENABLED=0 kill switch.

## Related

- uses [[auto-loop-core-engine]] — auto-loop feeds daily-log lines to turn-audit and consumes bloat feedback
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
