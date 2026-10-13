---
name: state snapshot and DELTA
slug: state-snapshot-and-delta
type: system
sources:
  - path: scripts/ops/state-snapshot.py
    hash: 3112f4632b64a6b531b215ea81ba82b2ceb6436942511f816de94ced3171bfe8
  - path: tests/test_state_snapshot.sh
    hash: 44428d24f7cb21d69c1f03477dd4b07ce31b98c94879131f75d58d146aa08729
sources_digest: b22d6b1127d5b052b726fc0dc5a244376cf2f7f1b8d621a83596632c9199dcd2
links:
  - to: auto-loop-core-engine
    relation: produces
    description: The DELTA output drives idle detection and the work window.
  - to: work-window-brake
    relation: produces
    description: DELTA lines are the input to work-window.py's open/close decision.
generator:
  version: 1
covers:
  - symbol: file_sha16
    kind: function
    at: 'scripts/ops/state-snapshot.py:L54-L61'
  - symbol: directive_state
    kind: function
    at: 'scripts/ops/state-snapshot.py:L64-L72'
  - symbol: opreq_open
    kind: function
    at: 'scripts/ops/state-snapshot.py:L75-L87'
  - symbol: wowcar_sources
    kind: function
    at: 'scripts/ops/state-snapshot.py:L90-L104'
  - symbol: main
    kind: function
    at: 'scripts/ops/state-snapshot.py:L107-L166'
---
<!-- context:generated:start -->
## Summary

scripts/ops/state-snapshot.py parses human-directive.md status/sha16, OPREQ open counts, and computes DELTA change-detection (first-run, none, named changes, error exclusion). A missing ledger prints an error but still exits 0, and errored fields are excluded from the next DELTA. All fields are local since a 2026-08-24 re-charter (bridge/send/reply fields retired). The DELTA: none text is the idle-detection signal consumed by auto-loop.sh.

## Related

- produces [[auto-loop-core-engine]] — The DELTA output drives idle detection and the work window.
- produces [[work-window-brake]] — DELTA lines are the input to work-window.py's open/close decision.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
