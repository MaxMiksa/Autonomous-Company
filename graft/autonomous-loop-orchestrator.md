---
name: Autonomous Loop Orchestrator
slug: autonomous-loop-orchestrator
type: system
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
sources_digest: 5d1a44e9153a8e6e17b6bed2b5ec2c61057b12b9050bab1c1441797cb182daa4
links:
  - to: cockpit-dashboard
    relation: produces
    description: >-
      Writes .auto-loop-state, auto-loop.log, and runtime.env that the dashboard
      reads; holds from the dashboard pause/resume the loop.
  - to: container-entrypoint-bootstrap
    relation: depends_on
    description: >-
      Boot-epoch file stamped by entrypoint gates the loop's MCP-config
      freshness check.
  - to: opportunity-analyst-pipeline
    relation: uses
    description: >-
      The loop and the analyst share directive_writer.py for safe
      human-directive.md management and consensus.md as the cross-cycle relay.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The 24/7 autonomous orchestration loop (scripts/core/auto-loop.sh) that continuously runs Claude or Codex CLI engines in fresh sessions with memories/consensus.md as the cross-cycle relay. Implements a four-gate budget model (per-engine 5-hour, daily, weekly caps) backed by an idempotent spend ledger, a quota-aware engine router, a tier ladder for model/effort selection, and a circuit breaker with cooldown. Supports legacy cli and jcode harnesses with a tool denylist (preferred over allowlist due to MCP tool enumeration issues), prompt guardrail verification, usage-limit detection with anchored error patterns, and permanent Codex auth failure detection that disables the engine for the run. Uses LOOP_BOOT_ID for unique run IDs across container restarts.

## Related

- produces [[cockpit-dashboard]] — Writes .auto-loop-state, auto-loop.log, and runtime.env that the dashboard reads; holds from the dashboard pause/resume the loop.
- depends on [[container-entrypoint-bootstrap]] — Boot-epoch file stamped by entrypoint gates the loop's MCP-config freshness check.
- uses [[opportunity-analyst-pipeline]] — The loop and the analyst share directive_writer.py for safe human-directive.md management and consensus.md as the cross-cycle relay.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
