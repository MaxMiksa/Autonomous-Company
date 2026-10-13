---
name: prompt transport contract
slug: prompt-transport-contract
type: concept
sources:
  - path: tests/test_prompt_transport.sh
    hash: c5df34a0acc0d09b63a231df392960370ab146ceea135b5bcace427223300501
sources_digest: 43a23a58000634ae27009c31c7b63ef340a08366539358de968d0fd597edf089
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: >-
      Enforced inside run_claude_cycle_cli/run_codex_cycle_cli/run_jcode_cycle
      in auto-loop.sh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The invariant that cycle prompts are transported to engine CLIs via STDIN rather than argv, because Linux caps per-argument size at 131072 bytes (E2BIG). Codex uses the '-' sentinel; jcode passes normal-size prompts as the run subcommand's argv but refuses >=126000 bytes with a named PROMPT-TOO-LARGE reason before spawning.

## Related

- part of [[auto-loop-core-engine]] — Enforced inside run_claude_cycle_cli/run_codex_cycle_cli/run_jcode_cycle in auto-loop.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
