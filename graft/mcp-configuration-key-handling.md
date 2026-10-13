---
name: MCP configuration & key handling
slug: mcp-configuration-key-handling
type: system
sources:
  - path: tests/test_jcode_mcp_config.sh
    hash: 3a26837a4685e40b45e3e8593459a69680a7bc6cc7e839f4ceb986c570a27025
  - path: tests/test_mcp_config_manifest_sync.sh
    hash: 372a198973bc97e73dd00c1acafe2fe458887504be2f5ef9849242d6549c1112
  - path: tests/test_mcp_key_fallback.sh
    hash: 21c4be05f1922a08fa185aaa94f73941a785d5f380b7770431bdee7bf78115d6
  - path: tests/test_mcp_probe.sh
    hash: 07482a8311b81667003a304c3741feed20e311f1e28263a5bb3bcc5599e962ce
sources_digest: 81e578683fe3be807e72c1f06d92408015601631b429cc15a49d88cdcdab06ca
links:
  - to: auto-loop-core-engine
    relation: configures
    description: >-
      JCODE_MCP_CONFIG_REQUIRED preflight list in auto-loop.sh must agree with
      the manifest; airtable/linear must be absent from loop config (OPREQ-A
      invariant)
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The MCP server configuration stack: jcode-mcp-config.py generates the loop's MCP config from .mcp.json, keeping secrets in the server spec's env block (never argv, where ps could expose them) and failing closed if a required server's variable is unset. jcode-mcp-probe.py deterministically probes servers against a manifest, requiring at least one proven readcheck per server. A Keychain fallback fires on macOS when a ${VAR} placeholder or unset variable arrives, but never inside the container where the security binary is absent. Manifest/config/preflight sync is enforced to prevent boot crash-loops.

## Related

- configures [[auto-loop-core-engine]] — JCODE_MCP_CONFIG_REQUIRED preflight list in auto-loop.sh must agree with the manifest; airtable/linear must be absent from loop config (OPREQ-A invariant)
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
