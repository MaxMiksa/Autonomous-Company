---
name: Consensus & Ledger Pruning
slug: consensus-ledger-pruning
type: system
sources:
  - path: scripts/ops/consensus-prune.py
    hash: 37518266f3c661cfaca25dfec5326a9eda56959005b05e15edb999f1954c441b
  - path: tests/test_auto_loop_consensus_prune.sh
    hash: 9d97a8dfec49f5829637619f996e57ab7e0773498a9788855dacc61a10d51375
  - path: tests/test_consensus_prune.py
    hash: c563247bfe11da182eaa28fbf65d4a5c565e8d30e70f4fedc56a89a2b2673067
sources_digest: 1e1b242659e9b6f4cd5303492f21f774a90db182bdb59f2466b97a3f09a02de1
links:
  - to: harness-loop-core
    relation: uses
    description: >-
      Wired into auto-loop.sh after ledger-guard.py, gated on
      cycle_failed_reason being empty.
generator:
  version: 1
covers:
  - symbol: _load_runtime_env
    kind: function
    at: 'scripts/ops/consensus-prune.py:L123-L134'
  - symbol: _env_int
    kind: function
    at: 'scripts/ops/consensus-prune.py:L137-L142'
  - symbol: _env_flag
    kind: function
    at: 'scripts/ops/consensus-prune.py:L145-L146'
  - symbol: _app
    kind: function
    at: 'scripts/ops/consensus-prune.py:L149-L150'
  - symbol: _sha16
    kind: function
    at: 'scripts/ops/consensus-prune.py:L153-L154'
  - symbol: _load_state
    kind: function
    at: 'scripts/ops/consensus-prune.py:L157-L161'
  - symbol: _save_state
    kind: function
    at: 'scripts/ops/consensus-prune.py:L164-L171'
  - symbol: Skip
    kind: class
    at: 'scripts/ops/consensus-prune.py:L174-L175'
  - symbol: Section
    kind: class
    at: 'scripts/ops/consensus-prune.py:L179-L194'
  - symbol: __init__
    kind: method
    at: 'scripts/ops/consensus-prune.py:L182-L190'
  - symbol: kind
    kind: method
    at: 'scripts/ops/consensus-prune.py:L193-L194'
  - symbol: Removal
    kind: class
    at: 'scripts/ops/consensus-prune.py:L197-L206'
  - symbol: __init__
    kind: method
    at: 'scripts/ops/consensus-prune.py:L201-L206'
  - symbol: _split_sections
    kind: function
    at: 'scripts/ops/consensus-prune.py:L209-L217'
  - symbol: _mark_primary
    kind: function
    at: 'scripts/ops/consensus-prune.py:L220-L241'
  - symbol: flush
    kind: function
    at: 'scripts/ops/consensus-prune.py:L226-L229'
  - symbol: _tail_pass
    kind: function
    at: 'scripts/ops/consensus-prune.py:L245-L249'
  - symbol: _entries_wwd
    kind: function
    at: 'scripts/ops/consensus-prune.py:L252-L284'
  - symbol: _entries_para
    kind: function
    at: 'scripts/ops/consensus-prune.py:L287-L322'
  - symbol: _entries_bullets
    kind: function
    at: 'scripts/ops/consensus-prune.py:L325-L349'
  - symbol: _select
    kind: function
    at: 'scripts/ops/consensus-prune.py:L352-L374'
  - symbol: _line_offsets
    kind: function
    at: 'scripts/ops/consensus-prune.py:L378-L382'
  - symbol: _strip_and_blocks
    kind: function
    at: 'scripts/ops/consensus-prune.py:L385-L400'
  - symbol: _rebuild
    kind: function
    at: 'scripts/ops/consensus-prune.py:L403-L412'
  - symbol: main
    kind: function
    at: 'scripts/ops/consensus-prune.py:L416-L720'
  - symbol: finish_skip
    kind: function
    at: 'scripts/ops/consensus-prune.py:L447-L463'
  - symbol: after_bytes
    kind: function
    at: 'scripts/ops/consensus-prune.py:L531-L532'
  - symbol: record_history
    kind: function
    at: 'scripts/ops/consensus-prune.py:L549-L568'
  - symbol: emit_warns
    kind: function
    at: 'scripts/ops/consensus-prune.py:L570-L572'
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

Maintenance of the canonical consensus document and conflict ledger. consensus-prune.py prunes old entries to keep the document under a size threshold, selecting the newest N by cycle number (not file order), preserving non-entry paragraphs, handling (Prior, Cycle N) lead-ins as single entries, archiving byte-exact pieces with SHA dedupe, and failing closed when required markers would be lost. ledger-guard.py is the companion operational guard. The consensus-prune test suite covers dozens of scenarios including kill switches, dry-run, and streak alarms.

## Related

- uses [[harness-loop-core]] — Wired into auto-loop.sh after ledger-guard.py, gated on cycle_failed_reason being empty.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
