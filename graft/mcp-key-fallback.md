---
name: MCP key fallback
slug: mcp-key-fallback
type: concept
sources:
  - path: tests/test_mcp_key_fallback.sh
    hash: 21c4be05f1922a08fa185aaa94f73941a785d5f380b7770431bdee7bf78115d6
sources_digest: 0c0222525a7f47e855e3eae01f1df1201123dd2371c32c6c36c82e8cfcd267e2
links:
  - to: mcp-config-probe-system
    relation: part_of
    description: the fallback is embedded in the generated MCP config
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The .mcp.json MCP server config embeds a Keychain fallback that fires on macOS when a ${VAR} placeholder or unset variable is encountered, but must never fire inside the container where the security binary does not exist. Keys are deliberately placed in ENV rather than argv to avoid leaking secrets via ps. Context7 uses a stdio server reading CONTEXT7_API_KEY from the environment.

## Related

- part of [[mcp-config-probe-system]] — the fallback is embedded in the generated MCP config
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
