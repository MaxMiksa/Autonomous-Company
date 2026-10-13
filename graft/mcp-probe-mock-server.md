---
name: MCP Probe & Mock Server
slug: mcp-probe-mock-server
type: system
sources:
  - path: tests/fixtures/mock_mcp_server.py
    hash: e5124ccf90e18331b1e81557000a0bf0cc13e1fd7f0412250c5f37fb08e23021
  - path: tests/test_browse_extract.sh
    hash: 37b269657d3077acf85e81540cd0355f9e97b432f0e6e1d973c2dfc170a887a6
sources_digest: 8768a5d08b7dac2f877ec71835de3f1487d1dd4ef20a6494b2b649037a913d22
links:
  - to: airtable-access-wrappers
    relation: validates
    description: MCP probe verifies server reachability and key shape after deploy
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The jcode-mcp-probe tool and its deterministic mock stdio server fixture. The mock implements minimal JSON-RPC 2.0 over newline-delimited stdin/stdout, configured entirely via env vars (MOCK_TOOLS, MOCK_CALL_TEXT, MOCK_CALL_ISERROR, MOCK_DIE), ignores notifications, and always returns a result even for unknown methods — a controllable stand-in for integration tests.

## Related

- validates [[airtable-access-wrappers]] — MCP probe verifies server reachability and key shape after deploy
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
