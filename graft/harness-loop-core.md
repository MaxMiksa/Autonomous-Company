---
name: Harness Loop Core
slug: harness-loop-core
type: system
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
sources_digest: 5d1a44e9153a8e6e17b6bed2b5ec2c61057b12b9050bab1c1441797cb182daa4
links:
  - to: cycle-cost-bloat-governance
    relation: produces
    description: >-
      Emits the cycle ndjson/log output that turn-audit, web-research-cost, and
      tool-usage-audit consume.
  - to: production-surface-tripwire
    relation: validates
    description: >-
      auto-loop.sh is one of the protected surfaces that prod-mechanism-guard.py
      blocks unplanned writes to.
  - to: state-staleness-probes
    relation: uses
    description: Invokes state-snapshot per-cycle and consumes its DELTA line.
  - to: work-window-brake
    relation: uses
    description: >-
      Wires _workwin_open to gate idle-skip, captures the window exit code
      set-e-safe, and reads WORK_WINDOW_ENABLED live from runtime env.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The central auto-loop.sh harness that drives autonomous cycles, including budget gates, cycle engine selection, work-window integration, and consensus pruning. It is the integration point for most ops scripts and the subject of extensive regression tests. Budget gates are fail-closed (degraded reads never lower a same-period prior observation), spend is summed from two disjoint sources (ccusage + TOTAL_SPEND_LEDGER) rather than maxed, and the off-hours poll default is 900 seconds with the transition logged once.

## Related

- produces [[cycle-cost-bloat-governance]] — Emits the cycle ndjson/log output that turn-audit, web-research-cost, and tool-usage-audit consume.
- validates [[production-surface-tripwire]] — auto-loop.sh is one of the protected surfaces that prod-mechanism-guard.py blocks unplanned writes to.
- uses [[state-staleness-probes]] — Invokes state-snapshot per-cycle and consumes its DELTA line.
- uses [[work-window-brake]] — Wires _workwin_open to gate idle-skip, captures the window exit code set-e-safe, and reads WORK_WINDOW_ENABLED live from runtime env.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
