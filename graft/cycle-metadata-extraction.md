---
name: cycle metadata extraction
slug: cycle-metadata-extraction
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: scripts/core/codex-final-text.py
    hash: 3bc904db8c553fb60846f122faadf8447d3fe045c99b4d47c906c67567c264e4
  - path: tests/test_cycle_metadata.sh
    hash: ed0597fda8cb7dd8c8f45b5dea353e18374e12a7f4b247afab630f455e708c2e
  - path: tests/test_mixed_harness.sh
    hash: bd8a1f81df957e0bfdfacf44982a2274a58809d5f9bd8618c64c3efeecb868cc
sources_digest: 1d3ea068ed0fd08af5c30459f48a3c186ebd8e91055aa598a9e0dd0f46cfc867
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: extract_cycle_metadata() and run_engine_cycle() live in auto-loop.sh
  - to: codex-final-text-extractor
    relation: uses
    description: >-
      codex-final-text.py converts the Codex CLI JSONL event stream into clean
      summary text without leaking reasoning/thread metadata
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

The invariant that each cycle's metadata (CYCLE_TYPE, CYCLE_SUBTYPE, RESULT_TEXT, CYCLE_HARNESS_USED, CYCLE_PROVIDER_USED) is parsed and attributed per-cycle, overriding any global LOOP_HARNESS, and that parsing must never kill the loop when Codex is routed through alternation or fallback. Cost attribution must not leak a stale jcode cost into a subsequent CLI cycle, and unmeasured/zero-cost jcode cycles fail and latch.

## Related

- part of [[auto-loop-core-engine]] — extract_cycle_metadata() and run_engine_cycle() live in auto-loop.sh
- uses [[codex-final-text-extractor]] — codex-final-text.py converts the Codex CLI JSONL event stream into clean summary text without leaking reasoning/thread metadata
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
