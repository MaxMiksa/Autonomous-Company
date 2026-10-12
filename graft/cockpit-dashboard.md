---
name: Cockpit Dashboard
slug: cockpit-dashboard
type: system
sources:
  - path: dashboard/app.js
    hash: 1a974b1c1d72cf714de69954e840a6335990788860f9442ad1e61fcf6f041ca8
  - path: dashboard/sentry_client.py
    hash: 96977bb6701f18064edb69c783e53bdb73c930c8ddadcd1caf47583b42700df4
  - path: dashboard/server.py
    hash: 999b44bc7671293e78906611b1dfd46bcf6efcc520ed92623a17281766a7fc85
sources_digest: c3eeec88fbadc17427d51f65b1a682adbd4d4eb429313cc3a6c06273f937d76d
links:
  - to: auto-loop-orchestration
    relation: uses
    description: >-
      Polls /api/status and controls the loop via /api/hold and /api/directive;
      reads state files the loop writes.
  - to: directive-writer-gate
    relation: uses
    description: >-
      Routes all human-directive.md writes through
      scripts/core/directive_writer.py which locks and gates on in-flight
      PENDING directives.
  - to: sentry-reporter
    relation: uses
    description: Server error reporting goes through the external sentry_client library.
generator:
  version: 1
covers:
  - symbol: escapeHtml
    kind: function
    at: 'dashboard/app.js:L92-L99'
  - symbol: renderInlineMarkdown
    kind: function
    at: 'dashboard/app.js:L101-L108'
  - symbol: renderMarkdown
    kind: function
    at: 'dashboard/app.js:L110-L192'
  - symbol: closeParagraph
    kind: function
    at: 'dashboard/app.js:L117-L122'
  - symbol: closeList
    kind: function
    at: 'dashboard/app.js:L123-L128'
  - symbol: classForState
    kind: function
    at: 'dashboard/app.js:L194-L216'
  - symbol: applyCardState
    kind: function
    at: 'dashboard/app.js:L218-L221'
  - symbol: renderGraft
    kind: function
    at: 'dashboard/app.js:L223-L246'
  - symbol: formatTime
    kind: function
    at: 'dashboard/app.js:L248-L254'
  - symbol: renderStateList
    kind: function
    at: 'dashboard/app.js:L256-L285'
  - symbol: ladder
    kind: function
    at: 'dashboard/app.js:L262-L262'
  - symbol: fetchStatus
    kind: function
    at: 'dashboard/app.js:L287-L348'
  - symbol: renderCost
    kind: function
    at: 'dashboard/app.js:L350-L398'
  - symbol: usd
    kind: function
    at: 'dashboard/app.js:L351-L351'
  - symbol: renderCcusage
    kind: function
    at: 'dashboard/app.js:L400-L420'
  - symbol: usd
    kind: function
    at: 'dashboard/app.js:L402-L402'
  - symbol: renderHold
    kind: function
    at: 'dashboard/app.js:L426-L436'
  - symbol: setHold
    kind: function
    at: 'dashboard/app.js:L438-L468'
  - symbol: renderDirective
    kind: function
    at: 'dashboard/app.js:L470-L485'
  - symbol: submitDirective
    kind: function
    at: 'dashboard/app.js:L487-L530'
  - symbol: send
    kind: function
    at: 'dashboard/app.js:L498-L503'
  - symbol: renderSettings
    kind: function
    at: 'dashboard/app.js:L532-L552'
  - symbol: gatherSettings
    kind: function
    at: 'dashboard/app.js:L554-L561'
  - symbol: loadIdeas
    kind: function
    at: 'dashboard/app.js:L564-L584'
  - symbol: loadToolUsage
    kind: function
    at: 'dashboard/app.js:L587-L622'
  - symbol: loadAnalysis
    kind: function
    at: 'dashboard/app.js:L626-L650'
  - symbol: renderAnalystTrigger
    kind: function
    at: 'dashboard/app.js:L654-L667'
  - symbol: runAnalystNow
    kind: function
    at: 'dashboard/app.js:L669-L686'
  - symbol: extractDirective
    kind: function
    at: 'dashboard/app.js:L692-L704'
  - symbol: copyToBtn
    kind: function
    at: 'dashboard/app.js:L706-L714'
  - symbol: loadDirectiveTemplates
    kind: function
    at: 'dashboard/app.js:L728-L760'
  - symbol: loadSettings
    kind: function
    at: 'dashboard/app.js:L763-L771'
  - symbol: saveSettings
    kind: function
    at: 'dashboard/app.js:L773-L802'
  - symbol: setWakeAvailability
    kind: function
    at: 'dashboard/app.js:L808-L815'
  - symbol: wakeLoop
    kind: function
    at: 'dashboard/app.js:L817-L834'
  - symbol: resetAutoTimer
    kind: function
    at: 'dashboard/app.js:L837-L850'
  - symbol: notifiedIds
    kind: function
    at: 'dashboard/app.js:L926-L933'
  - symbol: rememberNotified
    kind: function
    at: 'dashboard/app.js:L935-L942'
  - symbol: renderNotifyButton
    kind: function
    at: 'dashboard/app.js:L944-L962'
  - symbol: announceNewRequests
    kind: function
    at: 'dashboard/app.js:L964-L984'
  - symbol: opreqPanelBusy
    kind: function
    at: 'dashboard/app.js:L992-L999'
  - symbol: renderOperatorRequests
    kind: function
    at: 'dashboard/app.js:L1001-L1060'
  - symbol: submitDecision
    kind: function
    at: 'dashboard/app.js:L1062-L1101'
  - symbol: loadOperatorRequests
    kind: function
    at: 'dashboard/app.js:L1103-L1110'
  - symbol: _parse_dsn
    kind: function
    at: 'dashboard/sentry_client.py:L33-L43'
  - symbol: capture_exception
    kind: function
    at: 'dashboard/sentry_client.py:L49-L102'
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

Browser-side SPA controller plus its stdlib-only HTTP server and Sentry reporter. The server (ThreadingHTTPServer) abstracts Windows/macOS/Linux host control, reads/writes state files (human-directive.md, operator-requests/decisions, runtime.env via a SETTINGS_SPEC whitelist that prevents persisting secrets), and exposes REST endpoints (/api/status, /api/hold, /api/directive, /api/ideas, /api/tool-usage). The browser app polls /api/status on a timer, renders live state cards, and provides the only real loop control (setHold) plus a directive editor with an allowPending retry flow to override a live PENDING directive. Notable invariants: log files are read with a 256KB tail window because auto-loop.log grows across redeploys; file decoding tries utf-8/utf-8-sig/gb18030/cp936 for Windows; the consensus panel refuses to overwrite while the operator is reading the full file; the ccusage block fails open (hidden when unavailable); tool-usage is a real table because the proportional Rajdhani font makes character-padding impossible.

## Related

- uses [[auto-loop-orchestration]] — Polls /api/status and controls the loop via /api/hold and /api/directive; reads state files the loop writes.
- uses [[directive-writer-gate]] — Routes all human-directive.md writes through scripts/core/directive_writer.py which locks and gates on in-flight PENDING directives.
- uses [[sentry-reporter]] — Server error reporting goes through the external sentry_client library.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
