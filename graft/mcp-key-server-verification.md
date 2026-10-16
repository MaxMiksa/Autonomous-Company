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
  - to: harness-loop-core
    relation: validates
    description: Verifies MCP keys in the running loop process after deploy.
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

Deploy-time and runtime verification of MCP server health. verify-mcp-keys.py inspects the running auto-loop.sh process environment via /proc/<pid>/environ (not its own shell, avoiding docker exec's fresh-shell false failures) to check each server's key shape (Airtable dot, Linear lin_api_, Context7 ctx7sk). mock_mcp_server.py is a deterministic stdio JSON-RPC fixture for jcode-mcp-probe integration tests, configured entirely via env vars including MOCK_DIE to simulate unreachable servers.

## Related

- validates [[harness-loop-core]] — Verifies MCP keys in the running loop process after deploy.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
