---
name: work window brake
slug: work-window-brake
type: system
sources:
  - path: scripts/ops/work-window-watchdog.py
    hash: 228677456f5e5634b3c6a9964c8b92e13a4c2e4992154feed8a3334779fd0a5f
  - path: scripts/ops/work-window.py
    hash: 7b39b958c05be0d7242887ae4957cf7e6034f20990d587dbab31471a3365c92a
  - path: tests/test_work_window_watchdog.py
    hash: 43cd4a904f4badbb8ce3a4ee88adff57b790ff6c8067435e361617f37a10de40
  - path: tests/test_work_window.py
    hash: d8c97cca8d25af801fd7214e5176acbe222a9d2ba05610141bf1fd1f40a1bff2
sources_digest: 4719487039a4c01cf3949f901a26049919a415cd0340f75be8c2f6b566434d9a
links:
  - to: auto-loop-core-engine
    relation: uses
    description: >-
      The loop consults the work window to decide whether empty cycles are
      acceptable.
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
  - symbol: run
    kind: function
    at: 'tests/test_work_window.py:L21-L42'
  - symbol: check
    kind: function
    at: 'tests/test_work_window.py:L45-L48'
  - symbol: run
    kind: function
    at: 'tests/test_work_window_watchdog.py:L18-L29'
  - symbol: check
    kind: function
    at: 'tests/test_work_window_watchdog.py:L32-L35'
---
<!-- context:generated:start -->
## Summary

work-window.py is the empty-cycle work-window brake: a changed DELTA opens the window (recording opened_at_cycle and reason), no delta with no state stays closed, fresh windows stay open until TTL expiry, negative age (stored opened_at_cycle > current cycle) fails closed, corrupt state or missing DELTA fail open, and WORK_WINDOW_ENABLED=0 forces closed. work-window-watchdog.py is the alarm layer detecting consecutive empty cycles while the window is open, emitting an alarm only once when crossing the threshold (not on every violation), with a 'failed' cycle not counted as a violation and an escape clause for enumerated blockers.

## Related

- uses [[auto-loop-core-engine]] — The loop consults the work window to decide whether empty cycles are acceptable.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
