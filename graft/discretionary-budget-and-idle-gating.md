---
name: discretionary budget and idle gating
slug: discretionary-budget-and-idle-gating
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_discretionary_budget.sh
    hash: 32b2f12385f1bf8cc0984fc89d1181074406a1726028d2705d2224759cf6de7e
sources_digest: fac3cbdfc041bb7070379bb73e93b7ffa39b29097ef9b7c4ab684dd159e720a1
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: >-
      Idle flag, 3600s idle interval, $30 cap, and ledger filename live in
      auto-loop.sh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Two spending-control mechanisms in auto-loop.sh: idle detection based on snapshot `DELTA: none` (fails open), and a discretionary daily cap (default $30) that injects a warning line into the prompt once the day's spend reaches the threshold, with exactly two injection sites (one per prompt branch). The ledger sum ignores non-JSON lines and missing files, and the cap comparison uses `>=` so an exact match triggers the warning.

## Related

- part of [[auto-loop-core-engine]] — Idle flag, 3600s idle interval, $30 cap, and ledger filename live in auto-loop.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
