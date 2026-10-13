# scripts/core/jcode-mcp-config.py · [[mcp-configuration-and-manifest]] [[mcp-configuration-boot-probe]] [[secret-management-runtime-env-keychain]]

Generates jcode's stdio-only MCP config from the repo's .mcp.json, bridging http servers through mcp-remote and skipping OPREQ-A-denied servers, so the loop's tool surface matches what jcode can actually connect to.

- expand · function · L96-L108 — Substitutes ${VAR} references from the environment, returning None if any referenced variable is unset so the caller can skip the server loudly.
- sub · function · L100-L105 — Replacement callback that resolves one ${VAR} match and records it as missing when the environment has no value.
- convert · function · L111-L162 — Rewrites one server spec into a jcode-compatible stdio form, passing stdio servers through and wrapping http/sse servers in an mcp-remote bridge while keeping secrets out of argv.
- main · function · L165-L276 — Reads the source .mcp.json, applies SKIP/OVERRIDE/convert per server, and atomically writes the resulting config plus a freshness stamp, refusing to write empty or partial configs.
