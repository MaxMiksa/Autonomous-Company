---
name: Operator Escalation Gate
slug: operator-escalation-gate
type: file
sources:
  - path: scripts/core/operator_request_notify.py
    hash: 153aaa73966afd59b8ac7d1a58c29a7279df6297d84743b2375cedd2135ceb18
sources_digest: 08e270506033e760552382aabd9d83029cb15360041cab348a97e0080bea68bf
links:
  - to: consensus-memory-state-files
    relation: uses
    description: >-
      Reads memories/operator-requests.md and writes the Awaiting Operator
      projection into consensus.md
  - to: human-directive-write-path
    relation: uses
    description: Reads explicit directives in human-directive.md as resolution evidence
  - to: telegram-notification-channel
    relation: uses
    description: Sends operator alerts via the Telegram Bot API
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
---
<!-- context:generated:start -->
## Summary

operator_request_notify.py is the sole authority for deciding when human operator input is genuinely needed and managing the notification lifecycle. It reads operator-requests.md, deduplicates via content fingerprints, sends Telegram notifications only for seven escalation-worthy types, and requires deterministic verification (checksum-matched evidence, structured verification logs, or explicit directives) for resolution. It regenerates the Awaiting Operator projection in consensus.md and deliberately refuses to invent requests.

## Related

- uses [[consensus-memory-state-files]] — Reads memories/operator-requests.md and writes the Awaiting Operator projection into consensus.md
- uses [[human-directive-write-path]] — Reads explicit directives in human-directive.md as resolution evidence
- uses [[telegram-notification-channel]] — Sends operator alerts via the Telegram Bot API
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
