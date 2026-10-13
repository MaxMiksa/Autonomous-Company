---
name: engine-usage-cost adapter
slug: engine-usage-cost-adapter
type: file
sources:
  - path: scripts/core/engine-usage-cost.py
    hash: ed2abe259894787b3b28b7e9e9597f1bdfb7bbaf8b3aa9fdf47db72e2473da5f
  - path: tests/test_cost_model_hint.sh
    hash: 88c94116abda50a52133d2f6350eb0a69e2ede2fca34275796eeb8b9dfd4c1ac
sources_digest: c0eacf67ffd9c5c1fc325d7e7df01e64ceb517ed85fad05b9d16b354ff4f185f
links:
  - to: auto-loop-core-engine
    relation: uses
    description: >-
      Priced by the loop for each cycle; hint mechanism covers cycles killed by
      watchdog.
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

scripts/core/engine-usage-cost.py prices engine cycles against the 2026-10 list-price table, including cache read multipliers (0.05x for newer models, uniform 0.10x for others). Its 'model hint' mechanism handles watchdog-killed cycles where token events exist but no `done` event arrives: no hint defaults to a conservative unknown-model row, a valid hint applies the real tariff while flagging estimated:true, and a present `done` event always overrides any hint to prevent model-substitution attacks.

## Related

- uses [[auto-loop-core-engine]] — Priced by the loop for each cycle; hint mechanism covers cycles killed by watchdog.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
