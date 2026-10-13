---
name: Directive Writer
slug: directive-writer
type: system
sources:
  - path: dashboard/server.py
    hash: 999b44bc7671293e78906611b1dfd46bcf6efcc520ed92623a17281766a7fc85
  - path: scripts/analyst/opportunity-analyst-jcode.sh
    hash: 44d5ba1f3c85dcd90621856e6db86bd24a0602c8ecbaa9ef36c4018abb28b33b
  - path: scripts/analyst/opportunity-analyst.sh
    hash: a0a766435a1f9e501b97cca96bb30314440de72fd569313488d3b80d5f9c55a5
  - path: scripts/analyst/promote_directive.py
    hash: 9c45147f1730fc30545b94a30428d54e0bd40f04506aa3db00614880ec93d677
  - path: scripts/core/directive_writer.py
    hash: 276871ed21c1686f9b10a2179256e93b609c818f77a7b7e5f31a7e6681829da4
  - path: tests/test_directive_section_refs.sh
    hash: 413742241d956ae77feb01e20780757ee86fa63f3699e3926a2ddeea81a53a71
  - path: tests/test_directive_writer.py
    hash: 8246a641c797789b53117ec96cd0a3922bad2d9c5dc9ba873e13daf579f35a73
sources_digest: 7f7792bb7ec8eab2ea546673df02cfda235c7c22464c40c871c4acad0375c880
links:
  - to: auto-loop-core-engine
    relation: uses
    description: >-
      auto-loop reads directive status via _directive_is_pending() and
      escalation logic
  - to: cockpit-dashboard-server
    relation: uses
    description: All directive writes route through this writer.
  - to: directive-promotion-gate
    relation: implements
    description: >-
      The promotion gate writes new directives with PENDING status through this
      writer.
  - to: opportunity-analyst-codex
    relation: uses
    description: Used for safe restore of human-directive.md after analysis.
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
  - symbol: sha256
    kind: function
    at: 'scripts/analyst/promote_directive.py:L91-L92'
  - symbol: audit
    kind: function
    at: 'scripts/analyst/promote_directive.py:L95-L98'
  - symbol: blocked
    kind: function
    at: 'scripts/analyst/promote_directive.py:L101-L104'
  - symbol: notify
    kind: function
    at: 'scripts/analyst/promote_directive.py:L107-L113'
  - symbol: main
    kind: function
    at: 'scripts/analyst/promote_directive.py:L116-L225'
  - symbol: undefined_section_refs
    kind: function
    at: 'scripts/core/directive_writer.py:L100-L109'
  - symbol: now
    kind: function
    at: 'scripts/core/directive_writer.py:L112-L113'
  - symbol: sha
    kind: function
    at: 'scripts/core/directive_writer.py:L116-L117'
  - symbol: read_live
    kind: function
    at: 'scripts/core/directive_writer.py:L120-L126'
  - symbol: body_of
    kind: function
    at: 'scripts/core/directive_writer.py:L129-L136'
  - symbol: audit
    kind: function
    at: 'scripts/core/directive_writer.py:L139-L145'
  - symbol: _telegram_env
    kind: function
    at: 'scripts/core/directive_writer.py:L148-L171'
  - symbol: notify
    kind: function
    at: 'scripts/core/directive_writer.py:L174-L184'
  - symbol: _why_pending
    kind: function
    at: 'scripts/core/directive_writer.py:L187-L215'
  - symbol: backup
    kind: function
    at: 'scripts/core/directive_writer.py:L218-L232'
  - symbol: normalize_ownership
    kind: function
    at: 'scripts/core/directive_writer.py:L235-L281'
  - symbol: atomic_write
    kind: function
    at: 'scripts/core/directive_writer.py:L284-L296'
  - symbol: verify_written
    kind: function
    at: 'scripts/core/directive_writer.py:L299-L303'
  - symbol: Refused
    kind: class
    at: 'scripts/core/directive_writer.py:L306-L307'
  - symbol: live_body
    kind: function
    at: 'scripts/core/directive_writer.py:L312-L315'
  - symbol: split_body
    kind: function
    at: 'scripts/core/directive_writer.py:L318-L337'
  - symbol: section_sizes
    kind: function
    at: 'scripts/core/directive_writer.py:L340-L344'
  - symbol: size_brake
    kind: function
    at: 'scripts/core/directive_writer.py:L347-L363'
  - symbol: _pending_gate
    kind: function
    at: 'scripts/core/directive_writer.py:L366-L382'
  - symbol: _refuse_section_refs
    kind: function
    at: 'scripts/core/directive_writer.py:L385-L393'
  - symbol: with_lock
    kind: function
    at: 'scripts/core/directive_writer.py:L396-L405'
  - symbol: wrapper
    kind: function
    at: 'scripts/core/directive_writer.py:L397-L404'
  - symbol: cmd_write
    kind: function
    at: 'scripts/core/directive_writer.py:L418-L472'
  - symbol: cmd_append
    kind: function
    at: 'scripts/core/directive_writer.py:L476-L504'
  - symbol: cmd_archive
    kind: function
    at: 'scripts/core/directive_writer.py:L508-L572'
  - symbol: cmd_status
    kind: function
    at: 'scripts/core/directive_writer.py:L576-L610'
  - symbol: cmd_restore
    kind: function
    at: 'scripts/core/directive_writer.py:L614-L650'
  - symbol: cmd_show
    kind: function
    at: 'scripts/core/directive_writer.py:L653-L664'
  - symbol: main
    kind: function
    at: 'scripts/core/directive_writer.py:L667-L725'
  - symbol: _refuse_forbidden
    kind: function
    at: 'scripts/core/directive_writer.py:L706-L712'
  - symbol: fn
    kind: function
    at: 'scripts/core/directive_writer.py:L707-L711'
  - symbol: check
    kind: function
    at: 'tests/test_directive_writer.py:L22-L25'
  - symbol: Env
    kind: class
    at: 'tests/test_directive_writer.py:L28-L52'
  - symbol: __init__
    kind: method
    at: 'tests/test_directive_writer.py:L29-L32'
  - symbol: run
    kind: method
    at: 'tests/test_directive_writer.py:L34-L36'
  - symbol: live
    kind: method
    at: 'tests/test_directive_writer.py:L38-L39'
  - symbol: audit
    kind: method
    at: 'tests/test_directive_writer.py:L41-L43'
  - symbol: show
    kind: method
    at: 'tests/test_directive_writer.py:L45-L47'
  - symbol: f
    kind: method
    at: 'tests/test_directive_writer.py:L49-L52'
  - symbol: main
    kind: function
    at: 'tests/test_directive_writer.py:L63-L155'
---
<!-- context:generated:start -->
## Summary

scripts/core/directive_writer.py manages the human-directive.md lifecycle: write, append, status, show --sections, and archive subcommands. It enforces: append refuses non-heading sections (rc 3), the PENDING gate blocks append/archive without --allow-pending (rc 2), undefined § references are rejected, stale body_sha256 checks fail status transitions, archive has a resolver-section guard and prefix-matching rules, and a size brake (DIRECTIVE_BODY_WARN_BYTES/MAX_BYTES) with --force-size override. Backups are created, audit lines written, and the archive file contains verbatim text plus a stamp. undefined_section_refs() guards against the bug that froze directive revision 11 (references to absent §6/§7).

## Related

- uses [[auto-loop-core-engine]] — auto-loop reads directive status via _directive_is_pending() and escalation logic
- uses [[cockpit-dashboard-server]] — All directive writes route through this writer.
- implements [[directive-promotion-gate]] — The promotion gate writes new directives with PENDING status through this writer.
- uses [[opportunity-analyst-codex]] — Used for safe restore of human-directive.md after analysis.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
