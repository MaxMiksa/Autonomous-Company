---
name: SnapOG Worker
slug: snapog-worker
type: system
sources:
  - path: projects/_archive/snapog/src/index.ts
    hash: c484536a0f66188fa0ac986f34c605540b32efb599ec1ae08d091b89a20d2954
  - path: projects/_archive/snapog/src/types.ts
    hash: 1551e13c618a1b8ceaa8b5189318810934889c1d4e822425cb830e7efb45bc15
sources_digest: 3a502edd4ac88332d9c5d9708afe48ce4227dfd0fbbe3aa4b9aebdc3c5ff6165
links:
  - to: snapog-cost-alerts
    relation: uses
    description: Scheduled cron triggers runCostAlertCheck.
  - to: snapog-d1-schema
    relation: uses
    description: 'Persists users, api_keys, usage_events, api_key_cache_keys in D1.'
  - to: snapog-og-rendering
    relation: uses
    description: >-
      Calls generateOGImage and buildCacheKey for image generation and
      deterministic cache keys.
generator:
  version: 1
covers:
  - symbol: sha256
    kind: function
    at: 'projects/_archive/snapog/src/index.ts:L21-L29'
  - symbol: generateRawKey
    kind: function
    at: 'projects/_archive/snapog/src/index.ts:L31-L35'
  - symbol: htmlResponse
    kind: function
    at: 'projects/_archive/snapog/src/index.ts:L37-L42'
  - symbol: resolveApiKey
    kind: function
    at: 'projects/_archive/snapog/src/index.ts:L45-L56'
  - symbol: billingMonthISO
    kind: function
    at: 'projects/_archive/snapog/src/index.ts:L61-L64'
  - symbol: maybeResetUsage
    kind: function
    at: 'projects/_archive/snapog/src/index.ts:L67-L83'
  - symbol: trackCacheKeyAndCheckCap
    kind: function
    at: 'projects/_archive/snapog/src/index.ts:L90-L110'
  - symbol: recordUsage
    kind: function
    at: 'projects/_archive/snapog/src/index.ts:L113-L130'
  - symbol: scheduled
    kind: method
    at: 'projects/_archive/snapog/src/index.ts:L360-L370'
  - symbol: Tier
    kind: type
    at: 'projects/_archive/snapog/src/types.ts:L3-L3'
  - symbol: ApiKey
    kind: interface
    at: 'projects/_archive/snapog/src/types.ts:L16-L27'
  - symbol: OGParams
    kind: interface
    at: 'projects/_archive/snapog/src/types.ts:L29-L37'
  - symbol: Env
    kind: interface
    at: 'projects/_archive/snapog/src/types.ts:L39-L49'
---
<!-- context:generated:start -->
## Summary

Hono-based Cloudflare Worker generating Open Graph images on demand. Routes: GET /og (validate API key, enforce monthly usage limits, cache to R2), / and /register (landing + key creation with waitlist for paid tiers since Stripe isn't wired), /dashboard (usage stats), scheduled cron for cost alerts. API keys hashed (SHA-256) before storage, never stored raw; usage counted even on cache hits; R2 writes bypassed when per-key cache-key cap exceeded (still renders and counts, returns X-Cache: BYPASSED); waitUntil for fire-and-forget ops; free-tier watermark enforced; input params length-limited. Monthly rollover via maybeResetUsage tied to usage_reset_at.

## Related

- uses [[snapog-cost-alerts]] — Scheduled cron triggers runCostAlertCheck.
- uses [[snapog-d1-schema]] — Persists users, api_keys, usage_events, api_key_cache_keys in D1.
- uses [[snapog-og-rendering]] — Calls generateOGImage and buildCacheKey for image generation and deterministic cache keys.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
