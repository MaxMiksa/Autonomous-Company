---
name: Opportunity Analyst
slug: opportunity-analyst
type: system
sources:
  - path: scripts/analyst/merge_registry.py
    hash: 55719338148054fff06780400062453a037e4bf10fe5817f04536b5c85ade7d1
  - path: scripts/analyst/opportunity-analyst-jcode.sh
    hash: 44d5ba1f3c85dcd90621856e6db86bd24a0602c8ecbaa9ef36c4018abb28b33b
  - path: scripts/analyst/opportunity-analyst.sh
    hash: a0a766435a1f9e501b97cca96bb30314440de72fd569313488d3b80d5f9c55a5
  - path: scripts/analyst/promote_directive.py
    hash: 9c45147f1730fc30545b94a30428d54e0bd40f04506aa3db00614880ec93d677
sources_digest: 75454ff8bc70f6d13f710afccacb1d257fee5f92de6ec58fe62f123d1a3f7cd5
links:
  - to: autonomous-loop-orchestrator
    relation: produces
    description: Writes human-directive.md that the loop consumes as its directive.
  - to: directive-promotion-gate
    relation: implements
    description: promote_directive.py is the deterministic fail-closed gate.
  - to: directive-writer
    relation: uses
    description: directive_writer.py restores human-directive.md if modified.
  - to: registry-merge-invariants
    relation: implements
    description: merge_registry.py enforces the live-span-only merge invariants.
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

Independent 'second-brain' (APP-221) that analyzes Auto Company's Tender Track portfolio and produces decision reports plus candidate-registry updates. Two implementations: the legacy codex-based opportunity-analyst.sh (gpt-5.6-sol, three passes: draft report, live-span registry merge via merge_registry.py, deterministic promotion gate via promote_directive.py) and the newer jcode-based opportunity-analyst-jcode.sh (claude-opus-5-5, audit-only mode, no registry writes or directive promotion per the 2026-08-24 re-charter). Both never auto-apply directives (snapshot/restore with hash check), avoid passing large file contents as prompt args to prevent E2BIG, and record session IDs to logs for budget exclusion. The jcode variant enforces a 2400-second timeout, a 126KB prompt-size guard, and validates the model against jcode model list to avoid silent fallback.

## Related

- produces [[autonomous-loop-orchestrator]] — Writes human-directive.md that the loop consumes as its directive.
- implements [[directive-promotion-gate]] — promote_directive.py is the deterministic fail-closed gate.
- uses [[directive-writer]] — directive_writer.py restores human-directive.md if modified.
- implements [[registry-merge-invariants]] — merge_registry.py enforces the live-span-only merge invariants.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
