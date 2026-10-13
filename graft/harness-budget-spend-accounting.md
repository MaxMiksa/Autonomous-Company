---
name: Harness Budget & Spend Accounting
slug: harness-budget-spend-accounting
type: system
sources:
  - path: tests/test_budget_gates.sh
    hash: 8d96846319108d7f4c41477e346d7ae803743be23e0bc4ca6de30e9f117e99c9
  - path: tests/test_ccusage_failclosed.sh
    hash: 366b96bee74416db05cc9752919b04304a49f5121d5802920a26641b196ef706
  - path: tests/test_codex_spend_sources.sh
    hash: 38e285a908cfdba71566f50ec2429fed8dc40ccdaaf68886e24e27399bba5bef
sources_digest: c99cd4e5b318e2c1e8842f663946ac4cebec8888e1c1f828afb3dbd4dae0f03f
links:
  - to: fail-closed-harness-brakes
    relation: implements
    description: Budget gates and spend holds are part of the harness's fail-closed braking
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The budget-gate and spend-measurement machinery in auto-loop.sh: 15 budget gates per APP-263, ccusage measurement that is fail-closed (first-ever failure latches a hold and returns NA, degraded reads never lower a same-period prior observation), and Codex spend summed from two disjoint sources (ccusage + TOTAL_SPEND_LEDGER) rather than max, which previously caused real spend to vanish. Weekly resume-time walk counts codex ledger rows and aborts conservatively on malformed amounts.

## Related

- implements [[fail-closed-harness-brakes]] — Budget gates and spend holds are part of the harness's fail-closed braking
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
