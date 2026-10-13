---
name: dashboard server
slug: dashboard-server
type: system
sources:
  - path: dashboard/server.py
    hash: 1b4eb273b98a9ab8c80543f5a060add328626bc2af171f5d96927d6b0f72159c
  - path: tests/test_dashboard_server.py
    hash: 6f1dcc68a7aea1f92cea60faa92f88dfbfc4aa33b949784f2e31f716a588e4e7
sources_digest: f87046a53333e8dc3b50eaa62bd7e263e52440b70d3ca62a43cfbaa4ec2fec95
links: []
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
  - symbol: _directive_writer_module
    kind: function
    at: 'dashboard/server.py:L321-L336'
  - symbol: directive_sections
    kind: function
    at: 'dashboard/server.py:L339-L358'
  - symbol: as_directive_section
    kind: function
    at: 'dashboard/server.py:L361-L382'
  - symbol: read_directive
    kind: function
    at: 'dashboard/server.py:L385-L421'
  - symbol: _section
    kind: function
    at: 'dashboard/server.py:L396-L407'
  - symbol: DirectiveRefused
    kind: class
    at: 'dashboard/server.py:L424-L425'
  - symbol: write_directive
    kind: function
    at: 'dashboard/server.py:L428-L466'
  - symbol: parse_proposed_authorization
    kind: function
    at: 'dashboard/server.py:L495-L504'
  - symbol: read_operator_requests
    kind: function
    at: 'dashboard/server.py:L507-L542'
  - symbol: _decisions_audit
    kind: function
    at: 'dashboard/server.py:L545-L552'
  - symbol: write_operator_decision
    kind: function
    at: 'dashboard/server.py:L555-L641'
  - symbol: _parse_env_file
    kind: function
    at: 'dashboard/server.py:L644-L656'
  - symbol: read_ideas
    kind: function
    at: 'dashboard/server.py:L659-L677'
  - symbol: read_tool_usage
    kind: function
    at: 'dashboard/server.py:L680-L717'
  - symbol: read_analysis
    kind: function
    at: 'dashboard/server.py:L720-L738'
  - symbol: analyst_trigger_state
    kind: function
    at: 'dashboard/server.py:L741-L748'
  - symbol: analyst_run_now
    kind: function
    at: 'dashboard/server.py:L751-L777'
  - symbol: read_directive_templates
    kind: function
    at: 'dashboard/server.py:L795-L802'
  - symbol: read_settings
    kind: function
    at: 'dashboard/server.py:L805-L847'
  - symbol: write_settings
    kind: function
    at: 'dashboard/server.py:L850-L896'
  - symbol: _proc_cmdline
    kind: function
    at: 'dashboard/server.py:L899-L904'
  - symbol: _proc_ppid
    kind: function
    at: 'dashboard/server.py:L907-L914'
  - symbol: read_hold
    kind: function
    at: 'dashboard/server.py:L921-L944'
  - symbol: set_hold
    kind: function
    at: 'dashboard/server.py:L947-L984'
  - symbol: wake_loop
    kind: function
    at: 'dashboard/server.py:L987-L1045'
  - symbol: trigger_redeploy
    kind: function
    at: 'dashboard/server.py:L1048-L1084'
  - symbol: _week_start_epoch
    kind: function
    at: 'dashboard/server.py:L1100-L1107'
  - symbol: _ccusage_compute
    kind: function
    at: 'dashboard/server.py:L1110-L1165'
  - symbol: _run
    kind: function
    at: 'dashboard/server.py:L1116-L1124'
  - symbol: _is_codex
    kind: function
    at: 'dashboard/server.py:L1139-L1141'
  - symbol: read_ccusage
    kind: function
    at: 'dashboard/server.py:L1168-L1188'
  - symbol: _bg
    kind: function
    at: 'dashboard/server.py:L1180-L1185'
  - symbol: read_engine_runtime
    kind: function
    at: 'dashboard/server.py:L1191-L1288'
  - symbol: _window_cutoff_epoch
    kind: function
    at: 'dashboard/server.py:L1291-L1319'
  - symbol: read_cost_summary
    kind: function
    at: 'dashboard/server.py:L1322-L1453'
  - symbol: _last_budget_gate
    kind: function
    at: 'dashboard/server.py:L1456-L1464'
  - symbol: read_tail
    kind: function
    at: 'dashboard/server.py:L1467-L1474'
  - symbol: parse_sections
    kind: function
    at: 'dashboard/server.py:L1477-L1492'
  - symbol: parse_int
    kind: function
    at: 'dashboard/server.py:L1495-L1499'
  - symbol: parse_positive_int
    kind: function
    at: 'dashboard/server.py:L1502-L1507'
  - symbol: parse_key_values
    kind: function
    at: 'dashboard/server.py:L1510-L1517'
  - symbol: blank_parsed
    kind: function
    at: 'dashboard/server.py:L1520-L1544'
  - symbol: parse_windows_status_output
    kind: function
    at: 'dashboard/server.py:L1547-L1629'
  - symbol: parse_macos_status_output
    kind: function
    at: 'dashboard/server.py:L1632-L1668'
  - symbol: read_state_file_pairs
    kind: function
    at: 'dashboard/server.py:L1671-L1679'
  - symbol: run_status_command
    kind: function
    at: 'dashboard/server.py:L1682-L1685'
  - symbol: run_dashboard_action
    kind: function
    at: 'dashboard/server.py:L1688-L1700'
  - symbol: parse_status_output
    kind: function
    at: 'dashboard/server.py:L1703-L1705'
  - symbol: gather_status_payload
    kind: function
    at: 'dashboard/server.py:L1708-L1728'
  - symbol: read_graft_freshness
    kind: function
    at: 'dashboard/server.py:L1731-L1741'
  - symbol: DashboardHandler
    kind: class
    at: 'dashboard/server.py:L1744-L2049'
  - symbol: _json
    kind: method
    at: 'dashboard/server.py:L1745-L1752'
  - symbol: _text
    kind: method
    at: 'dashboard/server.py:L1754-L1763'
  - symbol: _serve_file
    kind: method
    at: 'dashboard/server.py:L1765-L1769'
  - symbol: do_GET
    kind: method
    at: 'dashboard/server.py:L1771-L1776'
  - symbol: _do_GET
    kind: method
    at: 'dashboard/server.py:L1778-L1844'
  - symbol: _read_body
    kind: method
    at: 'dashboard/server.py:L1846-L1853'
  - symbol: do_POST
    kind: method
    at: 'dashboard/server.py:L1855-L1860'
  - symbol: _do_POST
    kind: method
    at: 'dashboard/server.py:L1862-L1925'
  - symbol: _handle_operator_decision
    kind: method
    at: 'dashboard/server.py:L1927-L1967'
  - symbol: _handle_directive
    kind: method
    at: 'dashboard/server.py:L1969-L2015'
  - symbol: _handle_settings
    kind: method
    at: 'dashboard/server.py:L2017-L2046'
  - symbol: log_message
    kind: method
    at: 'dashboard/server.py:L2048-L2049'
  - symbol: main
    kind: function
    at: 'dashboard/server.py:L2052-L2074'
  - symbol: DashboardServerTests
    kind: class
    at: 'tests/test_dashboard_server.py:L28-L211'
  - symbol: test_windows_not_running_maps_to_stopped
    kind: method
    at: 'tests/test_dashboard_server.py:L29-L53'
  - symbol: test_windows_not_installed_daemon_maps_correctly
    kind: method
    at: 'tests/test_dashboard_server.py:L55-L75'
  - symbol: test_macos_active_configured_running_maps_correctly
    kind: method
    at: 'tests/test_dashboard_server.py:L77-L113'
  - symbol: test_macos_inactive_configured_stopped_and_guardian_without_caffeinate
    kind: method
    at: 'tests/test_dashboard_server.py:L115-L136'
  - symbol: test_macos_not_installed_maps_correctly
    kind: method
    at: 'tests/test_dashboard_server.py:L138-L158'
  - symbol: test_windows_start_uses_powershell_runner
    kind: method
    at: 'tests/test_dashboard_server.py:L160-L170'
  - symbol: test_macos_stop_uses_shell_runner_with_pause_daemon
    kind: method
    at: 'tests/test_dashboard_server.py:L172-L184'
  - symbol: test_refresh_uses_status_script
    kind: method
    at: 'tests/test_dashboard_server.py:L186-L195'
  - symbol: test_invalid_log_tail_lines_fall_back_to_default
    kind: method
    at: 'tests/test_dashboard_server.py:L197-L200'
  - symbol: test_unsupported_host_raises
    kind: method
    at: 'tests/test_dashboard_server.py:L202-L211'
  - symbol: EngineRuntimeParsingTests
    kind: class
    at: 'tests/test_dashboard_server.py:L236-L369'
  - symbol: _run
    kind: method
    at: 'tests/test_dashboard_server.py:L239-L244'
  - symbol: fake_read
    kind: function
    at: 'tests/test_dashboard_server.py:L240-L241'
  - symbol: test_claude_cycle_reports_its_effort
    kind: method
    at: 'tests/test_dashboard_server.py:L246-L254'
  - symbol: test_codex_cycle_still_reports_codex_effort
    kind: method
    at: 'tests/test_dashboard_server.py:L256-L260'
  - symbol: test_window_budget_and_ladders_take_the_latest_boot
    kind: method
    at: 'tests/test_dashboard_server.py:L262-L272'
  - symbol: test_legacy_tier_line_without_claude_effort_still_parses
    kind: method
    at: 'tests/test_dashboard_server.py:L274-L285'
  - symbol: _settings
    kind: method
    at: 'tests/test_dashboard_server.py:L293-L297'
  - symbol: test_settings_source_runtime_env_wins
    kind: method
    at: 'tests/test_dashboard_server.py:L299-L304'
  - symbol: test_settings_source_container_when_absent_from_file
    kind: method
    at: 'tests/test_dashboard_server.py:L306-L311'
  - symbol: test_settings_source_default_when_nowhere
    kind: method
    at: 'tests/test_dashboard_server.py:L313-L316'
  - symbol: _runtime
    kind: method
    at: 'tests/test_dashboard_server.py:L333-L341'
  - symbol: fake_read
    kind: function
    at: 'tests/test_dashboard_server.py:L334-L335'
  - symbol: test_escalated_cycle_reports_the_escalated_model
    kind: method
    at: 'tests/test_dashboard_server.py:L343-L349'
  - symbol: test_escalation_before_the_tier_line_is_ignored
    kind: method
    at: 'tests/test_dashboard_server.py:L351-L364'
  - symbol: test_codex_cycle_ignores_escalation_entirely
    kind: method
    at: 'tests/test_dashboard_server.py:L366-L369'
  - symbol: WindowCutoffTests
    kind: class
    at: 'tests/test_dashboard_server.py:L372-L433'
  - symbol: setUp
    kind: method
    at: 'tests/test_dashboard_server.py:L380-L387'
  - symbol: tearDown
    kind: method
    at: 'tests/test_dashboard_server.py:L389-L391'
  - symbol: _write
    kind: method
    at: 'tests/test_dashboard_server.py:L393-L397'
  - symbol: test_fresh_blockstart_anchors_the_window
    kind: method
    at: 'tests/test_dashboard_server.py:L399-L405'
  - symbol: test_stale_usage_file_falls_back_to_rolling
    kind: method
    at: 'tests/test_dashboard_server.py:L407-L415'
  - symbol: test_blockstart_older_than_rolling_never_widens_the_window
    kind: method
    at: 'tests/test_dashboard_server.py:L417-L422'
  - symbol: test_missing_or_unparseable_file_falls_back
    kind: method
    at: 'tests/test_dashboard_server.py:L424-L433'
  - symbol: DirectorPanelAppendTests
    kind: class
    at: 'tests/test_dashboard_server.py:L436-L533'
  - symbol: setUp
    kind: method
    at: 'tests/test_dashboard_server.py:L448-L463'
  - symbol: tearDown
    kind: method
    at: 'tests/test_dashboard_server.py:L465-L468'
  - symbol: _w
    kind: method
    at: 'tests/test_dashboard_server.py:L470-L473'
  - symbol: _show
    kind: method
    at: 'tests/test_dashboard_server.py:L475-L478'
  - symbol: _live
    kind: method
    at: 'tests/test_dashboard_server.py:L480-L481'
  - symbol: test_send_on_done_appends_and_keeps_body
    kind: method
    at: 'tests/test_dashboard_server.py:L483-L490'
  - symbol: test_inner_headings_are_demoted_to_one_section
    kind: method
    at: 'tests/test_dashboard_server.py:L492-L499'
  - symbol: test_own_heading_is_kept
    kind: method
    at: 'tests/test_dashboard_server.py:L501-L506'
  - symbol: test_pending_gate_then_allow_pending_appends
    kind: method
    at: 'tests/test_dashboard_server.py:L508-L517'
  - symbol: test_sections_summary_partitions_body
    kind: method
    at: 'tests/test_dashboard_server.py:L519-L525'
  - symbol: test_sections_empty_when_writer_unloadable
    kind: method
    at: 'tests/test_dashboard_server.py:L527-L533'
  - symbol: ReadTextFileTailTests
    kind: class
    at: 'tests/test_dashboard_server.py:L540-L598'
  - symbol: _tmp
    kind: method
    at: 'tests/test_dashboard_server.py:L545-L550'
  - symbol: test_returns_whole_file_when_smaller_than_window
    kind: method
    at: 'tests/test_dashboard_server.py:L552-L556'
  - symbol: test_truncates_to_the_tail_and_drops_the_partial_first_line
    kind: method
    at: 'tests/test_dashboard_server.py:L558-L565'
  - symbol: test_multibyte_seek_does_not_produce_replacement_junk
    kind: method
    at: 'tests/test_dashboard_server.py:L567-L571'
  - symbol: test_missing_file_returns_fallback
    kind: method
    at: 'tests/test_dashboard_server.py:L573-L576'
  - symbol: test_engine_runtime_falls_back_to_full_file_when_banner_is_out_of_window
    kind: method
    at: 'tests/test_dashboard_server.py:L578-L598'
  - symbol: fake_read
    kind: function
    at: 'tests/test_dashboard_server.py:L589-L590'
  - symbol: WeeklyCostWindowTests
    kind: class
    at: 'tests/test_dashboard_server.py:L601-L645'
  - symbol: _summary_for
    kind: method
    at: 'tests/test_dashboard_server.py:L606-L610'
  - symbol: _stamp
    kind: method
    at: 'tests/test_dashboard_server.py:L613-L614'
  - symbol: test_week_window_splits_old_and_new_costs
    kind: method
    at: 'tests/test_dashboard_server.py:L616-L635'
  - symbol: test_unstamped_cost_line_counts_all_time_only
    kind: method
    at: 'tests/test_dashboard_server.py:L637-L645'
  - symbol: LiveBudgetGateDisplayTests
    kind: class
    at: 'tests/test_dashboard_server.py:L648-L682'
  - symbol: test_engine_runtime_parses_live_gate_banner_last_match
    kind: method
    at: 'tests/test_dashboard_server.py:L654-L666'
  - symbol: test_cost_summary_carries_last_budget_gate_line
    kind: method
    at: 'tests/test_dashboard_server.py:L668-L682'
  - symbol: GraftFreshnessTests
    kind: class
    at: 'tests/test_dashboard_server.py:L685-L714'
  - symbol: test_absent_file_reports_unavailable
    kind: method
    at: 'tests/test_dashboard_server.py:L689-L693'
  - symbol: test_valid_status_passthrough
    kind: method
    at: 'tests/test_dashboard_server.py:L695-L705'
  - symbol: test_malformed_json_reports_unavailable
    kind: method
    at: 'tests/test_dashboard_server.py:L707-L714'
---
<!-- context:generated:start -->
## Summary

dashboard/server.py powers the Auto Company operations dashboard: status parsing for Windows/macOS/Linux hosts, action dispatch (start/stop/refresh), engine runtime state extraction from persistent logs, settings resolution, spend window calculation anchored to ccusage's blockStart, and directive file management via the real directive_writer.py subprocess.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
