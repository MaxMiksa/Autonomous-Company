---
name: spending & budget controls
slug: spending-budget-controls
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_discretionary_budget.sh
    hash: 32b2f12385f1bf8cc0984fc89d1181074406a1726028d2705d2224759cf6de7e
  - path: tests/test_tier_ladder_daily.sh
    hash: d0bfb4ace48e1fa9665e17059be3f618b46fda0dcf432544a6bb16c07a3ed8db
sources_digest: bf50292fffc8496b272f5e60ec2df1722baaedc0de0e626d98184f4ca7b57aeb
links:
  - to: auto-loop-core-engine
    relation: implements
    description: These controls are implemented inside auto-loop.sh.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Cross-cutting spending-control mechanisms: the discretionary daily cap injects a warning line into the prompt once the day's spend reaches a threshold (default $30, >= comparison so exact match triggers), idle detection based on snapshot text 'DELTA: none' fails open, and apply_tier_ladder() selects per-engine tiers from daily budget (per-engine independence, MODEL_LABEL on Codex-routed cycles, combined model:effort rung syntax). The ledger is discretionary-spend.ndjson, summed for today's UTC date, skipping malformed lines.

## Related

- implements [[auto-loop-core-engine]] — These controls are implemented inside auto-loop.sh.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
