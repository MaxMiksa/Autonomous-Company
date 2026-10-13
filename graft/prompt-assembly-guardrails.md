---
name: prompt assembly & guardrails
slug: prompt-assembly-guardrails
type: concept
sources:
  - path: tests/test_prompt_assembly.sh
    hash: 0cd8e397ee0db20d70eac066f7542b6dbabfec6bdd6d031cdc0e378da04876d6
  - path: tests/test_prompt_guardrails.sh
    hash: db057850964c46f60538024a1b3e521d4a4ca01d2671a5ee173522bf85bdf6dc
sources_digest: f3e91686b0a6ec6b59a24fd6e79f1ed9b33e0000b755df77d4841e31c415be20
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: >-
      Prompt-building branches and REQUIRED_PROMPT_GUARDRAILS array live in
      auto-loop.sh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Every FULL_PROMPT assignment in auto-loop.sh must assemble correctly despite embedded guardrail text, with a specific XML section order (rules → consensus → snapshot → cycle_orders) and five required rules. A stray double quote previously closed the assignment early causing a production outage that bash -n could not detect. PROMPT.md is held to a 20,480-byte budget with every REQUIRED_PROMPT_GUARDRAILS string byte-identical, and legacy vocabulary (tender, discovery, WTP, candidate-registry, EKAP, GLOBAL_SAFETY) appears at most twice.

## Related

- part of [[auto-loop-core-engine]] — Prompt-building branches and REQUIRED_PROMPT_GUARDRAILS array live in auto-loop.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
