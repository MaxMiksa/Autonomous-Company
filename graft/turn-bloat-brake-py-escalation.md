---
name: turn-bloat-brake.py escalation
slug: turn-bloat-brake-py-escalation
type: file
sources:
  - path: scripts/ops/turn-bloat-brake.py
    hash: c4d72b732830311e89db486abb41c8a13a5760ffa043354c953b99a155ff96fb
sources_digest: 93e6e3b6eb4024ddad8b0fcce6229594bdda3cb1e9d81312e3032e73e31593e6
links:
  - to: cycle-cost-risk-audit
    relation: depends_on
    description: Consumes the BLOATED verdict produced by turn-audit.py.
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

Operational escalation script that tracks consecutive BLOATED cycles (turns>65, dur>=675s, cost>=$5) and emits a hard mandate once a streak crosses a configurable threshold (default 3), complementing the softer per-cycle advisory from turn-audit. --record updates a persistent streak counter and prints a one-time Telegram alarm exactly on the crossing; --feedback prints the HARD_LINE mandate pre-cycle when a streak is active. Always exits 0 so it never fails the harness loop, resets on any non-BLOATED verdict, writes state atomically, and stays quiet after the crossing alarm to avoid spam.

## Related

- depends on [[cycle-cost-risk-audit]] — Consumes the BLOATED verdict produced by turn-audit.py.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
