---
name: MCP key fallback
slug: mcp-key-fallback
type: concept
sources:
  - path: scripts/core/jcode-mcp-config.py
    hash: 7e5496c29eae3646af4874f74f0d70e22230b762a74acdfb7e38e93197b41aca
  - path: tests/test_mcp_key_fallback.sh
    hash: 21c4be05f1922a08fa185aaa94f73941a785d5f380b7770431bdee7bf78115d6
sources_digest: 233ee8be6589fb9c92cf6076fbfd45d1a8dd4a5644771def8e811c24208d024d
links:
  - to: mcp-configuration-system
    relation: part_of
    description: The fallback is embedded in the generated .mcp.json server commands.
generator:
  version: 1
covers:
  - symbol: expand
    kind: function
    at: 'scripts/core/jcode-mcp-config.py:L96-L108'
  - symbol: sub
    kind: function
    at: 'scripts/core/jcode-mcp-config.py:L100-L105'
  - symbol: convert
    kind: function
    at: 'scripts/core/jcode-mcp-config.py:L111-L162'
  - symbol: main
    kind: function
    at: 'scripts/core/jcode-mcp-config.py:L165-L276'
---
<!-- context:generated:start -->
## Summary

The design decision that MCP server keys are resolved via a Keychain fallback on macOS (when a ${VAR} placeholder or unset variable arrives) but never inside the container where the security binary is absent. Keys are deliberately placed in the ENV block rather than argv to avoid leaking secrets via ps. The fallback branch must be genuinely present in the config, and a real key passes through untouched without invoking security.

## Related

- part of [[mcp-configuration-system]] — The fallback is embedded in the generated .mcp.json server commands.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
