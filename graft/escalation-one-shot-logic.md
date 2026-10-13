---
name: escalation one-shot logic
slug: escalation-one-shot-logic
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_escalation.sh
    hash: 51d700c7d869599d1a6d48913b0097143e7b0c93a520123dd7cf3bb5c8c874fc
sources_digest: 9a02888d0e79f033c09e732b17784d6988a21c256f154df0cba7c291afa174d6
links: []
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

One-shot operator escalation (APP-238): an armed escalation is consumed exactly once on a PENDING directive with a Claude cycle (model override, effort override, long wall timeout), and a refusal leaves it ARMED rather than burning approval. Unrelated keys in runtime.env are preserved after consumption.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
