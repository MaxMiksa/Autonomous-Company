---
name: dashboard server
slug: dashboard-server
type: system
sources:
  - path: dashboard/server.py
    hash: 999b44bc7671293e78906611b1dfd46bcf6efcc520ed92623a17281766a7fc85
  - path: tests/test_dashboard_server.py
    hash: 56e9073d5a9447df622cb3e0873d553053a3b16089534d427c177db772b933dd
  - path: tests/test_refusal_format.sh
    hash: 11bf5e9869e2e573b4a897e4df84053e4f58d759d3073a9e058705482cc31ef5
sources_digest: b345d383ecc504e4dc9ae899649f4c78d13f54490aec22ca11dbdb4bb80e8732
links:
  - to: operator-request-notification
    relation: produces
    description: >-
      The refusal format written by the cockpit's operator-decision panel is
      consumed by operator_request_notify.py.
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
  - symbol: DashboardServerTests
    kind: class
    at: 'tests/test_dashboard_server.py:L27-L210'
  - symbol: test_windows_not_running_maps_to_stopped
    kind: method
    at: 'tests/test_dashboard_server.py:L28-L52'
  - symbol: test_windows_not_installed_daemon_maps_correctly
    kind: method
    at: 'tests/test_dashboard_server.py:L54-L74'
  - symbol: test_macos_active_configured_running_maps_correctly
    kind: method
    at: 'tests/test_dashboard_server.py:L76-L112'
  - symbol: test_macos_inactive_configured_stopped_and_guardian_without_caffeinate
    kind: method
    at: 'tests/test_dashboard_server.py:L114-L135'
  - symbol: test_macos_not_installed_maps_correctly
    kind: method
    at: 'tests/test_dashboard_server.py:L137-L157'
  - symbol: test_windows_start_uses_powershell_runner
    kind: method
    at: 'tests/test_dashboard_server.py:L159-L169'
  - symbol: test_macos_stop_uses_shell_runner_with_pause_daemon
    kind: method
    at: 'tests/test_dashboard_server.py:L171-L183'
  - symbol: test_refresh_uses_status_script
    kind: method
    at: 'tests/test_dashboard_server.py:L185-L194'
  - symbol: test_invalid_log_tail_lines_fall_back_to_default
    kind: method
    at: 'tests/test_dashboard_server.py:L196-L199'
  - symbol: test_unsupported_host_raises
    kind: method
    at: 'tests/test_dashboard_server.py:L201-L210'
  - symbol: EngineRuntimeParsingTests
    kind: class
    at: 'tests/test_dashboard_server.py:L235-L368'
  - symbol: _run
    kind: method
    at: 'tests/test_dashboard_server.py:L238-L243'
  - symbol: fake_read
    kind: function
    at: 'tests/test_dashboard_server.py:L239-L240'
  - symbol: test_claude_cycle_reports_its_effort
    kind: method
    at: 'tests/test_dashboard_server.py:L245-L253'
  - symbol: test_codex_cycle_still_reports_codex_effort
    kind: method
    at: 'tests/test_dashboard_server.py:L255-L259'
  - symbol: test_window_budget_and_ladders_take_the_latest_boot
    kind: method
    at: 'tests/test_dashboard_server.py:L261-L271'
  - symbol: test_legacy_tier_line_without_claude_effort_still_parses
    kind: method
    at: 'tests/test_dashboard_server.py:L273-L284'
  - symbol: _settings
    kind: method
    at: 'tests/test_dashboard_server.py:L292-L296'
  - symbol: test_settings_source_runtime_env_wins
    kind: method
    at: 'tests/test_dashboard_server.py:L298-L303'
  - symbol: test_settings_source_container_when_absent_from_file
    kind: method
    at: 'tests/test_dashboard_server.py:L305-L310'
  - symbol: test_settings_source_default_when_nowhere
    kind: method
    at: 'tests/test_dashboard_server.py:L312-L315'
  - symbol: _runtime
    kind: method
    at: 'tests/test_dashboard_server.py:L332-L340'
  - symbol: fake_read
    kind: function
    at: 'tests/test_dashboard_server.py:L333-L334'
  - symbol: test_escalated_cycle_reports_the_escalated_model
    kind: method
    at: 'tests/test_dashboard_server.py:L342-L348'
  - symbol: test_escalation_before_the_tier_line_is_ignored
    kind: method
    at: 'tests/test_dashboard_server.py:L350-L363'
  - symbol: test_codex_cycle_ignores_escalation_entirely
    kind: method
    at: 'tests/test_dashboard_server.py:L365-L368'
  - symbol: WindowCutoffTests
    kind: class
    at: 'tests/test_dashboard_server.py:L371-L432'
  - symbol: setUp
    kind: method
    at: 'tests/test_dashboard_server.py:L379-L386'
  - symbol: tearDown
    kind: method
    at: 'tests/test_dashboard_server.py:L388-L390'
  - symbol: _write
    kind: method
    at: 'tests/test_dashboard_server.py:L392-L396'
  - symbol: test_fresh_blockstart_anchors_the_window
    kind: method
    at: 'tests/test_dashboard_server.py:L398-L404'
  - symbol: test_stale_usage_file_falls_back_to_rolling
    kind: method
    at: 'tests/test_dashboard_server.py:L406-L414'
  - symbol: test_blockstart_older_than_rolling_never_widens_the_window
    kind: method
    at: 'tests/test_dashboard_server.py:L416-L421'
  - symbol: test_missing_or_unparseable_file_falls_back
    kind: method
    at: 'tests/test_dashboard_server.py:L423-L432'
  - symbol: ReadTextFileTailTests
    kind: class
    at: 'tests/test_dashboard_server.py:L439-L497'
  - symbol: _tmp
    kind: method
    at: 'tests/test_dashboard_server.py:L444-L449'
  - symbol: test_returns_whole_file_when_smaller_than_window
    kind: method
    at: 'tests/test_dashboard_server.py:L451-L455'
  - symbol: test_truncates_to_the_tail_and_drops_the_partial_first_line
    kind: method
    at: 'tests/test_dashboard_server.py:L457-L464'
  - symbol: test_multibyte_seek_does_not_produce_replacement_junk
    kind: method
    at: 'tests/test_dashboard_server.py:L466-L470'
  - symbol: test_missing_file_returns_fallback
    kind: method
    at: 'tests/test_dashboard_server.py:L472-L475'
  - symbol: test_engine_runtime_falls_back_to_full_file_when_banner_is_out_of_window
    kind: method
    at: 'tests/test_dashboard_server.py:L477-L497'
  - symbol: fake_read
    kind: function
    at: 'tests/test_dashboard_server.py:L488-L489'
  - symbol: WeeklyCostWindowTests
    kind: class
    at: 'tests/test_dashboard_server.py:L500-L544'
  - symbol: _summary_for
    kind: method
    at: 'tests/test_dashboard_server.py:L505-L509'
  - symbol: _stamp
    kind: method
    at: 'tests/test_dashboard_server.py:L512-L513'
  - symbol: test_week_window_splits_old_and_new_costs
    kind: method
    at: 'tests/test_dashboard_server.py:L515-L534'
  - symbol: test_unstamped_cost_line_counts_all_time_only
    kind: method
    at: 'tests/test_dashboard_server.py:L536-L544'
  - symbol: LiveBudgetGateDisplayTests
    kind: class
    at: 'tests/test_dashboard_server.py:L547-L581'
  - symbol: test_engine_runtime_parses_live_gate_banner_last_match
    kind: method
    at: 'tests/test_dashboard_server.py:L553-L565'
  - symbol: test_cost_summary_carries_last_budget_gate_line
    kind: method
    at: 'tests/test_dashboard_server.py:L567-L581'
  - symbol: GraftFreshnessTests
    kind: class
    at: 'tests/test_dashboard_server.py:L584-L613'
  - symbol: test_absent_file_reports_unavailable
    kind: method
    at: 'tests/test_dashboard_server.py:L588-L592'
  - symbol: test_valid_status_passthrough
    kind: method
    at: 'tests/test_dashboard_server.py:L594-L604'
  - symbol: test_malformed_json_reports_unavailable
    kind: method
    at: 'tests/test_dashboard_server.py:L606-L613'
---
<!-- context:generated:start -->
## Summary

dashboard/server.py is the cockpit status/action server: parses the persistent auto-loop.log to reflect the latest boot (including escalated cycles and legacy tier lines), resolves settings, computes cost summaries with spend-window anchoring on ccusage blockStart and rolling fallback, splits weekly cost on Monday-UTC, tails log files with multibyte safety and banner recovery, and renders the operator-decision panel (including the refusal format). It imports a sibling sentry_client, which tests must account for via sys.path insertion.

## Related

- produces [[operator-request-notification]] — The refusal format written by the cockpit's operator-decision panel is consumed by operator_request_notify.py.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
