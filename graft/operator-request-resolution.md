---
name: operator request resolution
slug: operator-request-resolution
type: system
sources:
  - path: tests/test_operator_request_notify.py
    hash: 07fef3026944da791037a735c7e5cea15cdb4f53eabaecf7affda422400f016f
  - path: tests/test_refusal_format.sh
    hash: 11bf5e9869e2e573b4a897e4df84053e4f58d759d3073a9e058705482cc31ef5
sources_digest: ebe602783e96c25da7ca858c8d25dcc4551f325dec64bdc8b5d77a6c35198ecb
links:
  - to: directive-writer-section-refs
    relation: uses
    description: Reads Decision/Authorization lines from human-directive.md
  - to: operator-action-router
    relation: uses
    description: operator-requests.md is a shared input consumed by the router
generator:
  version: 1
covers:
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

scripts/core/operator_request_notify.py orchestrates Telegram notifications for operator requests and enforces deterministic per-type resolution rules: document-procurement requires a SHA-256 checksum-matched file under memories/operator-evidence/<id>/ (rejecting mismatches and paths outside that directory); credential requires a PASS log with no secret-shaped tokens; legal/financial/adjudication require a structured 'Decision for OPREQ-<id>: <word> — <rationale>' line; expenditure/external-action require a complete 'Authorization for OPREQ-<id>:' block with System/Action/Target/Limit. Notifications are one-time with a content fingerprint (ignoring timestamp-only changes), re-notified on material edits, and HOLD/informational/research-result types are suppressed. Resolved requests disappear from the consensus projection.

## Related

- uses [[directive-writer-section-refs]] — Reads Decision/Authorization lines from human-directive.md
- uses [[operator-action-router]] — operator-requests.md is a shared input consumed by the router
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
