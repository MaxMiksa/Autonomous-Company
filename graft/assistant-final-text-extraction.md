---
name: Assistant Final-Text Extraction
slug: assistant-final-text-extraction
type: system
sources:
  - path: scripts/core/codex-final-text.py
    hash: 3bc904db8c553fb60846f122faadf8447d3fe045c99b4d47c906c67567c264e4
  - path: scripts/core/jcode-final-text.py
    hash: 8913ac57b8ca910581f28286fbdfb665674ee1a1273a477b39f39d1b02bf4215
sources_digest: 8c86c687652a082aa409b4a8ba8ffb34c64122612918dfab6b3f4384e3425870
links:
  - to: auto-company-loop-orchestration
    relation: uses
    description: >-
      auto-loop.sh calls these to extract the assistant's answer from event
      streams
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

Extracts the complete assistant response from jcode/codex ndjson event streams, because done.text is unreliable (can carry only the final block on tool-using runs). Concatenates all text deltas and prefers the longer of concatenated-deltas vs done.text — a deliberate safety trade-off following the principle that noise is never loss. Mirrored implementations exist for the jcode and codex CLI paths.

## Related

- uses [[auto-company-loop-orchestration]] — auto-loop.sh calls these to extract the assistant's answer from event streams
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
