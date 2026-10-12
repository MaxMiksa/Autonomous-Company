---
name: Registry Merge Invariants
slug: registry-merge-invariants
type: concept
sources:
  - path: scripts/analyst/merge_registry.py
    hash: 55719338148054fff06780400062453a037e4bf10fe5817f04536b5c85ade7d1
sources_digest: 5ff39050e2ffebfcb89290b663b10deb8e198c076c45e5893acf920e54d83301
links:
  - to: opportunity-analyst
    relation: part_of
    description: >-
      Used in pass 2 of the analyst to splice the model-proposed registry
      replacement
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
---
<!-- context:generated:start -->
## Summary

merge_registry.py surgically replaces only the 'live decision state' span of candidate-registry.md (between ## Selected and ## Exhausted patterns / lessons headings) while leaving the ~180KB append-only historical journal byte-identical. Enforces invariants: no candidate ID may disappear, no duplicate axes, and the identity (axis) of active candidates cannot be rewritten — only verdict changes are allowed. Heading matching uses regex on heading text (not whitespace) to survive cosmetic markdown edits; ID extraction anchors to table-cell starts to avoid false positives; and the script proves prefix/suffix byte-identity via exact string slicing and hashes, restoring the original on failure.

## Related

- part of [[opportunity-analyst]] — Used in pass 2 of the analyst to splice the model-proposed registry replacement
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
