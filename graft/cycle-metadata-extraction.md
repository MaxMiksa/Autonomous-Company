---
name: cycle metadata extraction
slug: cycle-metadata-extraction
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_cycle_metadata.sh
    hash: ed0597fda8cb7dd8c8f45b5dea353e18374e12a7f4b247afab630f455e708c2e
  - path: tests/test_mixed_harness.sh
    hash: bd8a1f81df957e0bfdfacf44982a2274a58809d5f9bd8618c64c3efeecb868cc
sources_digest: 41c372a61544e37903d76e2cf30c939868aad7751cf5856aa2c205b95737efec
links: []
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Per-cycle attribution of engine, harness, provider, and result text so that mixed-harness loops (claude→jcode, codex→cli) correctly attribute cost and metadata. Per-cycle variables override any global LOOP_HARNESS; stale jcode cost must not leak into subsequent CLI cycles; unmeasured or zero-cost jcode cycles fail and latch.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
