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
sources_digest: cf149c4008337ecead8ddfe321efdf4f3f7689539c7d47a6746acb772bf80fdc
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: extract_cycle_metadata lives in auto-loop.sh and is called per cycle
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

extract_cycle_metadata() parses engine output (Codex plain-prose, Claude JSON, no-JSON edge) into CYCLE_TYPE/CYCLE_SUBTYPE/RESULT_TEXT, and codex-final-text.py converts the Codex CLI JSONL event stream into clean summary text without leaking reasoning/thread metadata. The critical invariant (APP-240) is that metadata extraction must never kill the loop or container when Codex is routed through alternation or fallback; non-JSON extractor input is a fallback trigger (exit 1).

## Related

- part of [[auto-loop-core-engine]] — extract_cycle_metadata lives in auto-loop.sh and is called per cycle
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
