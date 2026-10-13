---
name: one-shot operator escalation
slug: one-shot-operator-escalation
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_escalation.sh
    hash: 51d700c7d869599d1a6d48913b0097143e7b0c93a520123dd7cf3bb5c8c874fc
sources_digest: 9a02888d0e79f033c09e732b17784d6988a21c256f154df0cba7c291afa174d6
links:
  - to: auto-loop-core-engine
    relation: implements
    description: apply_cycle_escalation() and helpers live in auto-loop.sh.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The APP-238 escalation mechanism: a PENDING directive with a Claude cycle applies model/effort/long-wall-timeout overrides and consumes the escalation exactly once; a DONE directive or Codex-routed cycle refuses and leaves it ARMED; a refusal never burns an approval. Unrelated keys in runtime.env are preserved after consumption.

## Related

- implements [[auto-loop-core-engine]] — apply_cycle_escalation() and helpers live in auto-loop.sh.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
