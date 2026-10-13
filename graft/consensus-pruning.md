---
name: Consensus Pruning
slug: consensus-pruning
type: file
sources:
  - path: scripts/ops/consensus-prune.py
    hash: 37518266f3c661cfaca25dfec5326a9eda56959005b05e15edb999f1954c441b
sources_digest: d17d9ad0f679e6f71038a7016f1d1348c147b53607ba81a4fb6e2c7abc170051
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
---
<!-- context:generated:start -->
## Summary

consensus-prune.py prunes old entries from the canonical consensus document to keep it under a size threshold, archiving byte-exact pieces to docs/operations/consensus-archive-*.md with SHA dedupe so re-runs don't duplicate archive blocks. It selects the newest N entries by cycle number (not file order), preserves non-entry paragraphs, handles '(Prior, Cycle N)' lead-in forms as single entries, detects code fences to skip sections, and fails closed when required markers would be lost. It integrates with ledger-guard.py and emits streak alarms after repeated skips.

## Related

- uses [[harness-loop-core]] — Wired into auto-loop.sh after ledger-guard.py, gated on cycle_failed_reason being empty.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
