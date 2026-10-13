---
name: engine-usage-cost adapter
slug: engine-usage-cost-adapter
type: file
sources:
  - path: tests/test_cost_model_hint.sh
    hash: 88c94116abda50a52133d2f6350eb0a69e2ede2fca34275796eeb8b9dfd4c1ac
sources_digest: edbe3a6a770b598aa2c258da5a2e230f3d41cc4708248675f4cc734d10bd6a1c
links:
  - to: auto-loop-core-engine
    relation: uses
    description: Consumed by the loop for per-cycle cost attribution
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

scripts/core/engine-usage-cost.py computes per-cycle cost from token events, with a 'model hint' mechanism for watchdog-killed cycles where token events exist but no done event arrives. A present done event always overrides any hint to prevent model-substitution attacks; unrecognized hints fall back to conservative unknown-model pricing. Applies 2026-10 list prices with cache-read multipliers (0.05x newer models, 0.10x others).

## Related

- uses [[auto-loop-core-engine]] — Consumed by the loop for per-cycle cost attribution
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
