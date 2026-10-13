---
name: cycle metadata & prompt transport contract
slug: cycle-metadata-prompt-transport-contract
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: scripts/core/codex-final-text.py
    hash: 3bc904db8c553fb60846f122faadf8447d3fe045c99b4d47c906c67567c264e4
  - path: tests/test_cycle_metadata.sh
    hash: ed0597fda8cb7dd8c8f45b5dea353e18374e12a7f4b247afab630f455e708c2e
  - path: tests/test_prompt_transport.sh
    hash: c5df34a0acc0d09b63a231df392960370ab146ceea135b5bcace427223300501
sources_digest: c408566a2ac1c7e935434fbbab16d96262d4e2fe8421532389f3fa26b4beaff2
links:
  - to: auto-loop-core-engine
    relation: implements
    description: These contracts are implemented by functions inside auto-loop.sh.
generator:
  version: 1
covers:
  - symbol: final_text
    kind: function
    at: 'scripts/core/codex-final-text.py:L30-L47'
  - symbol: main
    kind: function
    at: 'scripts/core/codex-final-text.py:L50-L60'
---
<!-- context:generated:start -->
## Summary

Cross-cutting invariants about how cycle metadata is extracted and how prompts reach engine CLIs. extract_cycle_metadata() must not kill the loop when Codex is routed through alternation/fallback (APP-240 regression), and codex-final-text.py must strip reasoning/thread metadata from the JSONL event stream. Prompts are passed via STDIN (codex uses the `-` sentinel) to avoid E2BIG, and run_jcode_cycle refuses prompts >=126000 bytes with a named PROMPT-TOO-LARGE reason before spawning.

## Related

- implements [[auto-loop-core-engine]] — These contracts are implemented by functions inside auto-loop.sh.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
