---
name: tier ladder budgeting
slug: tier-ladder-budgeting
type: concept
sources:
  - path: tests/test_tier_ladder_daily.sh
    hash: d0bfb4ace48e1fa9665e17059be3f618b46fda0dcf432544a6bb16c07a3ed8db
sources_digest: 53b1c709d020ad69894bd767f046b6a9adb7a7661c913e24209b19c3dbead38d
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: Function lives in auto-loop.sh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

apply_tier_ladder() (APP-263) selects daily-budget-based tiers per engine independently — one engine's spend never affects the other's tier. Reads TOTAL_DAILY_BUDGET_USD, BG_CLAUDE_DAILY, BG_CODEX_DAILY and tier ladder strings; supports combined model:effort rung syntax and MODEL_LABEL on Codex-routed cycles. The function only reads budget-gate variables, never computes them.

## Related

- part of [[auto-loop-core-engine]] — Function lives in auto-loop.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
