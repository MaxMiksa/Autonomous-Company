---
name: prompt guardrails and size budget
slug: prompt-guardrails-and-size-budget
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_prompt_guardrails.sh
    hash: db057850964c46f60538024a1b3e521d4a4ca01d2671a5ee173522bf85bdf6dc
sources_digest: 911eaaff43a8f491a7ee0c3a2f292e5318d8102e8f413fef6c01ec27fd87f80f
links: []
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Invariants on PROMPT.md after a size reduction from 36,852 to 20,480 bytes: every REQUIRED_PROMPT_GUARDRAILS string defined in auto-loop.sh appears byte-identically in PROMPT.md, the file stays within the 20,480-byte budget, and legacy vocabulary (tender, discovery, WTP, candidate-registry, EKAP, GLOBAL_SAFETY) appears at most twice. The archive docs/tender-archive/prompt-sections-2026-10.md must exist and be non-empty.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
