---
name: engine-usage-cost model hint
slug: engine-usage-cost-model-hint
type: concept
sources:
  - path: tests/test_cost_model_hint.sh
    hash: 88c94116abda50a52133d2f6350eb0a69e2ede2fca34275796eeb8b9dfd4c1ac
sources_digest: edbe3a6a770b598aa2c258da5a2e230f3d41cc4708248675f4cc734d10bd6a1c
links:
  - to: cycle-metadata-cost-attribution
    relation: produces
    description: >-
      Computes cost_usd for cycles, including estimated rows for watchdog-killed
      cycles.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The engine-usage-cost.py adapter handles watchdog-killed cycles where token events exist but no `done` event arrives. A model hint applies the real tariff while flagging estimated:true; no hint defaults to a conservative unknown-model row; unrecognized hints fall back to conservative pricing; and a present `done` event always overrides any hint to prevent model-substitution attacks. Cache read multipliers are 0.05x for newer models, uniform 0.10x for others.

## Related

- produces [[cycle-metadata-cost-attribution]] — Computes cost_usd for cycles, including estimated rows for watchdog-killed cycles.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
