---
name: spending control mechanisms
slug: spending-control-mechanisms
type: system
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_discretionary_budget.sh
    hash: 32b2f12385f1bf8cc0984fc89d1181074406a1726028d2705d2224759cf6de7e
  - path: tests/test_tier_ladder_daily.sh
    hash: d0bfb4ace48e1fa9665e17059be3f618b46fda0dcf432544a6bb16c07a3ed8db
sources_digest: bf50292fffc8496b272f5e60ec2df1722baaedc0de0e626d98184f4ca7b57aeb
links: []
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The layered spending-control stack in auto-loop.sh: idle detection based on snapshot text 'DELTA: none', a discretionary daily cap that injects a warning line into the prompt once spend reaches a threshold, and the daily-budget tier ladder (APP-263) that selects model tiers per engine. The idle check fails open (unavailable snapshot treated as not idle), the ledger sum ignores non-JSON lines and missing files, and the cap comparison uses >= so an exact match triggers the warning.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
