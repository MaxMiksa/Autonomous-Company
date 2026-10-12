---
name: prompt assembly guardrails
slug: prompt-assembly-guardrails
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_prompt_assembly.sh
    hash: 0cd8e397ee0db20d70eac066f7542b6dbabfec6bdd6d031cdc0e378da04876d6
sources_digest: 3be46e00f072b765ed31bef745af51eb5eef4045999ed1d934c12b53ea9eb540
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: prompt assembly branches live in auto-loop.sh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Every FULL_PROMPT assignment in auto-loop.sh must assemble correctly despite embedded guardrail text: the 'Runtime Guardrails' header, five specific rules (OUTPUT HYGIENE, TURN ECONOMY), expanded cycle counter, turn-feedback slot, pre-run snapshot, and correct XML section order (rules → consensus → snapshot → cycle_orders). A stray double quote in a guardrail previously closed the assignment early causing a production outage that bash -n could not detect; the test extracts each prompt-building branch by line number and evaluates it in a sandboxed bash -c. Deliberately avoids mapfile for macOS bash 3.2 compatibility.

## Related

- part of [[auto-loop-core-engine]] — prompt assembly branches live in auto-loop.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
