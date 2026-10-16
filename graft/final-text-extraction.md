---
name: Final-text extraction
slug: final-text-extraction
type: concept
sources:
  - path: scripts/core/codex-final-text.py
    hash: 3bc904db8c553fb60846f122faadf8447d3fe045c99b4d47c906c67567c264e4
  - path: scripts/core/jcode-final-text.py
    hash: 8913ac57b8ca910581f28286fbdfb665674ee1a1273a477b39f39d1b02bf4215
sources_digest: 8c86c687652a082aa409b4a8ba8ffb34c64122612918dfab6b3f4384e3425870
links: []
generator:
  version: 1
covers:
  - symbol: final_text
    kind: function
    at: 'scripts/core/codex-final-text.py:L30-L47'
  - symbol: main
    kind: function
    at: 'scripts/core/codex-final-text.py:L50-L60'
  - symbol: final_text
    kind: function
    at: 'scripts/core/jcode-final-text.py:L30-L48'
  - symbol: main
    kind: function
    at: 'scripts/core/jcode-final-text.py:L51-L61'
---
<!-- context:generated:start -->
## Summary

The invariant that assistant final text must be reconstructed from event streams rather than trusted from a single field, because done.text/done.usage can silently truncate on tool-using runs. Both codex and jcode extractors concatenate all agent_message/text_delta events and prefer the longer of two readings, following the principle that noise is never loss. This is a direct response to measured failure modes (a 31-event text_delta sequence vs done.text holding only its last paragraph).
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
