---
name: Work-window brake & watchdog
slug: work-window-brake-watchdog
type: system
sources:
  - path: scripts/ops/work-window-watchdog.py
    hash: 228677456f5e5634b3c6a9964c8b92e13a4c2e4992154feed8a3334779fd0a5f
  - path: scripts/ops/work-window.py
    hash: 7b39b958c05be0d7242887ae4957cf7e6034f20990d587dbab31471a3365c92a
sources_digest: 67cc49769f751c820e323a57d45bcc4e06c4c7cf0c7523ea66929ea3f3522f2d
links:
  - to: cycle-cost-risk-audit
    relation: uses
    description: >-
      Shares the atomic temp-file+os.replace state-write pattern and
      always-exit-0 discipline with the audit scripts.
  - to: state-snapshot-py-probe
    relation: depends_on
    description: >-
      work-window.py parses the DELTA: line emitted by state-snapshot.py to
      decide whether a tracked surface changed.
generator:
  version: 1
covers:
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

A fail-closed brake plus alarm companion that prevents the auto-loop harness from emitting legitimate-but-harmful EMPTY CYCLE confirmations when a tracked surface change leaves follow-on work orphaned. work-window.py reads the state-snapshot DELTA line, maintains a K-cycle window in logs/work-window.json (atomic tmp+rename), fails open (exit 10) on unparseable delta or corrupt state, and relies on the discretionary-spend cap as the money backstop against a stuck-open window. work-window-watchdog.py detects empty-cycle confirmations while a window is open (narrow EMPTY_RE regex, not generic 'blocked' words, because the brake's escape clause requires enumerating blocked items) and alarms once on crossing a threshold, purely informational and always exit 0.

## Related

- uses [[cycle-cost-risk-audit]] — Shares the atomic temp-file+os.replace state-write pattern and always-exit-0 discipline with the audit scripts.
- depends on [[state-snapshot-py-probe]] — work-window.py parses the DELTA: line emitted by state-snapshot.py to decide whether a tracked surface changed.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
