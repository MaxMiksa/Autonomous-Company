---
name: MCP Key & Server Verification
slug: mcp-key-server-verification
type: system
sources:
  - path: scripts/ops/verify-mcp-keys.py
    hash: a35c1f35481876cedc5bb4cf0c7fd4eceaea1c85e57d3c28e87560b3f9f342db
  - path: tests/fixtures/mock_mcp_server.py
    hash: e5124ccf90e18331b1e81557000a0bf0cc13e1fd7f0412250c5f37fb08e23021
sources_digest: 57b335385305c0fa3319e1138b99b4f1e0f67c78040445ae393ff0732d828f7f
links:
  - to: auto-loop-harness
    relation: validates
    description: Verifies the MCP servers the loop depends on receive well-formed keys
generator:
  version: 1
covers:
  - symbol: loop_env
    kind: function
    at: 'scripts/ops/verify-mcp-keys.py:L39-L51'
  - symbol: main
    kind: function
    at: 'scripts/ops/verify-mcp-keys.py:L54-L75'
---
<!-- context:generated:start -->
## Summary

Tooling to verify MCP server configuration and key shape after deploys. verify-mcp-keys.py inspects the running auto-loop.sh process environment via /proc/<pid>/environ rather than its own shell (avoiding docker exec's fresh-shell false failures), checking shape predicates (Airtable keys contain a dot, Linear starts with lin_api_, Context7 starts with ctx7sk) and never printing key values. A mock MCP stdio server fixture provides a deterministic JSON-RPC stand-in for integration tests, configured entirely via environment variables including MOCK_DIE to simulate unreachable servers.

## Related

- validates [[auto-loop-harness]] — Verifies the MCP servers the loop depends on receive well-formed keys
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
