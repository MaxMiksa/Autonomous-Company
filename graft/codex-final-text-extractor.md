---
name: codex-final-text extractor
slug: codex-final-text-extractor
type: file
sources:
  - path: scripts/core/codex-final-text.py
    hash: 3bc904db8c553fb60846f122faadf8447d3fe045c99b4d47c906c67567c264e4
  - path: tests/test_cycle_metadata.sh
    hash: ed0597fda8cb7dd8c8f45b5dea353e18374e12a7f4b247afab630f455e708c2e
sources_digest: b561ae3aee3fd058651507fdbd1391e6b375a57107df85ff5527e51315aa8fe4
links:
  - to: cycle-metadata-extraction
    relation: implements
    description: Produces the clean summary text used in cycle metadata
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

A companion extractor that converts the Codex CLI's JSONL event stream into clean summary text, ensuring reasoning and thread metadata are not leaked. Non-JSON input is treated as a fallback trigger (exit 1).

## Related

- implements [[cycle-metadata-extraction]] — Produces the clean summary text used in cycle metadata
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
