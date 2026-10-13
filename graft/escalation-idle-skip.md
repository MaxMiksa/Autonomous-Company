---
name: escalation & idle-skip
slug: escalation-idle-skip
type: concept
sources:
  - path: tests/test_escalation.sh
    hash: 51d700c7d869599d1a6d48913b0097143e7b0c93a520123dd7cf3bb5c8c874fc
  - path: tests/test_idle_skip.sh
    hash: 13ce9f0b8801b94a1bc896bd2db53f2fc68c2984b45db8372050ca760e1edb53
sources_digest: 92650f7da774ca056fea11cc3f21d84d8c816f6639d90ee4dd5a5e034fde075a
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: Both mechanisms are functions inside auto-loop.sh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

One-shot operator escalation (APP-238): apply_cycle_escalation() consumes ESCALATE_NEXT_CYCLE exactly once, applies model/effort/timeout overrides only for PENDING directives with Claude cycles, and a refusal leaves it ARMED rather than burning approval. Idle-skip: _idle_skip_due never skips the first cycle of a UTC day, reads the kill switch at call time, always runs the OPREQ ledger step before sleeping, and writes last-full-cycle.date only on success.

## Related

- part of [[auto-loop-core-engine]] — Both mechanisms are functions inside auto-loop.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
