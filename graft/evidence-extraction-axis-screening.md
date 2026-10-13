---
name: Evidence Extraction & Axis Screening
slug: evidence-extraction-axis-screening
type: system
sources:
  - path: scripts/ops/extract-axis-evidence.py
    hash: 3f3d55a2a285cd52ab3b0d286b1f908b877283bfde69b03e442d10758080f567
sources_digest: 4bf6158710472fff59770fd8e5c297877f60bc810d6cb8cf5efc464a05a6a1b0
links:
  - to: opportunity-analyst-pipeline
    relation: produces
    description: Produces evidence packs consumed by the analyst
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Scripts that extract and validate evidence from discovery-scan markdown: extract-axis-evidence.py extracts every screened axis heading and its body text, replacing a broken shell version that dropped kill reasons and missed 19 axes due to a narrow heading regex, failing closed on any unreadable file, empty body, or heading/body count mismatch. These feed the analyst's evidence packs.

## Related

- produces [[opportunity-analyst-pipeline]] — Produces evidence packs consumed by the analyst
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
