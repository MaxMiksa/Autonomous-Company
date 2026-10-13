---
name: prompt content invariants
slug: prompt-content-invariants
type: concept
sources:
  - path: tests/test_prompt_assembly.sh
    hash: 0cd8e397ee0db20d70eac066f7542b6dbabfec6bdd6d031cdc0e378da04876d6
  - path: tests/test_prompt_guardrails.sh
    hash: db057850964c46f60538024a1b3e521d4a4ca01d2671a5ee173522bf85bdf6dc
sources_digest: f3e91686b0a6ec6b59a24fd6e79f1ed9b33e0000b755df77d4841e31c415be20
links:
  - to: auto-loop-core-engine
    relation: validates
    description: >-
      Enforces PROMPT.md budget/guardrail content and FULL_PROMPT assembly
      correctness
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

PROMPT.md must stay within a 20,480-byte budget, contain every REQUIRED_PROMPT_GUARDRAILS string byte-identically, and limit legacy vocabulary (tender, discovery, WTP, candidate-registry, EKAP, GLOBAL_SAFETY) to at most two occurrences. Every FULL_PROMPT assignment in auto-loop.sh must assemble correctly despite embedded guardrail text — a stray double quote previously closed an assignment early causing a production outage that bash -n could not detect.

## Related

- validates [[auto-loop-core-engine]] — Enforces PROMPT.md budget/guardrail content and FULL_PROMPT assembly correctness
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
