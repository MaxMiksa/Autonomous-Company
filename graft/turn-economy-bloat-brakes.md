---
name: turn economy & bloat brakes
slug: turn-economy-bloat-brakes
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
    relation: validates
    description: Verdicts feed back into loop behavior via the bloat brake's hard feedback.
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

Turn-economy policy (section 4) enforcement: turn-audit.py parses daily-log sessions, counts turns/messages, accounts for cache, applies verdict thresholds (CHATTY/BLOATED/ok) with pinned boundary values to prevent silent recalibration drift; turn-bloat-brake.py tracks consecutive BLOATED verdicts per app and triggers an alarm and hard feedback after a configurable streak (default K=3), resetting on ok/CHATTY, suppressing repeat alarms, with a kill switch.

## Related

- validates [[auto-loop-core-engine]] — Verdicts feed back into loop behavior via the bloat brake's hard feedback.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
