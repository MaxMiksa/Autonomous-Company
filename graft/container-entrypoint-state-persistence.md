---
name: Container Entrypoint & State Persistence
slug: container-entrypoint-state-persistence
type: system
sources:
  - path: docker-entrypoint.sh
    hash: fbc2010d8d1d9dda2bc7ebd72fba1d674136624f968ff2f453bf7bbb894de017
sources_digest: 4859f8b1dfb24f857df1d999107a7d92d7c4d14a2c247976ae81cbb021029d23
links:
  - to: auto-loop
    relation: launches
    description: >-
      Starts scripts/core/auto-loop.sh as a background process and restarts the
      container if it exits.
  - to: cockpit-dashboard-server
    relation: launches
    description: Starts dashboard/server.py as a background process.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

PID-1 bootstrap for the Auto-Company service: drops privileges root→app via gosu, stamps boot-epoch for the loop's MCP-config freshness gate, applies operator overrides from persistent runtime.env (parsed literally to avoid shell-special-char corruption), launches dashboard and auto-loop as background processes, waits on either to exit so container restarts. Persists state across redeploys by symlinking docs/ and .claude/skills/ into the memories volume, relocating CLAUDE_CONFIG_DIR and CODEX_HOME onto the logs volume, seeding Codex auth only on first boot to avoid token-rotation 401s. set +e guard around wait -n so non-zero child exit still produces a diagnostic; trap forwards TERM/INT to all children.

## Related

- launches [[auto-loop]] — Starts scripts/core/auto-loop.sh as a background process and restarts the container if it exits.
- launches [[cockpit-dashboard-server]] — Starts dashboard/server.py as a background process.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
