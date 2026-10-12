---
name: Autonomous Loop
slug: autonomous-loop
type: system
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
sources_digest: 5d1a44e9153a8e6e17b6bed2b5ec2c61057b12b9050bab1c1441797cb182daa4
links:
  - to: cockpit-dashboard
    relation: produces
    description: >-
      The loop's state (LOOP_COUNT, ERROR_COUNT, STATUS, ENGINE, MODEL) is read
      by the dashboard and compact-report.py via the cockpit state file
  - to: container-entrypoint-state-persistence
    relation: depends_on
    description: >-
      Boot-epoch file stamped by entrypoint gates the loop's MCP-config
      freshness check
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The 24/7 orchestration loop that continuously runs Claude or Codex CLI engines in fresh sessions with memories/consensus.md as the cross-cycle relay. Implements a four-gate budget model (per-engine 5-hour, daily, weekly caps) backed by an idempotent spend ledger, a quota-aware engine router, a tier ladder for round-robin model/effort selection, and a circuit breaker with cooldown. Supports legacy cli and jcode harnesses with a tool denylist (preferred over allowlist due to MCP tool enumeration issues), prompt guardrail verification, usage-limit detection, and permanent Codex auth failure detection that disables the engine for the run.

## Related

- produces [[cockpit-dashboard]] — The loop's state (LOOP_COUNT, ERROR_COUNT, STATUS, ENGINE, MODEL) is read by the dashboard and compact-report.py via the cockpit state file
- depends on [[container-entrypoint-state-persistence]] — Boot-epoch file stamped by entrypoint gates the loop's MCP-config freshness check
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
