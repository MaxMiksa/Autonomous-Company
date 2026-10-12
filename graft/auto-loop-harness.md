---
name: Auto-loop harness
slug: auto-loop-harness
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
  - to: cycle-cost-risk-audit
    relation: produces
    description: The loop writes cycle NDJSON files that the audit scripts parse.
  - to: prod-mechanism-guard
    relation: validates
    description: >-
      auto-loop.sh is a protected surface that the prod-mechanism guard blocks
      unplanned edits to.
  - to: turn-bloat-brake-py-escalation
    relation: uses
    description: The loop invokes the bloat brake's --record and --feedback modes.
  - to: work-window-brake-watchdog
    relation: uses
    description: >-
      The loop gates idle-skip on _workwin_open and wires the watchdog alarm
      post-cycle.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The central orchestration loop (scripts/core/auto-loop.sh) and its operational guards, which the many ops scripts plug into. It runs budget gates (15 behaviors from APP-263), a work-window brake, ledger-guard, consensus-prune hook, and turn-bloat brake, with ccusage spend measurement that is fail-closed (degraded reads never lower a same-period prior observation) and summed from two disjoint sources (ccusage figure + TOTAL_SPEND_LEDGER rows) rather than maxed. The business-hours gate _window_active() must run before select_cycle_engine and before the loop_count increment so off-hours ticks don't burn cycle numbers. This node is grounded in the many test scripts that pin its wiring and contracts.

## Related

- produces [[cycle-cost-risk-audit]] — The loop writes cycle NDJSON files that the audit scripts parse.
- validates [[prod-mechanism-guard]] — auto-loop.sh is a protected surface that the prod-mechanism guard blocks unplanned edits to.
- uses [[turn-bloat-brake-py-escalation]] — The loop invokes the bloat brake's --record and --feedback modes.
- uses [[work-window-brake-watchdog]] — The loop gates idle-skip on _workwin_open and wires the watchdog alarm post-cycle.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
