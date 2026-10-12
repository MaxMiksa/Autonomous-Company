# scripts/ops/verify-mcp-keys.py · [[mcp-key-verification]]

Post-deploy check that each MCP server's key is present and well-shaped in the loop process's own environment, without ever printing a secret.

- loop_env · function · L39-L51 — Reads the auto-loop process's /proc environ to obtain the actual environment MCP children are spawned from, avoiding the fresh-shell env gotcha.
- main · function · L54-L75 — Validates each configured MCP server's key against its expected shape and reports PASS/FAIL per server, returning a failing exit code.
