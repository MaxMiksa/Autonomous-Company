---
name: Consensus Pruning & Archival
slug: consensus-pruning-archival
type: system
sources:
  - path: scripts/ops/consensus-prune.py
    hash: 37518266f3c661cfaca25dfec5326a9eda56959005b05e15edb999f1954c441b
  - path: scripts/ops/registry-archive.py
    hash: 125be575d2da1c70effa433e2eabe55e5e7e7851fc89719651a1520bb76ee651
sources_digest: be2cf41b0112616fecff19a7dae0162fc97fb833468ecbb8336f3a0eed8065ea
links:
  - to: consensus-memory-state-files
    relation: validates
    description: >-
      Keeps consensus.md and candidate-registry.md under size thresholds to
      avoid PROMPT-SIZE brake drops
  - to: ledger-integrity-guard
    relation: depends_on
    description: >-
      ledger-guard.py's _rebase_after_prune reconciles baselines when pruning
      legitimately reduces file size
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

Maintenance scripts that keep the memory files under size brakes so the loop's inline prompt never drops them. consensus-prune.py archives stale per-cycle narrative from consensus.md into monthly docs when the file exceeds ~70KB, running six pruning passes with fail-closed data safety (rebuild verification, SHA-256, atomic writes) but fail-open loop impact (always exits 0). registry-archive.py moves stale notes and frozen PART A / Cycle N sections from candidate-registry.md into monthly files, enforcing a byte-identical protected live region and SHA-256 reconstruction verification.

## Related

- validates [[consensus-memory-state-files]] — Keeps consensus.md and candidate-registry.md under size thresholds to avoid PROMPT-SIZE brake drops
- depends on [[ledger-integrity-guard]] — ledger-guard.py's _rebase_after_prune reconciles baselines when pruning legitimately reduces file size
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
