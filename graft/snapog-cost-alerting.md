---
name: SnapOG Cost Alerting
slug: snapog-cost-alerting
type: system
sources:
  - path: projects/_archive/snapog/sample/alerts-dry-run.sh
    hash: fabd322c673a2e7f93273116221eac10392cdbf3d6cd8eb5457e6c960b67797c
  - path: projects/_archive/snapog/src/alerts/check.ts
    hash: fa0fdacdc3a2b495e86f2e70be76d1cadba5f829c78f39010a53d479eb5192c4
  - path: projects/_archive/snapog/src/alerts/graphql.ts
    hash: a8559345be8a04feec2111b7af71ba3158a630457b91af9fe39620b1008fa9d2
  - path: projects/_archive/snapog/src/alerts/index.ts
    hash: d65033194377f0ea1537c03e0dbe39571fbb24cd551c9993c20a0167284f2820
  - path: projects/_archive/snapog/src/alerts/thresholds.ts
    hash: 4331a806e43a7f426bd69778ffaafb0324ab5237ef6f12f16e2f730c724087d2
  - path: projects/_archive/snapog/src/alerts/webhook.ts
    hash: 518ec45652bc5010bbd34856e527e2dc9c2dfa525aea151ff467f3a802c9da81
sources_digest: a023a03dd2af6e7e9df9fb798dd0f07e79cfd170b044341747face1efa394741
links:
  - to: snapog-og-image-service
    relation: validates
    description: Checks usage metrics from the same D1 database and R2 bucket
generator:
  version: 1
covers:
  - symbol: AlertSeverity
    kind: type
    at: 'projects/_archive/snapog/src/alerts/check.ts:L10-L10'
  - symbol: Alert
    kind: interface
    at: 'projects/_archive/snapog/src/alerts/check.ts:L12-L18'
  - symbol: checkD1WritesPerDay
    kind: function
    at: 'projects/_archive/snapog/src/alerts/check.ts:L27-L44'
  - symbol: checkCacheHitRate
    kind: function
    at: 'projects/_archive/snapog/src/alerts/check.ts:L46-L71'
  - symbol: checkNewSignups
    kind: function
    at: 'projects/_archive/snapog/src/alerts/check.ts:L73-L89'
  - symbol: checkActiveUsers
    kind: function
    at: 'projects/_archive/snapog/src/alerts/check.ts:L91-L105'
  - symbol: checkR2Storage
    kind: function
    at: 'projects/_archive/snapog/src/alerts/check.ts:L107-L126'
  - symbol: runAllChecks
    kind: function
    at: 'projects/_archive/snapog/src/alerts/check.ts:L131-L150'
  - symbol: R2StorageSample
    kind: interface
    at: 'projects/_archive/snapog/src/alerts/graphql.ts:L8-L12'
  - symbol: fetchR2BucketStorage
    kind: function
    at: 'projects/_archive/snapog/src/alerts/graphql.ts:L17-L93'
  - symbol: runCostAlertCheck
    kind: function
    at: 'projects/_archive/snapog/src/alerts/index.ts:L8-L14'
  - symbol: ThresholdKey
    kind: type
    at: 'projects/_archive/snapog/src/alerts/thresholds.ts:L27-L27'
  - symbol: AlertPayload
    kind: interface
    at: 'projects/_archive/snapog/src/alerts/webhook.ts:L8-L13'
  - symbol: postAlerts
    kind: function
    at: 'projects/_archive/snapog/src/alerts/webhook.ts:L15-L42'
---
<!-- context:generated:start -->
## Summary

A cron-triggered (every 6h) cost-alerting pipeline with five independent checks against D1 (D1 writes/day estimated at 2 per request, 14-day cache hit rate, new signups in 30d, active users, R2 storage via a thin GraphQL client to Cloudflare Analytics). Thresholds are isolated in one file sourced from the CFO cost model so the CFO can revise numbers without touching check logic; severity escalates to critical at 1.5x threshold. Checks are deliberately isolated — a thrown error is logged and treated as no alert to prevent false positives — and delivery is log-only when ALERT_WEBHOOK_URL is unset, with network failures caught rather than thrown.

## Related

- validates [[snapog-og-image-service]] — Checks usage metrics from the same D1 database and R2 bucket
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
