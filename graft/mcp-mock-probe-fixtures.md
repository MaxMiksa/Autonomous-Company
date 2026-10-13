---
name: MCP Mock & Probe Fixtures
slug: mcp-mock-probe-fixtures
type: system
sources:
  - path: tests/fixtures/mock_mcp_server.py
    hash: e5124ccf90e18331b1e81557000a0bf0cc13e1fd7f0412250c5f37fb08e23021
  - path: tests/test_browse_extract.sh
    hash: 37b269657d3077acf85e81540cd0355f9e97b432f0e6e1d973c2dfc170a887a6
sources_digest: 8768a5d08b7dac2f877ec71835de3f1487d1dd4ef20a6494b2b649037a913d22
links:
  - to: auto-loop-harness
    relation: validates
    description: >-
      Fixtures exercise the MCP JSON-RPC protocol the harness's MCP servers
      speak
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Test fixtures for MCP integration: mock_mcp_server.py is a deterministic JSON-RPC 2.0 stdio server configured entirely via env vars (MOCK_TOOLS, MOCK_CALL_TEXT, MOCK_CALL_ISERROR, MOCK_DIE) used to test jcode-mcp-probe.py, and test_browse_extract.sh uses a fake MCP gateway HTTP server to validate browse-extract.py offline, asserting the critical invariant that the browser tab is always closed even on error paths.

## Related

- validates [[auto-loop-harness]] — Fixtures exercise the MCP JSON-RPC protocol the harness's MCP servers speak
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
