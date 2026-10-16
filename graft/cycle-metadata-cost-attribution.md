---
name: cycle metadata & cost attribution
slug: cycle-metadata-cost-attribution
type: concept
sources:
  - path: tests/test_cycle_counter.sh
    hash: ab58cfed1b942c55ff2422535c8904c0292904f40786afc3cb7a66774d635065
  - path: tests/test_cycle_metadata.sh
    hash: ed0597fda8cb7dd8c8f45b5dea353e18374e12a7f4b247afab630f455e708c2e
  - path: tests/test_mixed_harness.sh
    hash: bd8a1f81df957e0bfdfacf44982a2274a58809d5f9bd8618c64c3efeecb868cc
sources_digest: 8c8377775045f0e5357399f3b5644fbeea011fc507b4553c31738769d94d7328
links:
  - to: auto-loop-core-engine
    relation: implements
    description: >-
      extract_cycle_metadata() and run_engine_cycle() in auto-loop.sh produce
      these per-cycle variables and persist costs.
  - to: engine-usage-cost-model-hint
    relation: uses
    description: >-
      Cost attribution relies on the engine-usage-cost adapter's model-hint
      mechanism for watchdog-killed cycles.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Per-cycle metadata (CYCLE_TYPE, CYCLE_SUBTYPE, RESULT_TEXT, harness, provider) and cost must be attributed to the correct engine run, especially in mixed-harness loops (claude→jcode, codex→cli). Stale jcode cost must not leak into subsequent CLI cycles; unmeasured/zero-cost jcode cycles fail and latch; unparseable attempt costs block retries; the REVISE-2 gate A5 persists a claude attempt's cost under its own run ID before a codex retry.

## Related

- implements [[auto-loop-core-engine]] — extract_cycle_metadata() and run_engine_cycle() in auto-loop.sh produce these per-cycle variables and persist costs.
- uses [[engine-usage-cost-model-hint]] — Cost attribution relies on the engine-usage-cost adapter's model-hint mechanism for watchdog-killed cycles.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
