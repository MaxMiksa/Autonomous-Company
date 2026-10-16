---
name: Cockpit Dashboard
slug: cockpit-dashboard
type: system
sources:
  - path: dashboard/app.js
    hash: 8aafde35d774227ba4a3ddb2942f07ac42b3245f1be73f3dc1ad30650a64015c
  - path: dashboard/sentry_client.py
    hash: 96977bb6701f18064edb69c783e53bdb73c930c8ddadcd1caf47583b42700df4
  - path: dashboard/server.py
    hash: 6cc54894d69041d5e6f44ab24e5243e157855ebcf007fcb387188e303b85093f
sources_digest: edcf53e9eff087c8fe04f300246fc324a9d034a7097a7a5607be3fe4aebdaeb9
links:
  - to: auto-company-container-entrypoint
    relation: part_of
    description: >-
      Launched as a background process by docker-entrypoint.sh alongside the
      autonomous loop.
  - to: autonomous-loop-orchestrator
    relation: uses
    description: >-
      Reads loop state from auto-loop.log and consensus.md; hold/release
      endpoints pause/resume the loop.
  - to: directive-writer
    relation: uses
    description: write_directive appends via directive_writer.py to avoid data loss.
generator:
  version: 1
covers:
  - symbol: escapeHtml
    kind: function
    at: 'dashboard/app.js:L94-L101'
  - symbol: renderInlineMarkdown
    kind: function
    at: 'dashboard/app.js:L103-L110'
  - symbol: renderMarkdown
    kind: function
    at: 'dashboard/app.js:L112-L194'
  - symbol: closeParagraph
    kind: function
    at: 'dashboard/app.js:L119-L124'
  - symbol: closeList
    kind: function
    at: 'dashboard/app.js:L125-L130'
  - symbol: classForState
    kind: function
    at: 'dashboard/app.js:L196-L218'
  - symbol: applyCardState
    kind: function
    at: 'dashboard/app.js:L220-L223'
  - symbol: renderGraft
    kind: function
    at: 'dashboard/app.js:L225-L248'
  - symbol: formatTime
    kind: function
    at: 'dashboard/app.js:L250-L256'
  - symbol: renderStateList
    kind: function
    at: 'dashboard/app.js:L258-L287'
  - symbol: ladder
    kind: function
    at: 'dashboard/app.js:L264-L264'
  - symbol: fetchStatus
    kind: function
    at: 'dashboard/app.js:L289-L350'
  - symbol: renderCost
    kind: function
    at: 'dashboard/app.js:L352-L400'
  - symbol: usd
    kind: function
    at: 'dashboard/app.js:L353-L353'
  - symbol: renderCcusage
    kind: function
    at: 'dashboard/app.js:L402-L422'
  - symbol: usd
    kind: function
    at: 'dashboard/app.js:L404-L404'
  - symbol: renderHold
    kind: function
    at: 'dashboard/app.js:L428-L438'
  - symbol: setHold
    kind: function
    at: 'dashboard/app.js:L440-L470'
  - symbol: renderDirective
    kind: function
    at: 'dashboard/app.js:L472-L488'
  - symbol: renderDirectiveSections
    kind: function
    at: 'dashboard/app.js:L493-L532'
  - symbol: kb
    kind: function
    at: 'dashboard/app.js:L500-L500'
  - symbol: submitDirective
    kind: function
    at: 'dashboard/app.js:L534-L577'
  - symbol: send
    kind: function
    at: 'dashboard/app.js:L545-L550'
  - symbol: renderSettings
    kind: function
    at: 'dashboard/app.js:L579-L599'
  - symbol: gatherSettings
    kind: function
    at: 'dashboard/app.js:L601-L608'
  - symbol: loadIdeas
    kind: function
    at: 'dashboard/app.js:L611-L631'
  - symbol: loadToolUsage
    kind: function
    at: 'dashboard/app.js:L634-L669'
  - symbol: loadAnalysis
    kind: function
    at: 'dashboard/app.js:L673-L697'
  - symbol: renderAnalystTrigger
    kind: function
    at: 'dashboard/app.js:L701-L714'
  - symbol: runAnalystNow
    kind: function
    at: 'dashboard/app.js:L716-L733'
  - symbol: extractDirective
    kind: function
    at: 'dashboard/app.js:L739-L751'
  - symbol: copyToBtn
    kind: function
    at: 'dashboard/app.js:L753-L761'
  - symbol: loadDirectiveTemplates
    kind: function
    at: 'dashboard/app.js:L775-L807'
  - symbol: loadSettings
    kind: function
    at: 'dashboard/app.js:L810-L818'
  - symbol: saveSettings
    kind: function
    at: 'dashboard/app.js:L820-L849'
  - symbol: setWakeAvailability
    kind: function
    at: 'dashboard/app.js:L855-L862'
  - symbol: wakeLoop
    kind: function
    at: 'dashboard/app.js:L864-L881'
  - symbol: resetAutoTimer
    kind: function
    at: 'dashboard/app.js:L884-L897'
  - symbol: notifiedIds
    kind: function
    at: 'dashboard/app.js:L973-L980'
  - symbol: rememberNotified
    kind: function
    at: 'dashboard/app.js:L982-L989'
  - symbol: renderNotifyButton
    kind: function
    at: 'dashboard/app.js:L991-L1009'
  - symbol: announceNewRequests
    kind: function
    at: 'dashboard/app.js:L1011-L1031'
  - symbol: opreqPanelBusy
    kind: function
    at: 'dashboard/app.js:L1039-L1046'
  - symbol: renderOperatorRequests
    kind: function
    at: 'dashboard/app.js:L1048-L1107'
  - symbol: submitDecision
    kind: function
    at: 'dashboard/app.js:L1109-L1148'
  - symbol: loadOperatorRequests
    kind: function
    at: 'dashboard/app.js:L1150-L1157'
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
---
<!-- context:generated:start -->
## Summary

Local web cockpit UI for the Auto Company Guardian loop. Serves a single-page monitoring interface (dashboard/app.js) over a ThreadingHTTPServer (dashboard/server.py) that dispatches to platform-specific shell/PowerShell scripts for host control, reads state from auto-loop.log, human-directive.md, and operator-requests.md, and exposes endpoints for status, hold/release, directive submission, and settings. Includes a stdlib-only Sentry reporter (dashboard/sentry_client.py) that deliberately avoids sentry-sdk because the container has no pip deps, and is best-effort (never raises). Key invariants: directives are appended via directive_writer.py rather than replaced to avoid data loss; a PENDING directive is never overwritten unless explicitly allowed; operator-set holds are distinguished from loop-latched holds (confirmation dialog before releasing the latter); the analyst trigger writes a request file into a shared volume for a host-side cron watcher.

## Related

- part of [[auto-company-container-entrypoint]] — Launched as a background process by docker-entrypoint.sh alongside the autonomous loop.
- uses [[autonomous-loop-orchestrator]] — Reads loop state from auto-loop.log and consensus.md; hold/release endpoints pause/resume the loop.
- uses [[directive-writer]] — write_directive appends via directive_writer.py to avoid data loss.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
