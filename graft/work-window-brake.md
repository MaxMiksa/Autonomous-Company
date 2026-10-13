---
name: Work-Window Brake
slug: work-window-brake
type: system
sources:
  - path: scripts/ops/work-window-watchdog.py
    hash: 228677456f5e5634b3c6a9964c8b92e13a4c2e4992154feed8a3334779fd0a5f
  - path: scripts/ops/work-window.py
    hash: fd9dd4d65c12d2d5aefc8358f830da5764f16799b2d34aa97ea3c7c5a289a096
sources_digest: a1a7830b5cb58e843d9817ff7866727002fa09c63e73475dcf0d7dc274d985cc
links:
  - to: harness-loop-core
    relation: implements
    description: >-
      Exits 10 with an injection line telling the model to advance exactly one
      Next Action item or enumerate blockers; wired into auto-loop.sh.
  - to: state-staleness-probes
    relation: uses
    description: >-
      Parses the DELTA line emitted by state-snapshot.py to detect surface
      changes.
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
---
<!-- context:generated:start -->
## Summary

A fail-closed brake and its alarm companion that prevent the auto-loop harness from emitting empty-cycle confirmations when a tracked surface change has orphaned follow-on work. work-window.py parses the state-snapshot DELTA line, implements two operator-decision rules (directive DONE-only changes close the window; auditor-only changes neither open nor close it), fails open on unreadable state, and caps spend via a TTL. work-window-watchdog.py detects empty-cycle confirmations while a window is open using deliberately narrow regex phrasings (not generic 'blocked' words) because the brake's escape clause requires enumerating blocked items.

## Related

- implements [[harness-loop-core]] — Exits 10 with an injection line telling the model to advance exactly one Next Action item or enumerate blockers; wired into auto-loop.sh.
- uses [[state-staleness-probes]] — Parses the DELTA line emitted by state-snapshot.py to detect surface changes.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
