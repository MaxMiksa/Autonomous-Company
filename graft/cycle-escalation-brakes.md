---
name: Cycle Escalation Brakes
slug: cycle-escalation-brakes
type: system
sources:
  - path: scripts/ops/turn-bloat-brake.py
    hash: c4d72b732830311e89db486abb41c8a13a5760ffa043354c953b99a155ff96fb
  - path: scripts/ops/work-window-watchdog.py
    hash: 228677456f5e5634b3c6a9964c8b92e13a4c2e4992154feed8a3334779fd0a5f
  - path: scripts/ops/work-window.py
    hash: 7b39b958c05be0d7242887ae4957cf7e6034f20990d587dbab31471a3365c92a
sources_digest: 536c0739577e86fb7221129fd8842e59a9505c317ee37e3b68dab8f9a6a4eade
links:
  - to: cycle-cost-turn-auditing
    relation: depends_on
    description: Consumes BLOATED verdicts from turn-audit.py to drive the streak counter
  - to: state-snapshot-staleness
    relation: uses
    description: >-
      work-window.py reads the state-snapshot DELTA line on stdin to detect
      surface changes
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
  - symbol: _app_dir
    kind: function
    at: 'scripts/ops/work-window-watchdog.py:L45-L48'
  - symbol: _threshold
    kind: function
    at: 'scripts/ops/work-window-watchdog.py:L51-L57'
  - symbol: _read_state
    kind: function
    at: 'scripts/ops/work-window-watchdog.py:L60-L64'
  - symbol: _write_state
    kind: function
    at: 'scripts/ops/work-window-watchdog.py:L67-L74'
  - symbol: main
    kind: function
    at: 'scripts/ops/work-window-watchdog.py:L77-L125'
  - symbol: _app_dir
    kind: function
    at: 'scripts/ops/work-window.py:L44-L48'
  - symbol: _env_int
    kind: function
    at: 'scripts/ops/work-window.py:L51-L58'
  - symbol: _parse_delta
    kind: function
    at: 'scripts/ops/work-window.py:L61-L70'
  - symbol: _read_state
    kind: function
    at: 'scripts/ops/work-window.py:L73-L80'
  - symbol: _write_state
    kind: function
    at: 'scripts/ops/work-window.py:L83-L87'
  - symbol: _line
    kind: function
    at: 'scripts/ops/work-window.py:L90-L100'
  - symbol: main
    kind: function
    at: 'scripts/ops/work-window.py:L103-L160'
---
<!-- context:generated:start -->
## Summary

Fail-closed operational brakes and watchdogs that escalate when the auto-loop emits harmful patterns, complementing per-cycle advisories. turn-bloat-brake.py tracks consecutive BLOATED cycles and emits a one-time hard mandate (persist one milestone, end immediately) exactly on threshold crossing, resetting on any non-BLOATED verdict. work-window.py prevents legitimate-but-harmful EMPTY CYCLE confirmations when a tracked surface change leaves follow-on work orphaned, maintaining a K-cycle window with TTL and failing open (exit 10) on corrupt state. work-window-watchdog.py detects empty-cycle confirmations while a window is open using deliberately narrow regexes (the brake's escape clause requires enumerating blocked items). All always exit 0 so they never fail the harness loop, and write state atomically via temp+os.replace.

## Related

- depends on [[cycle-cost-turn-auditing]] — Consumes BLOATED verdicts from turn-audit.py to drive the streak counter
- uses [[state-snapshot-staleness]] — work-window.py reads the state-snapshot DELTA line on stdin to detect surface changes
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
