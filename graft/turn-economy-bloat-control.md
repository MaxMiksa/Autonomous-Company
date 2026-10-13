---
name: turn economy & bloat control
slug: turn-economy-bloat-control
type: system
sources:
  - path: tests/test_turn_audit.sh
    hash: ce3eb2af3fea266a763a0ca266f3c658f8498b604570c229141654d685f6c9e8
  - path: tests/test_turn_bloat_brake.py
    hash: 9599b12fa9480d0058872f2facb8d329c5deac8177df794c41982d955d887a74
sources_digest: 2e94fa5b7b9400debe79e6c573c421ac60369358f27f55e7554a08b1a2377a5e
links:
  - to: auto-loop-core-engine
    relation: uses
    description: Consumes daily log lines produced by engine cycles
generator:
  version: 1
covers:
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

The turn-economy policy (section 4): turn-audit.py parses daily logs to count turns/messages and cache, applying verdict thresholds (CHATTY, BLOATED, ok) with boundary values pinned to prevent silent recalibration drift (55 vs 56 turns, 66 turns, duration-based bloating). turn-bloat-brake.py tracks consecutive BLOATED verdicts per app and triggers an alarm plus hard feedback after a configurable streak (default K=3, overridable via TURN_BLOAT_STREAK), resetting on ok/CHATTY, suppressing repeat alarms, with a TURN_BLOAT_ENABLED=0 kill switch. Threshold bars are documented as p80/p90, watchdog proximity, and cost.

## Related

- uses [[auto-loop-core-engine]] — Consumes daily log lines produced by engine cycles
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
