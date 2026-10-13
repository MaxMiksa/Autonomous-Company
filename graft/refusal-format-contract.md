---
name: refusal format contract
slug: refusal-format-contract
type: concept
sources:
  - path: dashboard/server.py
    hash: 999b44bc7671293e78906611b1dfd46bcf6efcc520ed92623a17281766a7fc85
  - path: scripts/core/operator_request_notify.py
    hash: 153aaa73966afd59b8ac7d1a58c29a7279df6297d84743b2375cedd2135ceb18
  - path: tests/test_refusal_format.sh
    hash: 11bf5e9869e2e573b4a897e4df84053e4f58d759d3073a9e058705482cc31ef5
sources_digest: c53fc5627d11ac169fdba13eefb75b93575d79738efd1dfa734d7ad636807b76
links:
  - to: dashboard-server
    relation: produces
    description: >-
      The cockpit's operator-decision panel (dashboard/server.py) writes the
      refusal format
  - to: operator-request-notify
    relation: validates
    description: >-
      operator_request_notify.py parses the refusal format and records a single
      REFUSED audit entry, idempotent on second run
generator:
  version: 1
covers:
  - symbol: ps_quote
    kind: function
    at: 'dashboard/server.py:L123-L124'
  - symbol: detect_host_kind
    kind: function
    at: 'dashboard/server.py:L127-L137'
  - symbol: run_powershell_script
    kind: function
    at: 'dashboard/server.py:L140-L184'
  - symbol: run_shell_script
    kind: function
    at: 'dashboard/server.py:L187-L217'
  - symbol: get_host_profile
    kind: function
    at: 'dashboard/server.py:L220-L253'
  - symbol: read_text_file
    kind: function
    at: 'dashboard/server.py:L256-L270'
  - symbol: read_text_file_tail
    kind: function
    at: 'dashboard/server.py:L273-L305'
  - symbol: read_directive
    kind: function
    at: 'dashboard/server.py:L315-L347'
  - symbol: _section
    kind: function
    at: 'dashboard/server.py:L326-L337'
  - symbol: DirectiveRefused
    kind: class
    at: 'dashboard/server.py:L350-L351'
  - symbol: write_directive
    kind: function
    at: 'dashboard/server.py:L354-L397'
  - symbol: parse_proposed_authorization
    kind: function
    at: 'dashboard/server.py:L426-L435'
  - symbol: read_operator_requests
    kind: function
    at: 'dashboard/server.py:L438-L473'
  - symbol: _decisions_audit
    kind: function
    at: 'dashboard/server.py:L476-L483'
  - symbol: write_operator_decision
    kind: function
    at: 'dashboard/server.py:L486-L572'
  - symbol: _parse_env_file
    kind: function
    at: 'dashboard/server.py:L575-L587'
  - symbol: read_ideas
    kind: function
    at: 'dashboard/server.py:L590-L608'
  - symbol: read_tool_usage
    kind: function
    at: 'dashboard/server.py:L611-L648'
  - symbol: read_analysis
    kind: function
    at: 'dashboard/server.py:L651-L669'
  - symbol: analyst_trigger_state
    kind: function
    at: 'dashboard/server.py:L672-L679'
  - symbol: analyst_run_now
    kind: function
    at: 'dashboard/server.py:L682-L708'
  - symbol: read_directive_templates
    kind: function
    at: 'dashboard/server.py:L726-L733'
  - symbol: read_settings
    kind: function
    at: 'dashboard/server.py:L736-L778'
  - symbol: write_settings
    kind: function
    at: 'dashboard/server.py:L781-L827'
  - symbol: _proc_cmdline
    kind: function
    at: 'dashboard/server.py:L830-L835'
  - symbol: _proc_ppid
    kind: function
    at: 'dashboard/server.py:L838-L845'
  - symbol: read_hold
    kind: function
    at: 'dashboard/server.py:L852-L875'
  - symbol: set_hold
    kind: function
    at: 'dashboard/server.py:L878-L915'
  - symbol: wake_loop
    kind: function
    at: 'dashboard/server.py:L918-L976'
  - symbol: trigger_redeploy
    kind: function
    at: 'dashboard/server.py:L979-L1015'
  - symbol: _week_start_epoch
    kind: function
    at: 'dashboard/server.py:L1031-L1038'
  - symbol: _ccusage_compute
    kind: function
    at: 'dashboard/server.py:L1041-L1096'
  - symbol: _run
    kind: function
    at: 'dashboard/server.py:L1047-L1055'
  - symbol: _is_codex
    kind: function
    at: 'dashboard/server.py:L1070-L1072'
  - symbol: read_ccusage
    kind: function
    at: 'dashboard/server.py:L1099-L1119'
  - symbol: _bg
    kind: function
    at: 'dashboard/server.py:L1111-L1116'
  - symbol: read_engine_runtime
    kind: function
    at: 'dashboard/server.py:L1122-L1219'
  - symbol: _window_cutoff_epoch
    kind: function
    at: 'dashboard/server.py:L1222-L1250'
  - symbol: read_cost_summary
    kind: function
    at: 'dashboard/server.py:L1253-L1384'
  - symbol: _last_budget_gate
    kind: function
    at: 'dashboard/server.py:L1387-L1395'
  - symbol: read_tail
    kind: function
    at: 'dashboard/server.py:L1398-L1405'
  - symbol: parse_sections
    kind: function
    at: 'dashboard/server.py:L1408-L1423'
  - symbol: parse_int
    kind: function
    at: 'dashboard/server.py:L1426-L1430'
  - symbol: parse_positive_int
    kind: function
    at: 'dashboard/server.py:L1433-L1438'
  - symbol: parse_key_values
    kind: function
    at: 'dashboard/server.py:L1441-L1448'
  - symbol: blank_parsed
    kind: function
    at: 'dashboard/server.py:L1451-L1475'
  - symbol: parse_windows_status_output
    kind: function
    at: 'dashboard/server.py:L1478-L1560'
  - symbol: parse_macos_status_output
    kind: function
    at: 'dashboard/server.py:L1563-L1599'
  - symbol: read_state_file_pairs
    kind: function
    at: 'dashboard/server.py:L1602-L1610'
  - symbol: run_status_command
    kind: function
    at: 'dashboard/server.py:L1613-L1616'
  - symbol: run_dashboard_action
    kind: function
    at: 'dashboard/server.py:L1619-L1631'
  - symbol: parse_status_output
    kind: function
    at: 'dashboard/server.py:L1634-L1636'
  - symbol: gather_status_payload
    kind: function
    at: 'dashboard/server.py:L1639-L1659'
  - symbol: read_graft_freshness
    kind: function
    at: 'dashboard/server.py:L1662-L1672'
  - symbol: DashboardHandler
    kind: class
    at: 'dashboard/server.py:L1675-L1980'
  - symbol: _json
    kind: method
    at: 'dashboard/server.py:L1676-L1683'
  - symbol: _text
    kind: method
    at: 'dashboard/server.py:L1685-L1694'
  - symbol: _serve_file
    kind: method
    at: 'dashboard/server.py:L1696-L1700'
  - symbol: do_GET
    kind: method
    at: 'dashboard/server.py:L1702-L1707'
  - symbol: _do_GET
    kind: method
    at: 'dashboard/server.py:L1709-L1775'
  - symbol: _read_body
    kind: method
    at: 'dashboard/server.py:L1777-L1784'
  - symbol: do_POST
    kind: method
    at: 'dashboard/server.py:L1786-L1791'
  - symbol: _do_POST
    kind: method
    at: 'dashboard/server.py:L1793-L1856'
  - symbol: _handle_operator_decision
    kind: method
    at: 'dashboard/server.py:L1858-L1898'
  - symbol: _handle_directive
    kind: method
    at: 'dashboard/server.py:L1900-L1946'
  - symbol: _handle_settings
    kind: method
    at: 'dashboard/server.py:L1948-L1977'
  - symbol: log_message
    kind: method
    at: 'dashboard/server.py:L1979-L1980'
  - symbol: main
    kind: function
    at: 'dashboard/server.py:L1983-L2005'
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

The refusal format written by the cockpit's operator-decision panel must keep multi-line operator reasoning intact: a short head line followed by verbatim text, with numbered points surviving as separate lines. A line-anchored regex previously flattened multi-line reasoning into a single long REFUSE line, breaking the parser. The decision file must retain at least 12 lines and the REFUSE head must be a single bounded line.

## Related

- produces [[dashboard-server]] — The cockpit's operator-decision panel (dashboard/server.py) writes the refusal format
- validates [[operator-request-notify]] — operator_request_notify.py parses the refusal format and records a single REFUSED audit entry, idempotent on second run
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
