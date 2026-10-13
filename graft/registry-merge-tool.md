---
name: Registry Merge Tool
slug: registry-merge-tool
type: file
sources:
  - path: scripts/analyst/merge_registry.py
    hash: 55719338148054fff06780400062453a037e4bf10fe5817f04536b5c85ade7d1
sources_digest: 5ff39050e2ffebfcb89290b663b10deb8e198c076c45e5893acf920e54d83301
links:
  - to: opportunity-analyst-codex
    relation: part_of
    description: Pass-2 of the analyst pipeline.
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

Deterministic PASS-2 merge tool surgically replacing only the 'live decision state' span of a large markdown registry (between ## Selected and ## Exhausted patterns / lessons headings) while leaving the ~180KB append-only historical journal byte-identical. Enforces invariants: no candidate ID may disappear, no duplicate axes, identity (axis) of active candidates cannot be rewritten — only verdict changes allowed. Heading matching via regex on heading text (not whitespace) to survive cosmetic edits; ID extraction anchored to cell starts to avoid prose false positives; file-reference dereference (@/path) resolves pointer without relaxing checks. Fail-closed exit 0 with BLOCKED:/MERGED: stdout plus read-back verification and restoration on failure. Never trusts model instruction-following — proves prefix/suffix byte-identity via exact string slicing and hashes.

## Related

- part of [[opportunity-analyst-codex]] — Pass-2 of the analyst pipeline.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
