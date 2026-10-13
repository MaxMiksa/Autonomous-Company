---
name: prompt assembly and guardrails
slug: prompt-assembly-and-guardrails
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_prompt_assembly.sh
    hash: 0cd8e397ee0db20d70eac066f7542b6dbabfec6bdd6d031cdc0e378da04876d6
  - path: tests/test_prompt_guardrails.sh
    hash: db057850964c46f60538024a1b3e521d4a4ca01d2671a5ee173522bf85bdf6dc
sources_digest: dae1ca2b1792813bec3ba6b9f0b2c258ae30ce2dd640ded41fcf6218afb376e8
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

Every FULL_PROMPT assignment in auto-loop.sh must assemble correctly despite embedded guardrail text, with a fixed XML section order (rules → consensus → snapshot → cycle_orders) and the 'Runtime Guardrails' header plus five specific rules. A stray double quote previously closed the assignment early causing a production outage that bash -n could not detect. PROMPT.md is held to a 20,480-byte budget with legacy vocabulary (tender, discovery, WTP, candidate-registry, EKAP, GLOBAL_SAFETY) appearing at most twice, and every REQUIRED_PROMPT_GUARDRAILS string must appear byte-identically.

## Related

- part of [[auto-loop-core-engine]] — Prompt-building branches and REQUIRED_PROMPT_GUARDRAILS array live in auto-loop.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
