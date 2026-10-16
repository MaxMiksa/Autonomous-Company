---
name: PROMPT.md guardrail budget
slug: prompt-md-guardrail-budget
type: concept
sources:
  - path: tests/test_prompt_guardrails.sh
    hash: db057850964c46f60538024a1b3e521d4a4ca01d2671a5ee173522bf85bdf6dc
sources_digest: 8fa7299c2c6279e6a862dca71c16c1006f9d85d911f7ea0730d8207601f2d29d
links:
  - to: prompt-transport-contract
    relation: validates
    description: >-
      Guards the byte budget and guardrail-string identity that the prompt
      assembly depends on.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

PROMPT.md was reduced from 36,852 to 20,480 bytes; the guardrail strings defined in auto-loop.sh must appear byte-identically in it, legacy vocabulary (tender, discovery, WTP, candidate-registry, EKAP, GLOBAL_SAFETY) may appear at most twice, and the archive docs/tender-archive/prompt-sections-2026-10.md must exist and be non-empty.

## Related

- validates [[prompt-transport-contract]] — Guards the byte budget and guardrail-string identity that the prompt assembly depends on.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
