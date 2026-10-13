---
name: Registry Merge & Promotion Gates
slug: registry-merge-promotion-gates
type: system
sources:
  - path: scripts/analyst/merge_registry.py
    hash: 55719338148054fff06780400062453a037e4bf10fe5817f04536b5c85ade7d1
  - path: scripts/analyst/promote_directive.py
    hash: 9c45147f1730fc30545b94a30428d54e0bd40f04506aa3db00614880ec93d677
sources_digest: 9ae44d2dafc5b6983477fe5ce3cd6a132011b762f223203e35cbf3e564fa38e9
links:
  - to: directive-registry-management
    relation: validates
    description: >-
      Validates candidate-registry.md and human-directive.md integrity before
      and after analyst writes.
  - to: opportunity-analyst-pipeline
    relation: implements
    description: >-
      Enforces the promotion gate and registry splice invariants the analyst
      pipeline depends on.
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

Deterministic, fail-closed Python gates that protect the append-only candidate registry and human directive from model error. merge_registry.py surgically replaces only the 'live decision state' span of candidate-registry.md (between ## Selected and ## Exhausted patterns headings) while leaving the ~180KB historical journal byte-identical, enforcing invariants: no candidate ID may disappear, no duplicate axes, and the identity of active candidates cannot be rewritten. promote_directive.py blocks promotion on any risk-keyword hit (outreach, payment, deployment, legal, external writes), missing verdict keywords, or escalation language near the current Active Validation ID, requires the live directive Status to be DONE, backs up before writing, and verifies via read-back and diff. Both always exit 0 with BLOCKED:/MERGED:/PROMOTED: stdout and log hashes for operator monitoring.

## Related

- validates [[directive-registry-management]] — Validates candidate-registry.md and human-directive.md integrity before and after analyst writes.
- implements [[opportunity-analyst-pipeline]] — Enforces the promotion gate and registry splice invariants the analyst pipeline depends on.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
