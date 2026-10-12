---
name: Content-Hash Provenance
slug: content-hash-provenance
type: concept
sources:
  - path: scripts/core/decision_text_hash.py
    hash: 790b22fa08940d8d4c5418ec441c98f9d119b33eb718b7cfde81c01c71d94922
  - path: scripts/ops/kik-decision-read.py
    hash: 4f2060cbaaa784433de9720f1e9a3bfb3ba6c06cab00fae0efa0a426e5c926de
sources_digest: 29bce193d5c60bd9e7bf52e9c353d21de59f11e0b8c1f585378295f1c8433681
links:
  - to: ki-k-decision-evidence-pipeline
    relation: validates
    description: The digest's hash is validated against the bridge's recorded value
generator:
  version: 1
covers:
  - symbol: normalize
    kind: function
    at: 'scripts/core/decision_text_hash.py:L54-L60'
  - symbol: digest
    kind: function
    at: 'scripts/core/decision_text_hash.py:L63-L65'
  - symbol: fetch
    kind: function
    at: 'scripts/core/decision_text_hash.py:L68-L96'
  - symbol: main
    kind: function
    at: 'scripts/core/decision_text_hash.py:L99-L112'
  - symbol: _hasher
    kind: function
    at: 'scripts/ops/kik-decision-read.py:L45-L51'
  - symbol: fetch
    kind: function
    at: 'scripts/ops/kik-decision-read.py:L54-L67'
  - symbol: text_of
    kind: function
    at: 'scripts/ops/kik-decision-read.py:L70-L73'
  - symbol: first
    kind: function
    at: 'scripts/ops/kik-decision-read.py:L76-L78'
  - symbol: field
    kind: function
    at: 'scripts/ops/kik-decision-read.py:L81-L89'
  - symbol: read
    kind: function
    at: 'scripts/ops/kik-decision-read.py:L92-L131'
  - symbol: main
    kind: function
    at: 'scripts/ops/kik-decision-read.py:L134-L159'
---
<!-- context:generated:start -->
## Summary

The invariant that a content hash is only comparable if produced by the single canonical normalizer (decision_text_hash.py), because raw HTML from the ASP.NET endpoint varies by client. The normalization order is load-bearing at every step (decode, drop script/style, tag-to-space, entity-unescape after tag removal, NBSP mapping, whitespace collapse) and the hash includes the character count. A hash produced any other way must not be written to the bridge — a lesson from a 2026-07-29 incident where an underdetermined spec caused a legitimate evidence quarantine.

## Related

- validates [[ki-k-decision-evidence-pipeline]] — The digest's hash is validated against the bridge's recorded value
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
