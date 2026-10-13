---
name: MCP probe contract
slug: mcp-probe-contract
type: concept
sources:
  - path: tests/test_mcp_probe.sh
    hash: 07482a8311b81667003a304c3741feed20e311f1e28263a5bb3bcc5599e962ce
sources_digest: 30360d88aad0bab433575ab05149700a3fb89604ae38e77b068196f3a5916ae8
links:
  - to: mcp-configuration-key-handling
    relation: part_of
    description: jcode-mcp-probe.py is part of the MCP stack
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The deterministic MCP probe requires at least one proven readcheck per server (with an exemption mechanism for servers like browseros), enforces that the manifest's destructive tool list exactly matches live tools, and checks that the denylist covers both base tools and per-server tool names. Readcheck failures include isError, error-prefixed content, and server death. The probe runs against a mock stdio server with no model or network.

## Related

- part of [[mcp-configuration-key-handling]] — jcode-mcp-probe.py is part of the MCP stack
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
