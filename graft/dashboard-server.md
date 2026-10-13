---
name: dashboard server
slug: dashboard-server
type: file
sources:
  - path: tests/test_dashboard_server.py
    hash: 6f1dcc68a7aea1f92cea60faa92f88dfbfc4aa33b949784f2e31f716a588e4e7
  - path: tests/test_refusal_format.sh
    hash: 11bf5e9869e2e573b4a897e4df84053e4f58d759d3073a9e058705482cc31ef5
sources_digest: 13985929491af07f744c1fbb1c0f40f5b35036a0926db681811e06a6a192ef7a
links:
  - to: operator-request-resolution
    relation: produces
    description: >-
      Writes operator-decisions.md in the refusal format consumed by
      operator_request_notify.py
generator:
  version: 1
covers:
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

dashboard/server.py powers the Auto Company operations dashboard: status parsing for Windows/macOS/Linux, action dispatch (start/stop/refresh), engine runtime extraction from ever-growing auto-loop.log (latest boot), settings resolution, spend windows anchored to ccusage's blockStart, and directive file management. Writes the operator-decision refusal format (short head line + verbatim text) that operator_request_notify.py parses.

## Related

- produces [[operator-request-resolution]] — Writes operator-decisions.md in the refusal format consumed by operator_request_notify.py
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
