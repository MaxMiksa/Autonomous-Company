---
name: Harness Loop Core
slug: harness-loop-core
type: system
sources:
  - path: tests/test_active_window.sh
    hash: fcd17dad9794b155cb623d85a88dd74bf10c12961df71a37f446f030958135fd
  - path: tests/test_auto_loop_consensus_prune.sh
    hash: 9d97a8dfec49f5829637619f996e57ab7e0773498a9788855dacc61a10d51375
  - path: tests/test_auto_loop_ledger_guard.sh
    hash: 707a207723f0b5c371c39d0fbc5a14170b4c74bb9c893f550186797aebcf440f
  - path: tests/test_auto_loop_work_window.sh
    hash: 7bb4ebdcaef7c71820540195fab59c8c657ff11f525429105bb0376a30405369
  - path: tests/test_budget_gates.sh
    hash: 8d96846319108d7f4c41477e346d7ae803743be23e0bc4ca6de30e9f117e99c9
  - path: tests/test_ccusage_failclosed.sh
    hash: 366b96bee74416db05cc9752919b04304a49f5121d5802920a26641b196ef706
  - path: tests/test_codex_spend_sources.sh
    hash: 38e285a908cfdba71566f50ec2429fed8dc40ccdaaf68886e24e27399bba5bef
sources_digest: 2dd78516d34c5ab8431049466cf3e95e0cc7bbbae578d6701eee302cba740f09
links:
  - to: cycle-cost-risk-auditing
    relation: uses
    description: Wires turn-bloat-brake and tool-usage-audit as post-cycle hooks.
  - to: production-surface-guard
    relation: validates
    description: >-
      auto-loop.sh is a protected surface; its budget/spend functions are
      extracted and tested by the budget-gate suites.
  - to: state-staleness-measurement
    relation: uses
    description: Invokes state-snapshot per cycle.
  - to: work-window-brake
    relation: uses
    description: Wires work-window.py and the watchdog into the cycle flow.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The central auto-loop harness (scripts/core/auto-loop.sh) that drives autonomous cycles: business-hours gating (_window_active), cycle engine selection, budget gates, spend recording, and the wiring of all operational guards (ledger-guard, turn-bloat-brake, work-window, consensus-prune, watchdog) as post-cycle hooks. It is the integration point that all ops scripts hook into, and the target of the prod-mechanism-guard's protection. Budget gates follow the APP-263 decision with engine-specific gates, rollover independence, and fail-closed ccusage measurement where degraded reads never lower a same-period prior observation.

## Related

- uses [[cycle-cost-risk-auditing]] — Wires turn-bloat-brake and tool-usage-audit as post-cycle hooks.
- validates [[production-surface-guard]] — auto-loop.sh is a protected surface; its budget/spend functions are extracted and tested by the budget-gate suites.
- uses [[state-staleness-measurement]] — Invokes state-snapshot per cycle.
- uses [[work-window-brake]] — Wires work-window.py and the watchdog into the cycle flow.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
