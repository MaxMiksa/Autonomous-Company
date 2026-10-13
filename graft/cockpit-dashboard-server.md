---
name: Cockpit Dashboard Server
slug: cockpit-dashboard-server
type: system
sources:
  - path: dashboard/server.py
    hash: 999b44bc7671293e78906611b1dfd46bcf6efcc520ed92623a17281766a7fc85
sources_digest: 8b82355bba156c61c76505ae335656f264eff4fc117d0a477f2c27a30456f883
links:
  - to: cockpit-dashboard
    relation: produces
    description: Serves the REST endpoints and state files the browser panel consumes.
  - to: directive-writer
    relation: uses
    description: >-
      Routes all human-directive.md writes through the deterministic locking
      writer.
  - to: sentry-client
    relation: uses
    description: Reports server errors via capture_exception.
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
---
<!-- context:generated:start -->
## Summary

ThreadingHTTPServer-based local web service monitoring/controlling the autonomous loop across Windows (WSL), macOS, and Linux. Platform abstraction via get_host_profile() pairing each OS with a script runner and status parser. Routes directive writes through the single deterministic scripts/core/directive_writer.py (locks, gates on in-flight PENDING, refuses clobber unless allow_pending). SETTINGS_SPEC whitelist prevents persisting secrets to logs/runtime.env. Logs read via 256KB tail window because auto-loop.log grows across redeploys; decoding tries utf-8, utf-8-sig, gb18030, cp936 for Windows. Analyst trigger uses file-based ANALYST_RUN_REQUEST because cockpit runs inside app container and cannot start host-side cron containers. Error reporting via external sentry_client.

## Related

- produces [[cockpit-dashboard]] — Serves the REST endpoints and state files the browser panel consumes.
- uses [[directive-writer]] — Routes all human-directive.md writes through the deterministic locking writer.
- uses [[sentry-client]] — Reports server errors via capture_exception.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
