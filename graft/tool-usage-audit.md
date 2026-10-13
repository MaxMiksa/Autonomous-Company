---
name: tool usage audit
slug: tool-usage-audit
type: file
sources:
  - path: tests/test_tool_usage_audit.sh
    hash: 4bdf9378fc2af04ed89fc9559aa1fcc8520846c6847f13302f613ec896bfde6d
sources_digest: cba460eef4963bdc24ab59d1ddd5c9e0777b7c6fa78ddf2ea20f94c8ce1e9ab6
links:
  - to: auto-loop-core-engine
    relation: uses
    description: Consumes cycle-*.ndjson event streams from engine runs
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

scripts/ops/tool-usage-audit.py categorizes jcode NDJSON event streams (handling fragmented tool_input deltas split mid-token), with ledger idempotence and reporting. A rewritten cycle-0001.ndjson (cycle counter resets on container restart) is re-audited rather than deduped by filename; per-MCP-tool-name counts are recorded only for MCP tools (not bash); and browse-extract.py harness usage is counted as browser usage to prevent faking A/B drops. --report exits 0 even when the ndjson directory is missing.

## Related

- uses [[auto-loop-core-engine]] — Consumes cycle-*.ndjson event streams from engine runs
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
