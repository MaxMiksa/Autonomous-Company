---
name: Opportunity Analyst
slug: opportunity-analyst
type: system
sources:
  - path: >-
      scripts/analyst/codex-skill/autocompany-opportunity-director/scripts/context7_docs.sh
    hash: 79198378c25b2ff21cf5e4e2eda13f55c29ac806bd7f9d2bb0cba11a6268c447
  - path: scripts/analyst/merge_registry.py
    hash: 55719338148054fff06780400062453a037e4bf10fe5817f04536b5c85ade7d1
  - path: scripts/analyst/opportunity-analyst-jcode.sh
    hash: b3453b9880adcc95bc886501514c4a02c269721ac9ab6da94950a767553cc324
  - path: scripts/analyst/opportunity-analyst.sh
    hash: a0a766435a1f9e501b97cca96bb30314440de72fd569313488d3b80d5f9c55a5
  - path: scripts/analyst/promote_directive.py
    hash: 9c45147f1730fc30545b94a30428d54e0bd40f04506aa3db00614880ec93d677
sources_digest: 886ba5ef5aff8f1d7a216e21355b234744d030b0e741fdd48c667e7341ee054b
links:
  - to: directive-write-gate
    relation: uses
    description: >-
      promote_directive.py and directive_writer.py gate any human-directive.md
      overwrite
  - to: registry-merge-invariants
    relation: implements
    description: merge_registry.py enforces the live-span-only merge with invariant checks
generator:
  version: 1
covers:
  - symbol: identifier_fields
    kind: function
    at: 'scripts/analyst/merge_registry.py:L66-L76'
  - symbol: audit
    kind: function
    at: 'scripts/analyst/merge_registry.py:L79-L82'
  - symbol: blocked
    kind: function
    at: 'scripts/analyst/merge_registry.py:L85-L88'
  - symbol: extract_ids
    kind: function
    at: 'scripts/analyst/merge_registry.py:L91-L105'
  - symbol: extract_axes
    kind: function
    at: 'scripts/analyst/merge_registry.py:L108-L120'
  - symbol: table_rows
    kind: function
    at: 'scripts/analyst/merge_registry.py:L123-L131'
  - symbol: row_identity
    kind: function
    at: 'scripts/analyst/merge_registry.py:L134-L151'
  - symbol: sections
    kind: function
    at: 'scripts/analyst/merge_registry.py:L154-L163'
  - symbol: active_candidates
    kind: function
    at: 'scripts/analyst/merge_registry.py:L166-L186'
  - symbol: normalize_axis
    kind: function
    at: 'scripts/analyst/merge_registry.py:L189-L190'
  - symbol: resolve_span
    kind: function
    at: 'scripts/analyst/merge_registry.py:L193-L232'
  - symbol: _rewind_over_separators
    kind: function
    at: 'scripts/analyst/merge_registry.py:L235-L246'
  - symbol: split_registry
    kind: function
    at: 'scripts/analyst/merge_registry.py:L249-L272'
  - symbol: main
    kind: function
    at: 'scripts/analyst/merge_registry.py:L275-L428'
  - symbol: sha256
    kind: function
    at: 'scripts/analyst/promote_directive.py:L91-L92'
  - symbol: audit
    kind: function
    at: 'scripts/analyst/promote_directive.py:L95-L98'
  - symbol: blocked
    kind: function
    at: 'scripts/analyst/promote_directive.py:L101-L104'
  - symbol: notify
    kind: function
    at: 'scripts/analyst/promote_directive.py:L107-L113'
  - symbol: main
    kind: function
    at: 'scripts/analyst/promote_directive.py:L116-L225'
---
<!-- context:generated:start -->
## Summary

An independent 'second-brain' that invokes an LLM (Codex gpt-5.6-sol or jcode/Claude Opus 5.5) with the autocompany-opportunity-director skill to analyze the Tender Track portfolio and produce a decision report plus a candidate-registry update. Runs three passes: writes a draft report (never auto-applied), extracts and splices only the live span of candidate-registry.md via merge_registry.py with invariant checks, and runs a deterministic promotion gate. Never auto-applies directives (snapshot/restore with hash check), avoids passing large file contents as prompt arguments (E2BIG), and records session IDs to logs for budget exclusion. The jcode variant enforces a 131072-byte argv limit (guarded at 126000) and persists raw ndjson streams for cost calibration.

## Related

- uses [[directive-write-gate]] — promote_directive.py and directive_writer.py gate any human-directive.md overwrite
- implements [[registry-merge-invariants]] — merge_registry.py enforces the live-span-only merge with invariant checks
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
