---
name: SnapOG Cost Alerts
slug: snapog-cost-alerts
type: system
sources:
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
sources_digest: fe1d8fd6fcb0f308eb0c4072f436e2986ea169f87521e188c20ca981540b20fa
links:
  - to: snapog-d1-schema
    relation: uses
    description: 'Queries usage_events, api_keys for metrics.'
  - to: snapog-worker
    relation: part_of
    description: Cron entry point invoked by the worker's scheduled handler.
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

Cron-triggered cost-alerting system (every 6h) running five independent checks: D1 writes/day (assuming 2 writes per request), 14-day cache hit rate, new signups in 30 days, active users, R2 storage bytes (via Cloudflare GraphQL analytics API). Thresholds isolated in one file (ALERT_THRESHOLDS) sourced from CFO cost model so numbers can be revised without touching check logic; severity escalates to critical at 1.5× threshold. Checks deliberately isolated — thrown error logged and treated as no alert to prevent false positives. Webhook delivery short-circuits on empty alerts, falls back to log-only when ALERT_WEBHOOK_URL unset; network failures caught not thrown. GraphQL client returns null on any failure so callers skip storage checks rather than false-alert.

## Related

- uses [[snapog-d1-schema]] — Queries usage_events, api_keys for metrics.
- part of [[snapog-worker]] — Cron entry point invoked by the worker's scheduled handler.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
