---
name: Memory Ledger Files
slug: memory-ledger-files
type: concept
sources:
  - path: scripts/ops/consensus-prune.py
    hash: 37518266f3c661cfaca25dfec5326a9eda56959005b05e15edb999f1954c441b
  - path: scripts/ops/staleness-report.py
    hash: ebae44b614629bd12ad5e8db730b3eb731008cd740b6e73893cedb810c052516
  - path: scripts/ops/state-snapshot.py
    hash: 3112f4632b64a6b531b215ea81ba82b2ceb6436942511f816de94ced3171bfe8
  - path: tests/test_consensus_prune.py
    hash: c563247bfe11da182eaa28fbf65d4a5c565e8d30e70f4fedc56a89a2b2673067
sources_digest: 038d5fd198fa022521dbda7975e40518ac58a5f11fc7bbc50b6728062e9078b4
links:
  - to: consensus-pruning
    relation: validates
    description: >-
      consensus-prune.py keeps consensus.md under a size threshold, archiving
      byte-exact entries
  - to: memory-staleness-snapshot-probes
    relation: validates
    description: staleness-report.py and state-snapshot.py measure and hash these surfaces
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
  - symbol: _bytes
    kind: function
    at: 'scripts/ops/staleness-report.py:L37-L38'
  - symbol: _read
    kind: function
    at: 'scripts/ops/staleness-report.py:L41-L45'
  - symbol: _sections
    kind: function
    at: 'scripts/ops/staleness-report.py:L48-L55'
  - symbol: _heading_date
    kind: function
    at: 'scripts/ops/staleness-report.py:L58-L65'
  - symbol: directive_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L68-L86'
  - symbol: opreq_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L89-L99'
  - symbol: decisions_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L102-L107'
  - symbol: consensus_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L110-L117'
  - symbol: ledger_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L120-L142'
  - symbol: prompt_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L145-L152'
  - symbol: weekly_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L155-L168'
  - symbol: _accepted_weekly_gaps
    kind: function
    at: 'scripts/ops/staleness-report.py:L175-L191'
  - symbol: backup_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L197-L213'
  - symbol: build
    kind: function
    at: 'scripts/ops/staleness-report.py:L216-L224'
  - symbol: main
    kind: function
    at: 'scripts/ops/staleness-report.py:L227-L244'
  - symbol: file_sha16
    kind: function
    at: 'scripts/ops/state-snapshot.py:L54-L61'
  - symbol: directive_state
    kind: function
    at: 'scripts/ops/state-snapshot.py:L64-L72'
  - symbol: opreq_open
    kind: function
    at: 'scripts/ops/state-snapshot.py:L75-L87'
  - symbol: wowcar_sources
    kind: function
    at: 'scripts/ops/state-snapshot.py:L90-L104'
  - symbol: main
    kind: function
    at: 'scripts/ops/state-snapshot.py:L107-L166'
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

The canonical memory surfaces the auditor maintains: human-directive.md (the live directive, sliced from the first '\n## Directive\n' marker skipping Kaynak belgeler/WOWCAR/Operatör sections), operator-requests.md (OPREQ blocks), operator-decisions.md, consensus.md, and conflict-ledger docs. These are the objects of staleness measurement, snapshot hashing, and consensus pruning. The conflict-ledger staleness check matches on section codes (§7GJ) rather than cycle numbers because the header's cycle and last section's cycle legitimately differ.

## Related

- validates [[consensus-pruning]] — consensus-prune.py keeps consensus.md under a size threshold, archiving byte-exact entries
- validates [[memory-staleness-snapshot-probes]] — staleness-report.py and state-snapshot.py measure and hash these surfaces
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
