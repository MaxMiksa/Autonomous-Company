---
name: engine usage cost adapter
slug: engine-usage-cost-adapter
type: system
sources:
  - path: scripts/core/engine-usage-cost.py
    hash: ed2abe259894787b3b28b7e9e9597f1bdfb7bbaf8b3aa9fdf47db72e2473da5f
  - path: tests/test_cost_model_hint.sh
    hash: 88c94116abda50a52133d2f6350eb0a69e2ede2fca34275796eeb8b9dfd4c1ac
sources_digest: c0eacf67ffd9c5c1fc325d7e7df01e64ceb517ed85fad05b9d16b354ff4f185f
links: []
generator:
  version: 1
covers:
  - symbol: _n
    kind: function
    at: 'scripts/core/engine-usage-cost.py:L75-L78'
  - symbol: cost_for
    kind: function
    at: 'scripts/core/engine-usage-cost.py:L81-L123'
  - symbol: main
    kind: function
    at: 'scripts/core/engine-usage-cost.py:L126-L204'
---
<!-- context:generated:start -->
## Summary

scripts/core/engine-usage-cost.py adapts engine usage events into cost rows, with a 'model hint' mechanism for watchdog-killed cycles where token events exist but no done event arrives. A present done event always overrides any hint to prevent model-substitution attacks; unrecognized hints fall back to conservative pricing. Cache read multipliers are 0.05x for newer models and uniform 0.10x for others against the 2026-10 list-price table.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
