---
name: tool usage audit
slug: tool-usage-audit
type: file
sources:
  - path: scripts/ops/tool-usage-audit.py
    hash: 73a75d68bab3e0b42e31ad3d268b44a8c7ac168b91c6a8d1b2f1b3cd4cdba975
  - path: tests/test_tool_usage_audit.sh
    hash: 4bdf9378fc2af04ed89fc9559aa1fcc8520846c6847f13302f613ec896bfde6d
sources_digest: a34a96243cdbd57c7896fc7d5f5a4dde3fcdd8a6a1bca52ea9921948d1a6dab2
links:
  - to: auto-loop-core-engine
    relation: uses
    description: Audits the jcode NDJSON event stream produced by engine cycles
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
---
<!-- context:generated:start -->
## Summary

scripts/ops/tool-usage-audit.py categorizes jcode NDJSON event streams (with deliberately fragmented tool_input deltas split mid-token), counting tools like ctx7, airtable_r/airtable_w (script + MCP combined), linear, browser (harness + MCP), browser_mcp, and graft. Per-MCP-tool-name counts are recorded only for MCP tools (not bash). A second run appends nothing (idempotence); a rewritten cycle-0001.ndjson (cycle counter resets on container restart) is re-audited rather than deduped by filename; --report exits 0 even when the ndjson directory is missing; browse-extract.py harness is counted as browser usage to prevent faking A/B drops.

## Related

- uses [[auto-loop-core-engine]] — Audits the jcode NDJSON event stream produced by engine cycles
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
