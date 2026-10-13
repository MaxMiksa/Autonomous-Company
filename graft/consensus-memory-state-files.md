---
name: Consensus Memory & State Files
slug: consensus-memory-state-files
type: system
sources:
  - path: scripts/core/operator_request_notify.py
    hash: 153aaa73966afd59b8ac7d1a58c29a7279df6297d84743b2375cedd2135ceb18
  - path: scripts/ops/consensus-prune.py
    hash: 37518266f3c661cfaca25dfec5326a9eda56959005b05e15edb999f1954c441b
  - path: scripts/ops/idle-skip-note.py
    hash: 1d4f853b19cdc9ee94c0fd1136ea67393d04deb36a7563e2720ef15a0631ec98
  - path: scripts/ops/ledger-guard.py
    hash: 5b3098424eada1d1f669995baf5e1dd76ea4fb724c0c524ddc9986ce361128d7
  - path: scripts/ops/registry-archive.py
    hash: 125be575d2da1c70effa433e2eabe55e5e7e7851fc89719651a1520bb76ee651
sources_digest: 79d608b6d4fff5ec974ea63169a3d6a21de95bf94bf86671fc1ed1e9a4f017e5
links:
  - to: auto-company-loop-orchestration
    relation: produces
    description: >-
      The loop writes cycle narrative, state, and turn-audit lines into these
      files
  - to: consensus-pruning-archival
    relation: validates
    description: >-
      consensus-prune.py and registry-archive.py keep these files under size
      brakes
  - to: ledger-integrity-guard
    relation: validates
    description: >-
      ledger-guard.py detects silent content loss in consensus.md and the
      conflict ledger
  - to: operator-escalation-gate
    relation: uses
    description: >-
      operator_request_notify.py reads operator-requests.md and projects
      Awaiting Operator into consensus.md
generator:
  version: 1
