---
name: prompt transport contract
slug: prompt-transport-contract
type: concept
sources:
  - path: tests/test_prompt_assembly.sh
    hash: 0cd8e397ee0db20d70eac066f7542b6dbabfec6bdd6d031cdc0e378da04876d6
  - path: tests/test_prompt_guardrails.sh
    hash: db057850964c46f60538024a1b3e521d4a4ca01d2671a5ee173522bf85bdf6dc
  - path: tests/test_prompt_transport.sh
    hash: c5df34a0acc0d09b63a231df392960370ab146ceea135b5bcace427223300501
sources_digest: d38ec7e042fa7a49ca07dda1c6df2229257c4383c0b8936e8ba01cf853593cd9
links:
  - to: auto-loop-core-engine
    relation: validates
    description: >-
      Tests extract function bodies from auto-loop.sh and run them with stub
      engine binaries to pin the STDIN/argv contract and prompt assembly.
  - to: prompt-md-guardrail-budget
    relation: depends_on
    description: >-
      Every REQUIRED_PROMPT_GUARDRAILS string must appear byte-identically in
      PROMPT.md, which stays within a 20,480-byte budget.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

A hard invariant that cycle prompts are never passed as argv to engine CLIs (Linux 131072-byte per-argument cap causes E2BIG), but via STDIN with codex using the `-` sentinel; jcode refuses oversized prompts with a named reason before spawning. Also covers the prompt-assembly contract: every FULL_PROMPT assignment must assemble correctly despite embedded guardrail text, with exact XML section order (rules → consensus → snapshot → cycle_orders) and the Runtime Guardrails header.

## Related

- validates [[auto-loop-core-engine]] — Tests extract function bodies from auto-loop.sh and run them with stub engine binaries to pin the STDIN/argv contract and prompt assembly.
- depends on [[prompt-md-guardrail-budget]] — Every REQUIRED_PROMPT_GUARDRAILS string must appear byte-identically in PROMPT.md, which stays within a 20,480-byte budget.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
