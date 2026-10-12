---
name: Engine usage cost adapter
slug: engine-usage-cost-adapter
type: file
sources:
  - path: tests/test_cost_model_hint.sh
    hash: 88c94116abda50a52133d2f6350eb0a69e2ede2fca34275796eeb8b9dfd4c1ac
sources_digest: edbe3a6a770b598aa2c258da5a2e230f3d41cc4708248675f4cc734d10bd6a1c
links:
  - to: cycle-cost-risk-audit
    relation: uses
    description: Provides the cost figures the audit scripts consume.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

scripts/core/engine-usage-cost.py computes cost from cycle NDJSON, with a 'model hint' mechanism handling watchdog-killed cycles where token events exist but no done event arrives. A present done event always overrides any hint to prevent model-substitution attacks; no hint defaults to a conservative unknown-model row; unrecognized hints fall back to conservative pricing. Applies 2026-10 list prices with cache read multipliers (0.05x for newer models, uniform 0.10x for others).

## Related

- uses [[cycle-cost-risk-audit]] — Provides the cost figures the audit scripts consume.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
