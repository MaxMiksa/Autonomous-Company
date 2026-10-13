---
name: Auto Loop
slug: auto-loop
type: system
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
sources_digest: 5d1a44e9153a8e6e17b6bed2b5ec2c61057b12b9050bab1c1441797cb182daa4
links:
  - to: cockpit-dashboard-server
    relation: produces
    description: Writes the state files and logs the dashboard reads via /api/status.
  - to: container-entrypoint-state-persistence
    relation: part_of
    description: Launched by docker-entrypoint.sh as a background process.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

24/7 autonomous orchestration loop running Claude or Codex CLI engines in fresh sessions with memories/consensus.md as cross-cycle relay. Four-gate budget model (per-engine 5-hour, daily, weekly caps) backed by idempotent spend ledger; quota-aware router can alternate engines; tier ladder for round-robin model/effort selection; circuit breaker with cooldown for repeated failures. Two harnesses: legacy cli and newer jcode Rust binary, with comprehensive tool denylist (denylist over allowlist due to jcode MCP tool enumeration issues). Safety: prompt guardrail verification against PROMPT.md, framework anchor checks, usage-limit detection with anchored error patterns, permanent Codex auth failure detection disabling engine for the run. LOOP_BOOT_ID for unique run IDs across container restarts.

## Related

- produces [[cockpit-dashboard-server]] — Writes the state files and logs the dashboard reads via /api/status.
- part of [[container-entrypoint-state-persistence]] — Launched by docker-entrypoint.sh as a background process.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
