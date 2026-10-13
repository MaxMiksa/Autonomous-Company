---
name: idle-skip mechanism
slug: idle-skip-mechanism
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: scripts/ops/idle-skip-note.py
    hash: 1d4f853b19cdc9ee94c0fd1136ea67393d04deb36a7563e2720ef15a0631ec98
  - path: tests/test_discretionary_budget.sh
    hash: 32b2f12385f1bf8cc0984fc89d1181074406a1726028d2705d2224759cf6de7e
  - path: tests/test_idle_skip.sh
    hash: 13ce9f0b8801b94a1bc896bd2db53f2fc68c2984b45db8372050ca760e1edb53
sources_digest: f52f6ab81f487841590ca905b147b1156c694879649fa7e09cce28e0432e3ba8
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: _idle_skip_due() and the skip branch live in auto-loop.sh
  - to: operator-request-notify
    relation: uses
    description: >-
      The skip branch runs operator_request_notify.py OPREQ ledger step before
      sleeping
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

The idle-skip branch never calls a model, always runs the operator_request_notify.py OPREQ ledger step before sleeping, and writes last-full-cycle.date only on success. The first cycle of a UTC day is never skipped, the kill switch (IDLE_SKIP_ENABLED from runtime.env) is read at call time, and the consensus note maintains one line per day with a running count and first-skip start time. Idle detection is based on the snapshot text `DELTA: none` and fails open (unavailable snapshot treated as not idle).

## Related

- part of [[auto-loop-core-engine]] — _idle_skip_due() and the skip branch live in auto-loop.sh
- uses [[operator-request-notify]] — The skip branch runs operator_request_notify.py OPREQ ledger step before sleeping
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
