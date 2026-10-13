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
      The transport functions live in auto-loop.sh and are extracted verbatim
      for testing
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The invariant that cycle prompts are transported to engine CLIs via STDIN (codex using the '-' sentinel) rather than as argv arguments, preventing E2BIG failures from Linux's 131072-byte per-argument cap. run_jcode_cycle additionally refuses prompts >=126000 bytes with a named PROMPT-TOO-LARGE reason before spawning. This is pinned by a dedicated regression test that stubs the engine binary to record argv/stdin.

## Related

- part of [[auto-loop-core-engine]] — The transport functions live in auto-loop.sh and are extracted verbatim for testing
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
