---
name: Autonomous Loop Orchestrator
slug: autonomous-loop-orchestrator
type: system
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
sources_digest: 5d1a44e9153a8e6e17b6bed2b5ec2c61057b12b9050bab1c1441797cb182daa4
links:
  - to: auto-company-container-entrypoint
    relation: part_of
    description: Launched as a background process by docker-entrypoint.sh.
  - to: cockpit-dashboard
    relation: produces
    description: Writes state to auto-loop.log and consensus.md that the dashboard reads.
  - to: opportunity-analyst
    relation: uses
    description: Consumes human-directive.md produced by the analyst promotion gate.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The 24/7 autonomous orchestration loop (scripts/core/auto-loop.sh) that continuously runs Claude or Codex CLI engines in fresh sessions with memories/consensus.md as the cross-cycle relay. Implements a four-gate budget model (per-engine 5-hour, daily, weekly caps) backed by an idempotent spend ledger, a quota-aware engine router, a tier ladder for model/effort selection, and a circuit breaker with cooldown. Supports both the legacy cli harness and the newer jcode Rust binary, with a tool denylist (over allowlist, due to jcode MCP tool enumeration issues), prompt guardrail verification against PROMPT.md, framework anchor checks, and permanent Codex auth failure detection that disables the engine for the run. Uses LOOP_BOOT_ID for unique run IDs across container restarts.

## Related

- part of [[auto-company-container-entrypoint]] — Launched as a background process by docker-entrypoint.sh.
- produces [[cockpit-dashboard]] — Writes state to auto-loop.log and consensus.md that the dashboard reads.
- uses [[opportunity-analyst]] — Consumes human-directive.md produced by the analyst promotion gate.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
