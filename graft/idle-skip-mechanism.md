---
name: idle-skip mechanism
slug: idle-skip-mechanism
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: scripts/ops/idle-skip-note.py
    hash: 1d4f853b19cdc9ee94c0fd1136ea67393d04deb36a7563e2720ef15a0631ec98
  - path: tests/test_idle_skip.sh
    hash: 13ce9f0b8801b94a1bc896bd2db53f2fc68c2984b45db8372050ca760e1edb53
sources_digest: ffd2ea6db3f676a4f4c32eb45c35e95cc321081c793a585e546455320501da64
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: the skip branch lives in auto-loop.sh
  - to: operator-request-notification-system
    relation: uses
    description: always runs the OPREQ ledger step before sleeping
generator:
  version: 1
covers:
  - symbol: build_line
    kind: function
    at: 'scripts/ops/idle-skip-note.py:L26-L34'
  - symbol: main
    kind: function
    at: 'scripts/ops/idle-skip-note.py:L37-L89'
---
<!-- context:generated:start -->
## Summary

The idle-skip branch in auto-loop.sh skips cycles when idle: never calls a model, always runs the operator_request_notify.py OPREQ ledger step before sleeping, writes last-full-cycle.date only on success, and the first cycle of a UTC day is never skipped. The kill switch IDLE_SKIP_ENABLED is read at call time from runtime.env. The consensus note (idle-skip-note.py) maintains one line per day with a running count and first-skip start time.

## Related

- part of [[auto-loop-core-engine]] — the skip branch lives in auto-loop.sh
- uses [[operator-request-notification-system]] — always runs the OPREQ ledger step before sleeping
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
