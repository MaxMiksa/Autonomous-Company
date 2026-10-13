---
name: operator request resolution
slug: operator-request-resolution
type: system
sources:
  - path: scripts/core/operator_request_notify.py
    hash: 153aaa73966afd59b8ac7d1a58c29a7279df6297d84743b2375cedd2135ceb18
  - path: tests/test_operator_request_notify.py
    hash: 07fef3026944da791037a735c7e5cea15cdb4f53eabaecf7affda422400f016f
  - path: tests/test_refusal_format.sh
    hash: 11bf5e9869e2e573b4a897e4df84053e4f58d759d3073a9e058705482cc31ef5
sources_digest: c0dbffc502190641162626937e6e41f1c7762e2407d98ae82fcffaf4becc1239
links:
  - to: directive-writer-lifecycle
    relation: uses
    description: Reads Decision lines from human-directive.md to resolve requests.
  - to: operator-action-router
    relation: uses
    description: >-
      Both consume operator-requests.md and human-directive.md; router
      prioritizes hold > opreq > directive.
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
  - symbol: make_send_fn
    kind: function
    at: 'tests/test_operator_request_notify.py:L40-L50'
  - symbol: _send
    kind: function
    at: 'tests/test_operator_request_notify.py:L44-L47'
  - symbol: block_text
    kind: function
    at: 'tests/test_operator_request_notify.py:L53-L70'
  - symbol: OperatorRequestNotifyTests
    kind: class
    at: 'tests/test_operator_request_notify.py:L73-L777'
  - symbol: setUp
    kind: method
    at: 'tests/test_operator_request_notify.py:L74-L87'
  - symbol: tearDown
    kind: method
    at: 'tests/test_operator_request_notify.py:L89-L91'
  - symbol: write_requests
    kind: method
    at: 'tests/test_operator_request_notify.py:L93-L96'
  - symbol: noop_sleep
    kind: method
    at: 'tests/test_operator_request_notify.py:L98-L99'
  - symbol: test_new_request_notified_once
    kind: method
    at: 'tests/test_operator_request_notify.py:L102-L118'
  - symbol: test_unchanged_request_not_renotified
    kind: method
    at: 'tests/test_operator_request_notify.py:L121-L126'
  - symbol: test_timestamp_only_change_does_not_renotify
    kind: method
    at: 'tests/test_operator_request_notify.py:L129-L138'
  - symbol: test_material_change_renotifies_once
    kind: method
    at: 'tests/test_operator_request_notify.py:L141-L155'
  - symbol: test_ordinary_hold_type_never_notifies
    kind: method
    at: 'tests/test_operator_request_notify.py:L158-L177'
  - symbol: test_telegram_failure_not_marked_notified_then_recovers
    kind: method
    at: 'tests/test_operator_request_notify.py:L180-L195'
  - symbol: test_document_procurement_resolution_verifies_checksum_then_disappears
    kind: method
    at: 'tests/test_operator_request_notify.py:L202-L244'
  - symbol: test_document_procurement_resolution_blocks_on_checksum_mismatch
    kind: method
    at: 'tests/test_operator_request_notify.py:L248-L279'
  - symbol: test_document_procurement_resolution_blocks_path_outside_evidence_dir
    kind: method
    at: 'tests/test_operator_request_notify.py:L283-L308'
  - symbol: test_credential_resolution_requires_pass_log_without_secrets
    kind: method
    at: 'tests/test_operator_request_notify.py:L312-L353'
  - symbol: test_credential_resolution_blocks_if_log_contains_secret_shaped_token
    kind: method
    at: 'tests/test_operator_request_notify.py:L355-L400'
  - symbol: test_legal_decision_resolution_requires_structured_decision_line
    kind: method
    at: 'tests/test_operator_request_notify.py:L405-L435'
  - symbol: test_adjudication_pending_resolution_requires_structured_decision_line
    kind: method
    at: 'tests/test_operator_request_notify.py:L441-L480'
  - symbol: test_expenditure_resolution_requires_structured_authorization_block
    kind: method
    at: 'tests/test_operator_request_notify.py:L485-L523'
  - symbol: test_dedup_state_persists_across_process_reinstantiation
    kind: method
    at: 'tests/test_operator_request_notify.py:L528-L538'
  - symbol: _must_not_be_called
    kind: function
    at: 'tests/test_operator_request_notify.py:L534-L535'
  - symbol: test_requests_md_write_failure_does_not_lose_notified_state
    kind: method
    at: 'tests/test_operator_request_notify.py:L544-L565'
  - symbol: test_authorization_complete_block_passes
    kind: method
    at: 'tests/test_operator_request_notify.py:L585-L588'
  - symbol: test_authorization_blank_field_does_not_borrow_next_line
    kind: method
    at: 'tests/test_operator_request_notify.py:L590-L598'
  - symbol: test_authorization_missing_field_reported
    kind: method
    at: 'tests/test_operator_request_notify.py:L600-L604'
  - symbol: _refuse_run
    kind: method
    at: 'tests/test_operator_request_notify.py:L613-L621'
  - symbol: test_refuse_closes_the_request_as_refused_not_resolved
    kind: method
    at: 'tests/test_operator_request_notify.py:L623-L631'
  - symbol: test_refuse_works_without_an_authorization_block
    kind: method
    at: 'tests/test_operator_request_notify.py:L633-L640'
  - symbol: test_prose_mentioning_refusal_does_not_close_anything
    kind: method
    at: 'tests/test_operator_request_notify.py:L642-L651'
  - symbol: test_bare_refuse_with_two_requests_fails_closed
    kind: method
    at: 'tests/test_operator_request_notify.py:L653-L661'
  - symbol: test_named_refuse_targets_only_that_request
    kind: method
    at: 'tests/test_operator_request_notify.py:L663-L673'
  - symbol: _evidence
    kind: method
    at: 'tests/test_operator_request_notify.py:L683-L689'
  - symbol: test_evidence_files_in_the_directive_resolves
    kind: method
    at: 'tests/test_operator_request_notify.py:L691-L699'
  - symbol: test_evidence_files_in_the_request_block_still_resolves
    kind: method
    at: 'tests/test_operator_request_notify.py:L701-L713'
  - symbol: test_directive_entry_with_a_wrong_checksum_is_rejected
    kind: method
    at: 'tests/test_operator_request_notify.py:L715-L723'
  - symbol: test_directive_entry_cannot_escape_the_evidence_directory
    kind: method
    at: 'tests/test_operator_request_notify.py:L725-L734'
  - symbol: test_evidence_files_scoped_to_the_resolving_block
    kind: method
    at: 'tests/test_operator_request_notify.py:L736-L766'
  - symbol: test_decision_token_with_digits_and_underscore_resolves
    kind: method
    at: 'tests/test_operator_request_notify.py:L768-L777'
---
<!-- context:generated:start -->
## Summary

scripts/core/operator_request_notify.py orchestrates Telegram notifications for operator requests and enforces deterministic resolution rules per request type: document-procurement requires a SHA-256 checksum-matched file under memories/operator-evidence/<id>/, credential requires a PASS log with no secret-shaped tokens, legal/financial/adjudication require a structured 'Decision for OPREQ-<id>: <word> — <rationale>' line, and expenditure/external-action require a complete Authorization block. Dedup uses a content fingerprint (ignoring timestamp-only changes), and the refusal format is a short bounded head line followed by verbatim text (a line-anchored regex previously flattened multi-line reasoning).

## Related

- uses [[directive-writer-lifecycle]] — Reads Decision lines from human-directive.md to resolve requests.
- uses [[operator-action-router]] — Both consume operator-requests.md and human-directive.md; router prioritizes hold > opreq > directive.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
