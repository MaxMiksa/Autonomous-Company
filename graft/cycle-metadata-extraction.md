---
name: cycle metadata extraction
slug: cycle-metadata-extraction
type: concept
sources:
  - path: tests/test_cycle_metadata.sh
    hash: ed0597fda8cb7dd8c8f45b5dea353e18374e12a7f4b247afab630f455e708c2e
  - path: tests/test_mixed_harness.sh
    hash: bd8a1f81df957e0bfdfacf44982a2274a58809d5f9bd8618c64c3efeecb868cc
sources_digest: a2275503526f7c6027a9cae8b0ff17f8e3b22d00e8ccca9ebccabc3e4f7429a8
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: >-
      extract_cycle_metadata() and codex-final-text.py live in
      scripts/core/auto-loop.sh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

extract_cycle_metadata() parses per-cycle CYCLE_TYPE/CYCLE_SUBTYPE/RESULT_TEXT from engine output (Claude JSON, Codex plain-prose, or no-JSON edge). It must never kill the loop/container when Codex is routed through alternation or fallback (APP-240 regression). Companion codex-final-text.py converts the Codex CLI JSONL event stream into clean summary text without leaking reasoning/thread metadata.

## Related

- part of [[auto-loop-core-engine]] — extract_cycle_metadata() and codex-final-text.py live in scripts/core/auto-loop.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
