---
name: Cycle Cost & Usage Auditing
slug: cycle-cost-usage-auditing
type: system
sources:
  - path: scripts/ops/tool-usage-audit.py
    hash: 73a75d68bab3e0b42e31ad3d268b44a8c7ac168b91c6a8d1b2f1b3cd4cdba975
  - path: scripts/ops/turn-audit.py
    hash: 11d7f3bda3ad3eafbc2874669f8bb2169288e01cba152cc213fd28d51f8cf77f
  - path: scripts/ops/web-research-cost.py
    hash: 24d7735b6dc6defa0f80e75aeee37a13a40d4df43e9b38539be02df6fe23cbf2
  - path: tests/test_context7_check.sh
    hash: d4fc93cf6b456038f23e1e756019a7fa1b47a344b0385bc5cd3d3a5536834733
  - path: tests/test_cost_audit_tool_surface.py
    hash: 801b92c715ca95cef9c34ab863f87fa443c8abcc65ba03237a934f5aed78121a
sources_digest: 2775d7956d849b1a3b701c07a6de6ae3d3b49c8093964fbc87ea0076ad4bc763
links:
  - to: airtable-access-wrappers
    relation: validates
    description: >-
      cost-audit's advertised-tool column subtracts JCODE_TOOLS_DENY-hidden
      tools to avoid false positives
  - to: fail-closed-harness-brakes
    relation: produces
    description: turn-audit verdicts feed turn-bloat-brake's streak counter
generator:
  version: 1
covers:
  - symbol: calls_from_ndjson
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L43-L65'
  - symbol: categorize
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L68-L121'
  - symbol: main
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L124-L251'
  - symbol: dump
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L177-L190'
  - symbol: ts_of
    kind: function
    at: 'scripts/ops/turn-audit.py:L74-L78'
  - symbol: scan
    kind: function
    at: 'scripts/ops/turn-audit.py:L81-L112'
  - symbol: floor_usd
    kind: function
    at: 'scripts/ops/turn-audit.py:L115-L121'
  - symbol: summary_line
    kind: function
    at: 'scripts/ops/turn-audit.py:L124-L142'
  - symbol: main
    kind: function
    at: 'scripts/ops/turn-audit.py:L145-L158'
  - symbol: is_web
    kind: function
    at: 'scripts/ops/web-research-cost.py:L43-L44'
  - symbol: analyse
    kind: function
    at: 'scripts/ops/web-research-cost.py:L47-L76'
  - symbol: main
    kind: function
    at: 'scripts/ops/web-research-cost.py:L79-L161'
  - symbol: ok
    kind: function
    at: 'tests/test_cost_audit_tool_surface.py:L24-L25'
  - symbol: 'no'
    kind: function
    at: 'tests/test_cost_audit_tool_surface.py:L28-L31'
---
<!-- context:generated:start -->
## Summary

Per-cycle and per-turn cost/risk measurement tools that parse jcode NDJSON event streams and logs. tool-usage-audit.py reassembles tool calls from the jcode event stream (tool_start plus streamed deltas) and dedups on filename+size+mtime because the cycle counter restarts on container restart; web-research-cost.py corrects the naive assumption that a fetch costs once by scoring residual cost as output_tokens × turns_after_it; turn-audit.py classifies sessions as ok/CHATTY/BLOATED anchored to risk (duration and cost) rather than chattiness, since msgs_max was a redundant signal that doubled false alarms. All use only the standard library and always exit 0.

## Related

- validates [[airtable-access-wrappers]] — cost-audit's advertised-tool column subtracts JCODE_TOOLS_DENY-hidden tools to avoid false positives
- produces [[fail-closed-harness-brakes]] — turn-audit verdicts feed turn-bloat-brake's streak counter
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
