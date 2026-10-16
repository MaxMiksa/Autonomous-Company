---
name: MCP probe invariants
slug: mcp-probe-invariants
type: concept
sources:
  - path: tests/test_mcp_probe.sh
    hash: 07482a8311b81667003a304c3741feed20e311f1e28263a5bb3bcc5599e962ce
sources_digest: 30360d88aad0bab433575ab05149700a3fb89604ae38e77b068196f3a5916ae8
links:
  - to: mcp-config-key-handling
    relation: validates
    description: Runs against the generated config and manifest to catch drift before boot.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The deterministic MCP probe requires at least one proven readcheck per server (with exemptions like browseros), enforces that the manifest's destructive tool list exactly matches live tools, and checks the denylist covers both base tools and per-server tool names. Readcheck failures include isError, error-prefixed content, and server death; readchecks referencing nonexistent tools are rejected.

## Related

- validates [[mcp-config-key-handling]] — Runs against the generated config and manifest to catch drift before boot.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
