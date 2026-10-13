---
name: send-gate & rfq-send
slug: send-gate-rfq-send
type: system
sources:
  - path: tests/test_rfq_send.sh
    hash: da4d25d4be3529f89c4c62e9b7099278b95d98a4336a9762bfe6c01e31030a97
  - path: tests/test_send_gate.sh
    hash: 4d0f03bd1b3e73a289e87cf0a56b25499b131e48fac01098b3f1d81755cb190d
sources_digest: b9c595d31d560e66deb88d9d01033008661c0417a03fba124ffaf1729c7c63a4
links:
  - to: prod-mechanism-guard
    relation: validates
    description: >-
      Both scripts must be registered in prod-mechanism-guard.py and pass
      --check-sync
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

scripts/ops/send-gate.py and rfq-send.py are the fail-closed outbound communication guards. send-gate refuses on any unknown/error across 20 scenarios (caps, duplicates, opt-out, non-Qualified status, G4 failure, body-leak scanner for internal markers, exact normalized firm-name matching for g4_live, phase-check scoping to first-contact). rfq-send is buyer-side, requires §15 sponsor approval, forbids G4 gate usage, and targets the RFQ table (tblzcGP7kNfkmPDGJ) not the frozen tender table. Both are registered in prod-mechanism-guard.py.

## Related

- validates [[prod-mechanism-guard]] — Both scripts must be registered in prod-mechanism-guard.py and pass --check-sync
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
