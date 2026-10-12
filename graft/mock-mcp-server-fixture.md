---
name: Mock MCP server fixture
slug: mock-mcp-server-fixture
type: file
sources:
  - path: tests/fixtures/mock_mcp_server.py
    hash: e5124ccf90e18331b1e81557000a0bf0cc13e1fd7f0412250c5f37fb08e23021
sources_digest: d41c2c418dd351366a8be5287cd5eda2e5b636c4f854c074f9b15af1153ce6e9
links: []
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

A minimal JSON-RPC 2.0 mock MCP stdio server used as a test fixture for jcode-mcp-probe.py, configured entirely through environment variables (MOCK_TOOLS, MOCK_CALL_TEXT, MOCK_CALL_ISERROR, MOCK_DIE). Ignores notifications, silently skips malformed JSON, always returns a result even for unknown methods — a deterministic, controllable stand-in for a real MCP server in integration tests.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
