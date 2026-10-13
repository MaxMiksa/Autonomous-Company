---
name: registry archive
slug: registry-archive
type: file
sources:
  - path: scripts/ops/registry-archive.py
    hash: 125be575d2da1c70effa433e2eabe55e5e7e7851fc89719651a1520bb76ee651
  - path: tests/test_registry_archive.sh
    hash: 4ca1be679dfb4867f1e05625b59c587e0a40e525f53c35404d535f93017e5c76
sources_digest: 19cec281a0f24ce825491428331ca5006618cbdd419a7fc31cebd53d832015d2
links:
  - to: registry-queue-watch
    relation: uses
    description: Both operate on the candidate registry markdown
generator:
  version: 1
covers:
  - symbol: die
    kind: function
    at: 'scripts/ops/registry-archive.py:L55-L57'
  - symbol: sha
    kind: function
    at: 'scripts/ops/registry-archive.py:L60-L61'
  - symbol: heading_line_starts
    kind: function
    at: 'scripts/ops/registry-archive.py:L64-L65'
  - symbol: protected_span
    kind: function
    at: 'scripts/ops/registry-archive.py:L68-L80'
  - symbol: plan_note_chunks
    kind: function
    at: 'scripts/ops/registry-archive.py:L83-L105'
  - symbol: plan_section_chunks
    kind: function
    at: 'scripts/ops/registry-archive.py:L108-L140'
  - symbol: interleave
    kind: function
    at: 'scripts/ops/registry-archive.py:L143-L149'
  - symbol: main
    kind: function
    at: 'scripts/ops/registry-archive.py:L152-L340'
  - symbol: month_of
    kind: function
    at: 'scripts/ops/registry-archive.py:L250-L251'
---
<!-- context:generated:start -->
## Summary

scripts/ops/registry-archive.py archives stale dated sections from a candidate registry markdown file while preserving a protected live span (from `## Selected` through the end of `## Exhausted patterns / lessons`) byte-identical. Dry-run writes nothing; apply moves notes and frozen-pattern sections verbatim into a monthly archive file, leaves undated and non-frozen content untouched, inserts pointer lines, and is idempotent. --check stays silent when nothing is archivable even above threshold; --allow-undated-month can force undated sections into a specified month; frozen-pattern sections inside the protected region are never moved.

## Related

- uses [[registry-queue-watch]] — Both operate on the candidate registry markdown
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
