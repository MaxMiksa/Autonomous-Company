---
name: spending control & tier ladder
slug: spending-control-tier-ladder
type: concept
sources:
  - path: tests/test_discretionary_budget.sh
    hash: 32b2f12385f1bf8cc0984fc89d1181074406a1726028d2705d2224759cf6de7e
  - path: tests/test_tier_ladder_daily.sh
    hash: d0bfb4ace48e1fa9665e17059be3f618b46fda0dcf432544a6bb16c07a3ed8db
sources_digest: e553e25ff4646853b3da6ed85cfa1ef22fe9c1e0f2549f87ecfa405017c7d256
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: Implemented as shell fragments inside auto-loop.sh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Multiple layered spending mechanisms in auto-loop.sh: idle detection (DELTA: none snapshot, fails open), a discretionary daily cap that injects a warning line into the prompt at >= threshold, and apply_tier_ladder() selecting model/effort tiers from TOTAL_DAILY_BUDGET_USD with per-engine independence (BG_CLAUDE_DAILY vs BG_CODEX_DAILY). The cap comparison uses >= so an exact match triggers; the ledger sum ignores malformed lines and missing files.

## Related

- part of [[auto-loop-core-engine]] — Implemented as shell fragments inside auto-loop.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
