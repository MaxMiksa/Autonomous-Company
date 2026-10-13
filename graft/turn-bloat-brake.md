---
name: Turn Bloat Brake
slug: turn-bloat-brake
type: system
sources:
  - path: scripts/ops/turn-bloat-brake.py
    hash: c4d72b732830311e89db486abb41c8a13a5760ffa043354c953b99a155ff96fb
sources_digest: 93e6e3b6eb4024ddad8b0fcce6229594bdda3cb1e9d81312e3032e73e31593e6
links:
  - to: cycle-cost-risk-audits
    relation: depends_on
    description: Consumes the BLOATED verdict produced by turn-audit.py
  - to: telegram-notification-secrets
    relation: uses
    description: Emits the crossing alarm via Telegram
generator:
  version: 1
covers:
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
---
<!-- context:generated:start -->
## Summary

turn-bloat-brake.py is the hard escalation companion to the softer per-cycle turn-audit advisory: it tracks consecutive BLOATED cycles and emits a one-time Telegram alarm exactly on crossing a configurable streak threshold, then prints a HARD_LINE mandate pre-cycle while a streak is active. It always exits 0 so it never fails the harness loop, resets on any non-BLOATED verdict, and writes state atomically.

## Related

- depends on [[cycle-cost-risk-audits]] — Consumes the BLOATED verdict produced by turn-audit.py
- uses [[telegram-notification-secrets]] — Emits the crossing alarm via Telegram
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
