---
name: prompt transport contract
slug: prompt-transport-contract
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_prompt_transport.sh
    hash: c5df34a0acc0d09b63a231df392960370ab146ceea135b5bcace427223300501
sources_digest: 870b6c17e5ffbd5be63c54b60c9ac12ff9bd3cdbf84fb5299b5ffbc032d0e090
links: []
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Invariant that cycle prompts are transported to engine CLIs via STDIN (codex uses the '-' sentinel) rather than argv, preventing E2BIG failures from Linux's 131072-byte per-argument cap. run_jcode_cycle refuses prompts >=126000 bytes with a named PROMPT-TOO-LARGE reason before spawning, while normal-size prompts pass as the run subcommand's argv.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
