---
name: Consensus & Ledger Pruning
slug: consensus-ledger-pruning
type: system
sources:
  - path: tests/test_auto_loop_consensus_prune.sh
    hash: 9d97a8dfec49f5829637619f996e57ab7e0773498a9788855dacc61a10d51375
  - path: tests/test_auto_loop_ledger_guard.sh
    hash: 707a207723f0b5c371c39d0fbc5a14170b4c74bb9c893f550186797aebcf440f
  - path: tests/test_consensus_prune.py
    hash: c563247bfe11da182eaa28fbf65d4a5c565e8d30e70f4fedc56a89a2b2673067
sources_digest: d4706b078ed18805912a9aaee129495d34db3ae9fb5d866ba4308c319b272b10
links:
  - to: auto-loop-harness
    relation: uses
    description: >-
      Wired into the loop after ledger-guard.py, gated on cycle_failed_reason
      being empty
generator:
  version: 1
covers:
  - symbol: check
    kind: function
    at: 'tests/test_consensus_prune.py:L24-L27'
  - symbol: skip
    kind: function
    at: 'tests/test_consensus_prune.py:L30-L31'
  - symbol: newapp
    kind: function
    at: 'tests/test_consensus_prune.py:L34-L37'
  - symbol: consensus
    kind: function
    at: 'tests/test_consensus_prune.py:L40-L41'
  - symbol: entry
    kind: function
    at: 'tests/test_consensus_prune.py:L44-L49'
  - symbol: para
    kind: function
    at: 'tests/test_consensus_prune.py:L52-L56'
  - symbol: doc
    kind: function
    at: 'tests/test_consensus_prune.py:L59-L70'
  - symbol: doc2
    kind: function
    at: 'tests/test_consensus_prune.py:L73-L95'
  - symbol: run
    kind: function
    at: 'tests/test_consensus_prune.py:L101-L110'
  - symbol: guard
    kind: function
    at: 'tests/test_consensus_prune.py:L113-L116'
  - symbol: headers
    kind: function
    at: 'tests/test_consensus_prune.py:L119-L120'
  - symbol: section
    kind: function
    at: 'tests/test_consensus_prune.py:L123-L127'
  - symbol: non_cycle_paras
    kind: function
    at: 'tests/test_consensus_prune.py:L130-L131'
  - symbol: archive_pieces
    kind: function
    at: 'tests/test_consensus_prune.py:L134-L158'
  - symbol: full
    kind: function
    at: 'tests/test_consensus_prune.py:L375-L377'
  - symbol: prior_para
    kind: function
    at: 'tests/test_consensus_prune.py:L410-L411'
  - symbol: ec_doc
    kind: function
    at: 'tests/test_consensus_prune.py:L467-L472'
---
<!-- context:generated:start -->
## Summary

Operational guards that keep canonical documents under size thresholds and enforce cycle invariants. consensus-prune.py archives old entries from the consensus document to docs/operations/consensus-archive-*.md, selecting the newest N entries by cycle number (not file order), preserving non-entry paragraphs, handling (Prior, Cycle N) lead-in forms as single entries, and failing closed when required markers would be lost; archived pieces are byte-exact with SHA dedupe to prevent duplicate archive blocks. ledger-guard.py enforces cycle invariants and is wired into auto-loop.sh after the prune hook, gated on cycle_failed_reason being empty.

## Related

- uses [[auto-loop-harness]] — Wired into the loop after ledger-guard.py, gated on cycle_failed_reason being empty
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
