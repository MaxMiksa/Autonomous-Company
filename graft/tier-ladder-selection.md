---
name: tier ladder selection
slug: tier-ladder-selection
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_tier_ladder_daily.sh
    hash: d0bfb4ace48e1fa9665e17059be3f618b46fda0dcf432544a6bb16c07a3ed8db
sources_digest: 77cbb435ce04efe51b95cf9d62095f0dd2598e0bbf2bc6d0aa0f4ea8a049bc63
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: apply_tier_ladder() lives in auto-loop.sh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Daily-budget-based tier selection (APP-263) reads TOTAL_DAILY_BUDGET_USD, BG_CLAUDE_DAILY, BG_CODEX_DAILY and tier ladder strings, selecting tiers per engine independently so one engine's spend never affects the other's tier. Supports combined `model:effort` rung syntax and MODEL_LABEL on Codex-routed cycles. The function only reads budget-gate variables, never computes them.

## Related

- part of [[auto-loop-core-engine]] — apply_tier_ladder() lives in auto-loop.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