covers:
  - symbol: _looks_secret
    kind: function
    at: 'scripts/core/operator_request_notify.py:L114-L123'
  - symbol: now_iso
    kind: function
    at: 'scripts/core/operator_request_notify.py:L134-L135'
  - symbol: norm_field
    kind: function
    at: 'scripts/core/operator_request_notify.py:L138-L139'
  - symbol: material_hash
    kind: function
    at: 'scripts/core/operator_request_notify.py:L142-L151'
  - symbol: parse_fields
    kind: function
    at: 'scripts/core/operator_request_notify.py:L154-L166'
  - symbol: parse_blocks
    kind: function
    at: 'scripts/core/operator_request_notify.py:L169-L181'
  - symbol: validate_required
    kind: function
    at: 'scripts/core/operator_request_notify.py:L184-L186'
  - symbol: set_field_in_block_body
    kind: function
    at: 'scripts/core/operator_request_notify.py:L189-L198'
  - symbol: set_field_in_text
    kind: function
    at: 'scripts/core/operator_request_notify.py:L201-L208'
  - symbol: scrub_secrets
    kind: function
    at: 'scripts/core/operator_request_notify.py:L211-L216'
  - symbol: compose_message
    kind: function
    at: 'scripts/core/operator_request_notify.py:L241-L271'
  - symbol: send_telegram
    kind: function
    at: 'scripts/core/operator_request_notify.py:L274-L294'
  - symbol: attempt_notify
    kind: function
    at: 'scripts/core/operator_request_notify.py:L297-L306'
  - symbol: load_state
    kind: function
    at: 'scripts/core/operator_request_notify.py:L309-L327'
  - symbol: write_state
    kind: function
    at: 'scripts/core/operator_request_notify.py:L330-L337'
  - symbol: write_text_verified
    kind: function
    at: 'scripts/core/operator_request_notify.py:L340-L342'
  - symbol: audit
    kind: function
    at: 'scripts/core/operator_request_notify.py:L345-L348'
  - symbol: render_projection_body
    kind: function
    at: 'scripts/core/operator_request_notify.py:L351-L366'
  - symbol: splice_projection
    kind: function
    at: 'scripts/core/operator_request_notify.py:L369-L397'
  - symbol: process_notifications
    kind: function
    at: 'scripts/core/operator_request_notify.py:L400-L480'
  - symbol: _resolve_evidence_path
    kind: function
    at: 'scripts/core/operator_request_notify.py:L489-L499'
  - symbol: verify_document_procurement
    kind: function
    at: 'scripts/core/operator_request_notify.py:L502-L578'
  - symbol: verify_credential
    kind: function
    at: 'scripts/core/operator_request_notify.py:L581-L622'
  - symbol: _directive_window_after
    kind: function
    at: 'scripts/core/operator_request_notify.py:L646-L654'
  - symbol: _resolves_block_window
    kind: function
    at: 'scripts/core/operator_request_notify.py:L657-L671'
  - symbol: verify_legal_or_financial_decision
    kind: function
    at: 'scripts/core/operator_request_notify.py:L687-L709'
  - symbol: verify_authorization
    kind: function
    at: 'scripts/core/operator_request_notify.py:L712-L738'
  - symbol: refusal_for
    kind: function
    at: 'scripts/core/operator_request_notify.py:L754-L778'
  - symbol: verify_resolution
    kind: function
    at: 'scripts/core/operator_request_notify.py:L781-L802'
  - symbol: _answer_sources
    kind: function
    at: 'scripts/core/operator_request_notify.py:L805-L823'
  - symbol: process_resolutions
    kind: function
    at: 'scripts/core/operator_request_notify.py:L826-L884'
  - symbol: _main_impl
    kind: function
    at: 'scripts/core/operator_request_notify.py:L887-L979'
  - symbol: main
    kind: function
    at: 'scripts/core/operator_request_notify.py:L982-L994'
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
  - symbol: build_line
    kind: function
    at: 'scripts/ops/idle-skip-note.py:L26-L34'
  - symbol: main
    kind: function
    at: 'scripts/ops/idle-skip-note.py:L37-L89'
  - symbol: _env_int
    kind: function
    at: 'scripts/ops/ledger-guard.py:L43-L48'
  - symbol: _env_float
    kind: function
    at: 'scripts/ops/ledger-guard.py:L51-L55'
  - symbol: _app
    kind: function
    at: 'scripts/ops/ledger-guard.py:L58-L59'
  - symbol: _find_ledger
    kind: function
    at: 'scripts/ops/ledger-guard.py:L62-L69'
  - symbol: _metrics
    kind: function
    at: 'scripts/ops/ledger-guard.py:L72-L84'
  - symbol: _backup
    kind: function
    at: 'scripts/ops/ledger-guard.py:L87-L101'
  - symbol: _load_state
    kind: function
    at: 'scripts/ops/ledger-guard.py:L104-L108'
  - symbol: _save_state
    kind: function
    at: 'scripts/ops/ledger-guard.py:L111-L118'
  - symbol: _rebase_after_prune
    kind: function
    at: 'scripts/ops/ledger-guard.py:L125-L142'
  - symbol: _check
    kind: function
    at: 'scripts/ops/ledger-guard.py:L145-L170'
  - symbol: main
    kind: function
    at: 'scripts/ops/ledger-guard.py:L173-L240'
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

The durable memory layer: memories/consensus.md (per-cycle narrative, Key Decisions, Awaiting Operator projection), memories/candidate-registry.md (analyst-read registry with PART A / Cycle N sections), memories/human-directive.md, memories/operator-requests.md, and runtime artifacts (.auto-loop-state, .auto-loop.pid, .auto-loop-paused, logs/runtime.env). These files are the source of truth for the loop and are guarded against silent loss and bloat by dedicated maintenance scripts.

## Related

- produces [[auto-company-loop-orchestration]] — The loop writes cycle narrative, state, and turn-audit lines into these files
- validates [[consensus-pruning-archival]] — consensus-prune.py and registry-archive.py keep these files under size brakes
- validates [[ledger-integrity-guard]] — ledger-guard.py detects silent content loss in consensus.md and the conflict ledger
- uses [[operator-escalation-gate]] — operator_request_notify.py reads operator-requests.md and projects Awaiting Operator into consensus.md
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
