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
      Functions live in auto-loop.sh; codex-final-text.py is a companion
      extractor
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

extract_cycle_metadata() parses per-cycle CYCLE_TYPE/CYCLE_SUBTYPE/RESULT_TEXT from engine output (Codex plain-prose, Claude JSON, no-JSON edge). APP-240 regression: it must never kill the loop/container when Codex is routed through alternation or fallback. A companion extractor codex-final-text.py converts the Codex CLI JSONL event stream into clean summary text without leaking reasoning/thread metadata, treating non-JSON input as a fallback trigger (exit 1).

## Related

- part of [[auto-loop-core-engine]] — Functions live in auto-loop.sh; codex-final-text.py is a companion extractor
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
