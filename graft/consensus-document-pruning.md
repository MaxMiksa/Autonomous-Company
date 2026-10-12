---
name: Consensus document pruning
slug: consensus-document-pruning
type: system
sources:
  - path: tests/test_auto_loop_consensus_prune.sh
    hash: 9d97a8dfec49f5829637619f996e57ab7e0773498a9788855dacc61a10d51375
  - path: tests/test_consensus_prune.py
    hash: c563247bfe11da182eaa28fbf65d4a5c565e8d30e70f4fedc56a89a2b2673067
sources_digest: 95dd563f59940db788447b2a639e53d0d1e5774b111aa155878dbb7219deaca2
links:
  - to: auto-loop-harness
    relation: uses
    description: >-
      The loop invokes the prune hook after ledger-guard.py, gated on
      cycle_failed_reason being empty.
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

consensus-prune.py prunes old entries from the canonical consensus document to keep it under a size threshold, archiving byte-exact to docs/operations/consensus-archive-*.md with SHA dedupe so re-runs don't duplicate archive blocks. Selects the newest N entries by cycle number (not file order), preserves non-entry paragraphs, handles (Prior, Cycle N) lead-in forms as single entries, detects code fences to skip sections, and fails closed when required markers would be lost. Wired into auto-loop.sh after ledger-guard.py, gated on cycle_failed_reason being empty.

## Related

- uses [[auto-loop-harness]] — The loop invokes the prune hook after ledger-guard.py, gated on cycle_failed_reason being empty.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
