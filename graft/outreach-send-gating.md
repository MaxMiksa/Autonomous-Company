---
name: outreach & send gating
slug: outreach-send-gating
type: system
sources:
  - path: tests/test_g4_check.sh
    hash: 426129aa4d430db932523139037190cd1c5106394e917a10fc73e29b823bc4d2
  - path: tests/test_reply_watch.sh
    hash: a1291856a346b22fd46c2d1179ae6602778674b7f930d53c4216e449e286b67f
  - path: tests/test_rfq_reply_watch.sh
    hash: 67f49fb6296af24a61aa9a5b8bae530f3cb2db42d5ef68d6f6c2a5989d073cb0
  - path: tests/test_rfq_send.sh
    hash: da4d25d4be3529f89c4c62e9b7099278b95d98a4336a9762bfe6c01e31030a97
  - path: tests/test_send_gate.sh
    hash: 4d0f03bd1b3e73a289e87cf0a56b25499b131e48fac01098b3f1d81755cb190d
sources_digest: abfe07985fc07b4a5a38c86ee900d682440f2935fb4dfe56262d484fb933d2b8
links:
  - to: prod-mechanism-guard
    relation: depends_on
    description: >-
      rfq-send.py must be registered in prod-mechanism-guard.py and pass
      --check-sync
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The buyer-side outreach stack: send-gate.py (refusal policy for outreach sends), rfq-send.py (RFQ sender), reply-watch.py and rfq-reply-watch.py (outcome watchers), and g4-check.py (company identity matching). Fail-closed across 20+ scenarios: daily/total caps, duplicate outreach, opt-out, non-Qualified status, missing email, G4 failure, TEST rows excluded by STATUS, unrendered rows, GROUP_ROUTED special case, self-contradictory rows, body-leak scanner for internal markers, procurement-phase mismatch, follow-up mode, exact normalized firm-name matching for g4_live, and phase-check scoping to first-contact sends. Reply watchers report replies once and never as silence, flag bounces as delivery failures, and phrase silence as an observation ('hüküm değil') not a verdict. RFQ targets table tblzcGP7kNfkmPDGJ, never the frozen tender table tbl1fZbNmolrEXAMy.

## Related

- depends on [[prod-mechanism-guard]] — rfq-send.py must be registered in prod-mechanism-guard.py and pass --check-sync
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
