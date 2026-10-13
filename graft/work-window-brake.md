---
name: Work-Window Brake
slug: work-window-brake
type: system
sources:
  - path: scripts/ops/work-window-watchdog.py
    hash: 228677456f5e5634b3c6a9964c8b92e13a4c2e4992154feed8a3334779fd0a5f
  - path: scripts/ops/work-window.py
    hash: fd9dd4d65c12d2d5aefc8358f830da5764f16799b2d34aa97ea3c7c5a289a096
  - path: tests/test_work_window_watchdog.py
    hash: 43cd4a904f4badbb8ce3a4ee88adff57b790ff6c8067435e361617f37a10de40
  - path: tests/test_work_window.py
    hash: 234b10df540fe8774d445855295b088c68cdb23003bdd95c1c22debbd93a6c5e
sources_digest: a78c0a00706386eac93cd8b6347268522417f5ce0fba562eb2e68feee1e59bde
links:
  - to: auto-loop-harness
    relation: implements
    description: >-
      Honors the harness contract in scripts/core/auto-loop.sh; the loop gates
      idle-skip on _workwin_open and captures the exit code set-e-safe
  - to: memory-staleness-snapshot-probes
    relation: depends_on
    description: Parses the DELTA line format produced by state-snapshot.py
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

scripts/ops/work-window.py gates whether a cycle should proceed based on DELTA change detection: a changed DELTA opens the window and records opened_at_cycle; an unchanged DELTA stays open only within the TTL window; expired, negative-age (restart), and corrupt states fail closed. Special rules: a DONE directive pull or auditor-only change does not open the window, while PENDING appends and OPREQ changes still do. The companion work-window-watchdog.py detects consecutive empty work cycles while the window is open, emitting an alarm only once when the consecutive count crosses the threshold.

## Related

- implements [[auto-loop-harness]] — Honors the harness contract in scripts/core/auto-loop.sh; the loop gates idle-skip on _workwin_open and captures the exit code set-e-safe
- depends on [[memory-staleness-snapshot-probes]] — Parses the DELTA line format produced by state-snapshot.py
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
