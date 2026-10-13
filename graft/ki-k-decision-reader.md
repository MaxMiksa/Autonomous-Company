---
name: KİK Decision Reader
slug: ki-k-decision-reader
type: file
sources:
  - path: scripts/ops/kik-decision-read.py
    hash: 4f2060cbaaa784433de9720f1e9a3bfb3ba6c06cab00fae0efa0a426e5c926de
sources_digest: d0430e1b2184f3b5ab5ef2ec2df0217a8110eb3508d564651dace20265543677
links:
  - to: external-data-access-airtable-browser-ki-k
    relation: part_of
    description: One of the external data access tools
  - to: ki-k-decision-content-hash-canon
    relation: uses
    description: Dynamically imports decision_text_hash.py for the canonical hash
generator:
  version: 1
covers:
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

kik-decision-read.py fetches a Turkish public procurement (KİK) decision page in a single call and returns a compact digest: decision number/date, meeting/agenda numbers, contracting authority, tender reference, complainant (distinguished from an excluded firm), the operative karar verildi sentence, and the canonical content hash. It uses curl with a browser user-agent (urllib fails TLS on macOS), retries on short/empty responses, and extracts exclusion sentences only after dropping quoted legislation so a quoted article is never mistaken for a real exclusion.

## Related

- part of [[external-data-access-airtable-browser-ki-k]] — One of the external data access tools
- uses [[ki-k-decision-content-hash-canon]] — Dynamically imports decision_text_hash.py for the canonical hash
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
