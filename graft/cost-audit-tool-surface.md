---
name: Cost-audit tool surface
slug: cost-audit-tool-surface
type: file
sources:
  - path: tests/test_cost_audit_tool_surface.py
    hash: 801b92c715ca95cef9c34ab863f87fa443c8abcc65ba03237a934f5aed78121a
sources_digest: 65c78c93d0cfb2571cd60fa948df8ff16076750450177467d92e46909a85f8f9
links: []
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

The §5 tool-surface logic in scripts/ops/cost-audit.py computes the 'advertised' column by subtracting tools hidden by the JCODE_TOOLS_DENY deny-list rather than counting the raw MCP schema-cache (which previously caused OPREQ-1 false positives). The auto-loop.sh default yields exactly 15 browseros and 2 context7 denied tools while keeping mcp__browseros__tabs available; an environment override of JCODE_TOOLS_DENY takes precedence.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
