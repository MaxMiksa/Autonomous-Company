---
name: Directive & Registry Management
slug: directive-registry-management
type: system
sources:
  - path: dashboard/server.py
    hash: 1b4eb273b98a9ab8c80543f5a060add328626bc2af171f5d96927d6b0f72159c
  - path: scripts/analyst/opportunity-analyst-jcode.sh
    hash: 44d5ba1f3c85dcd90621856e6db86bd24a0602c8ecbaa9ef36c4018abb28b33b
  - path: scripts/analyst/opportunity-analyst.sh
    hash: a0a766435a1f9e501b97cca96bb30314440de72fd569313488d3b80d5f9c55a5
sources_digest: 5386242e9c7fae5a6be367061f62016333f76717126618a9c25e685913218479
links:
  - to: cockpit-dashboard
    relation: implements
    description: >-
      server.py's read_directive/write_directive and operator request ledger
      functions are implemented through this layer.
  - to: opportunity-analyst-pipeline
    relation: implements
    description: Analyst uses directive_writer.py for safe restore of human-directive.md.
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
---
<!-- context:generated:start -->
## Summary

The shared file-management layer for human-directive.md, consensus.md, and the operator request ledger. directive_writer.py (referenced by both the dashboard and analyst) manages the human-directive.md file with append-not-replace semantics to prevent data loss; operator decisions are formatted to match the verifier's exact parsing expectations; the analyst pipeline snapshots/restores with hash checks and never auto-applies directives.

## Related

- implements [[cockpit-dashboard]] — server.py's read_directive/write_directive and operator request ledger functions are implemented through this layer.
- implements [[opportunity-analyst-pipeline]] — Analyst uses directive_writer.py for safe restore of human-directive.md.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
