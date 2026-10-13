---
name: Opportunity Analyst (Codex)
slug: opportunity-analyst-codex
type: system
sources:
  - path: scripts/analyst/opportunity-analyst.sh
    hash: a0a766435a1f9e501b97cca96bb30314440de72fd569313488d3b80d5f9c55a5
sources_digest: da007f9034018dbd0503170144e8be4cae497ce9a604927f47722d34c5692a01
links:
  - to: directive-promotion-gate
    relation: uses
    description: Pass-3 decides if the report's proposed directive text may be applied.
  - to: directive-writer
    relation: uses
    description: Safe restore of human-directive.md.
  - to: registry-merge-tool
    relation: uses
    description: Pass-2 extracts and splices the live span of candidate-registry.md.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Independent 'second-brain' (APP-221) invoking OpenAI Codex (gpt-5.6-sol, effort high) with the autocompany-opportunity-director skill to analyze the Tender Track portfolio. Three passes: (1) write full report to analysis-directive.md (draft only, never auto-applied), (2) extract live span of candidate-registry.md via merge_registry.py, ask Codex to propose replacement for that span only, splice back with invariant checks, (3) deterministic promotion gate via promote_directive.py. Never auto-applies directives (snapshot/restore with hash check); avoids passing large file contents as prompt args (E2BIG); preserves registry historical journal by only editing live span; records Codex thread IDs to analyst-codex-sessions.log for budget exclusion. Runs as user app with CODEX_HOME on persistent volume, danger-full-access sandbox.

## Related

- uses [[directive-promotion-gate]] — Pass-3 decides if the report's proposed directive text may be applied.
- uses [[directive-writer]] — Safe restore of human-directive.md.
- uses [[registry-merge-tool]] — Pass-2 extracts and splices the live span of candidate-registry.md.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
