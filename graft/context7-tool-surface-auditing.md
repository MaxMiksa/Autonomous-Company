---
name: Context7 & Tool-Surface Auditing
slug: context7-tool-surface-auditing
type: system
sources:
  - path: tests/test_context7_check.sh
    hash: d4fc93cf6b456038f23e1e756019a7fa1b47a344b0385bc5cd3d3a5536834733
  - path: tests/test_cost_audit_tool_surface.py
    hash: 801b92c715ca95cef9c34ab863f87fa443c8abcc65ba03237a934f5aed78121a
sources_digest: f5613dd65499069f9c04777d4ceaad66df6cb614e12788018b8ed5d6e425e020
links:
  - to: cycle-cost-turn-auditing
    relation: part_of
    description: cost-audit.py is part of the cost auditing family
generator:
  version: 1
covers:
  - symbol: ok
    kind: function
    at: 'tests/test_cost_audit_tool_surface.py:L24-L25'
  - symbol: 'no'
    kind: function
    at: 'tests/test_cost_audit_tool_surface.py:L28-L31'
---
<!-- context:generated:start -->
## Summary

Auditors that ensure external library imports are accompanied by Context7 documentation lookups and that the advertised tool surface subtracts deny-listed tools. context7-check.py flags assistant cycles that import external libraries without a Context7 lookup, but must stay silent on stdlib-only ops scripts to avoid false alarms that erode trust. cost-audit.py's tool-surface logic subtracts tools hidden by JCODE_TOOLS_DENY from the 'advertised' column rather than counting the raw MCP schema-cache, which previously caused OPREQ-1 false positives.

## Related

- part of [[cycle-cost-turn-auditing]] — cost-audit.py is part of the cost auditing family
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
