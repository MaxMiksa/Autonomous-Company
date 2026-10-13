---
name: registry queue watch
slug: registry-queue-watch
type: system
sources:
  - path: scripts/ops/registry-archive.py
    hash: 125be575d2da1c70effa433e2eabe55e5e7e7851fc89719651a1520bb76ee651
  - path: scripts/ops/registry-queue-watch.py
    hash: 0ef6723d089c54ee8272050eb2776ce81af9de986e8f6dc15b065b7bbd913497
  - path: tests/test_registry_archive.sh
    hash: 4ca1be679dfb4867f1e05625b59c587e0a40e525f53c35404d535f93017e5c76
  - path: tests/test_registry_queue_watch.sh
    hash: 0c823a0b115d8fb57d7a64e25cb89f725943078e58504a22aa5306a416ac6668
sources_digest: 041be21891feded98c7048c108896acfbcd3843d06da6b28a7a6e7581bddea17
links:
  - to: outreach-and-send-gating
    relation: uses
    description: Shares the Airtable registry data model and attribution-Held firm concept.
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
  - symbol: api_key
    kind: function
    at: 'scripts/ops/registry-queue-watch.py:L48-L58'
  - symbol: fetch
    kind: function
    at: 'scripts/ops/registry-queue-watch.py:L61-L77'
  - symbol: main
    kind: function
    at: 'scripts/ops/registry-queue-watch.py:L80-L215'
---
<!-- context:generated:start -->
## Summary

scripts/ops/registry-queue-watch.py (APP-277) watches the registry request queue, firing only above threshold and respecting cooldown, and distinguishing an empty bridge queue with many attribution-Held firms as a company gap (not an operator gap). It detects EKAP-only queues (a v1 blind spot), persists cooldown in .registry-queue-state.json, and clears state when the queue drains so the next backlog alerts immediately. registry-archive.py archives stale dated sections from the candidate registry markdown while preserving a protected live span byte-identical, with dry-run/apply/check modes and idempotence.

## Related

- uses [[outreach-and-send-gating]] — Shares the Airtable registry data model and attribution-Held firm concept.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
