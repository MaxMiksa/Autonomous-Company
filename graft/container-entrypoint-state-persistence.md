---
name: Container Entrypoint & State Persistence
slug: container-entrypoint-state-persistence
type: system
sources:
  - path: docker-entrypoint.sh
    hash: fbc2010d8d1d9dda2bc7ebd72fba1d674136624f968ff2f453bf7bbb894de017
sources_digest: 4859f8b1dfb24f857df1d999107a7d92d7c4d14a2c247976ae81cbb021029d23
links:
  - to: autonomous-loop
    relation: uses
    description: Launches scripts/core/auto-loop.sh as a background process
  - to: cockpit-dashboard
    relation: uses
    description: Launches dashboard/server.py as a background process
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

PID-1 bootstrap that drops privileges via gosu, stamps a boot-epoch file for the loop's MCP-config freshness gate, applies operator overrides from runtime.env (parsed literally to avoid shell-special-character corruption), and launches the dashboard and auto-loop as background processes, restarting the container if either exits. Persists state across redeploys by symlinking docs/ and .claude/skills/ into the memories volume, relocating CLAUDE_CONFIG_DIR and CODEX_HOME onto the logs volume, and seeding Codex auth only on first boot to avoid token rotation 401s. A set +e guard around wait -n ensures a non-zero child exit still produces a diagnostic naming the dead process.

## Related

- uses [[autonomous-loop]] — Launches scripts/core/auto-loop.sh as a background process
- uses [[cockpit-dashboard]] — Launches dashboard/server.py as a background process
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
