---
name: state snapshot
slug: state-snapshot
type: file
sources:
  - path: scripts/ops/state-snapshot.py
    hash: 3112f4632b64a6b531b215ea81ba82b2ceb6436942511f816de94ced3171bfe8
  - path: tests/test_state_snapshot.sh
    hash: 44428d24f7cb21d69c1f03477dd4b07ce31b98c94879131f75d58d146aa08729
sources_digest: b22d6b1127d5b052b726fc0dc5a244376cf2f7f1b8d621a83596632c9199dcd2
links:
  - to: auto-loop-core-engine
    relation: uses
    description: auto-loop consumes the snapshot text including DELTA for idle detection
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

scripts/ops/state-snapshot.py parses human-directive.md and operator-requests.md to produce directive status/sha16, OPREQ open counts, and DELTA change-detection output. A missing ledger prints an error but still exits 0, and errored fields are excluded from the next DELTA. All fields are local since a 2026-08-24 re-charter, with bridge/send/reply fields retired.

## Related

- uses [[auto-loop-core-engine]] — auto-loop consumes the snapshot text including DELTA for idle detection
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
