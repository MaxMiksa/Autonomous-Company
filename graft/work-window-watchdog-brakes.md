---
name: work-window & watchdog brakes
slug: work-window-watchdog-brakes
type: system
sources:
  - path: scripts/ops/idle-skip-note.py
    hash: 1d4f853b19cdc9ee94c0fd1136ea67393d04deb36a7563e2720ef15a0631ec98
  - path: scripts/ops/work-window-watchdog.py
    hash: 228677456f5e5634b3c6a9964c8b92e13a4c2e4992154feed8a3334779fd0a5f
  - path: scripts/ops/work-window.py
    hash: fd9dd4d65c12d2d5aefc8358f830da5764f16799b2d34aa97ea3c7c5a289a096
  - path: tests/test_idle_skip.sh
    hash: 13ce9f0b8801b94a1bc896bd2db53f2fc68c2984b45db8372050ca760e1edb53
  - path: tests/test_work_window_watchdog.py
    hash: 43cd4a904f4badbb8ce3a4ee88adff57b790ff6c8067435e361617f37a10de40
  - path: tests/test_work_window.py
    hash: 234b10df540fe8774d445855295b088c68cdb23003bdd95c1c22debbd93a6c5e
sources_digest: aeb3a9cefd5d439796127cadbeb9ad692405ba8b9ed3fcb03a3cc1e84c1f71f9
links:
  - to: auto-loop-core-engine
    relation: uses
    description: >-
      The loop consults work-window and idle-skip before each cycle; idle-skip
      never skips the first cycle of a UTC day and reads the kill switch at call
      time.
generator:
  version: 1
covers:
  - symbol: build_line
    kind: function
    at: 'scripts/ops/idle-skip-note.py:L26-L34'
  - symbol: main
    kind: function
    at: 'scripts/ops/idle-skip-note.py:L37-L89'
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
    at: 'scripts/ops/work-window.py:L59-L63'
  - symbol: _env_int
    kind: function
    at: 'scripts/ops/work-window.py:L66-L73'
  - symbol: _parse_delta
    kind: function
    at: 'scripts/ops/work-window.py:L76-L85'
  - symbol: _read_state
    kind: function
    at: 'scripts/ops/work-window.py:L88-L95'
  - symbol: _write_state
    kind: function
    at: 'scripts/ops/work-window.py:L98-L102'
  - symbol: _line
    kind: function
    at: 'scripts/ops/work-window.py:L105-L115'
  - symbol: main
    kind: function
    at: 'scripts/ops/work-window.py:L118-L191'
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

Empty-cycle brakes and alarms: work-window.py gates whether a cycle proceeds based on DELTA change (10=open, 0=closed) with TTL window, fail-closed on expired/negative-age/corrupt state, kill switch, and special rules (DONE directive pull or auditor-only change does not open; PENDING appends and OPREQ changes do); work-window-watchdog.py detects consecutive empty cycles while the window is open, emitting an alarm only once on crossing the threshold (failed cycles not counted); idle-skip-note.py maintains a one-line-per-day consensus note with running count.

## Related

- uses [[auto-loop-core-engine]] — The loop consults work-window and idle-skip before each cycle; idle-skip never skips the first cycle of a UTC day and reads the kill switch at call time.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
