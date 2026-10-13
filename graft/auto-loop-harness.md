---
name: Auto-Loop Harness
slug: auto-loop-harness
type: system
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
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
sources_digest: 5ff8ef140fd914714e9cd8f63e5b9ae81d4fc87198bdcc0fd848b5cd5217656e
links:
  - to: deploy-environment-verification
    relation: depends_on
    description: verify-mcp-keys.py inspects its process environment; WSL daemon runs it
  - to: prod-mechanism-guard
    relation: depends_on
    description: >-
      auto-loop.sh is a protected surface; the guard blocks unplanned edits to
      it
  - to: turn-bloat-brake
    relation: uses
    description: >-
      Invokes ledger-guard.py and turn-bloat-brake.py, guarded against set -e
      failures
  - to: work-window-brake
    relation: uses
    description: >-
      Gates idle-skip on _workwin_open and captures the window exit code
      set-e-safe
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

scripts/core/auto-loop.sh is the central autonomous cycle harness. It is protected by the prod-mechanism guard and drives the budget gates, work-window brake, ledger guard, consensus prune, and turn-bloat brake. Its _window_active() business-hours gate is fail-open (a typo never parks the company), and off-hours ticks must not burn cycle numbers or trigger external calls. Budget gates (APP-263) are engine-specific with rollover independence, duplicate run_id dedup, and fail-closed ccusage reads that never lower a same-period prior observation. Codex spend is summed from two disjoint sources (ccusage + TOTAL_SPEND_LEDGER) rather than maxed, which previously caused real spend to vanish.

## Related

- depends on [[deploy-environment-verification]] — verify-mcp-keys.py inspects its process environment; WSL daemon runs it
- depends on [[prod-mechanism-guard]] — auto-loop.sh is a protected surface; the guard blocks unplanned edits to it
- uses [[turn-bloat-brake]] — Invokes ledger-guard.py and turn-bloat-brake.py, guarded against set -e failures
- uses [[work-window-brake]] — Gates idle-skip on _workwin_open and captures the window exit code set-e-safe
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
