---
name: MCP Key Verification
slug: mcp-key-verification
type: file
sources:
  - path: scripts/ops/verify-mcp-keys.py
    hash: a35c1f35481876cedc5bb4cf0c7fd4eceaea1c85e57d3c28e87560b3f9f342db
sources_digest: 53579789209d19207ea77c4e9195c8f1f5f66496648a6b53cdcedba956c4bec7
links:
  - to: harness-loop-core
    relation: validates
    description: >-
      Inspects the running auto-loop.sh process environment to confirm MCP
      servers receive well-formed keys after deploy.
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

verify-mcp-keys.py verifies that each MCP server (Airtable, Linear, Context7) receives a well-formed API key after a deploy by inspecting the environment of the running auto-loop.sh process via /proc/<pid>/environ rather than its own shell environment. This avoids docker exec's fresh-shell environment which lacks entrypoint-sourced variables and caused false failures. It never prints key values, only lengths and shape status, and detects whether a server uses a macOS security wrapper.

## Related

- validates [[harness-loop-core]] — Inspects the running auto-loop.sh process environment to confirm MCP servers receive well-formed keys after deploy.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
