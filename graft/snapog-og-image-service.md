---
name: SnapOG OG Image Service
slug: snapog-og-image-service
type: system
sources:
  - path: projects/_archive/snapog/src/dashboard/pages.ts
    hash: 6a33d1b6152ee8ea3ee6f5617105ce757c915627156072dd9cb1f3b78e32b4af
  - path: projects/_archive/snapog/src/index.ts
    hash: c484536a0f66188fa0ac986f34c605540b32efb599ec1ae08d091b89a20d2954
  - path: projects/_archive/snapog/src/og/render.ts
    hash: c74a09fcf98afae74090c3b72b8b4c7f84252e7f0aca090d1418352cd48d8094
  - path: projects/_archive/snapog/src/og/templates.ts
    hash: bfc8c9e61038224564b61c55c627b2d86d9ba2514dd47f64a717e94f0be8b810
  - path: projects/_archive/snapog/src/types.ts
    hash: 1551e13c618a1b8ceaa8b5189318810934889c1d4e822425cb830e7efb45bc15
sources_digest: d4343ceffc68f713a6dcfc6ae45ec31bd030d35d94d34d04ef9190c816f7239c
links:
  - to: snapog-cost-alerting
    relation: uses
    description: Scheduled cron invokes runCostAlertCheck from the alerts module.
  - to: snapog-data-schema
    relation: depends_on
    description: >-
      Uses D1 tables (users, api_keys, usage_events, api_key_cache_keys) for
      persistence and rate limiting.
generator:
  version: 1
covers:
  - symbol: layout
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L340-L355'
  - symbol: nav
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L357-L367'
  - symbol: footer
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L369-L376'
  - symbol: landingPage
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L378-L588'
  - symbol: registerPage
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L590-L628'
  - symbol: keyCreatedPage
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L630-L700'
  - symbol: dashboardPage
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L702-L789'
  - symbol: errorPage
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L791-L805'
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
  - symbol: generateOGImage
    kind: function
    at: 'projects/_archive/snapog/src/og/render.ts:L11-L23'
  - symbol: buildCacheKey
    kind: function
    at: 'projects/_archive/snapog/src/og/render.ts:L26-L37'
  - symbol: StyleObject
    kind: type
    at: 'projects/_archive/snapog/src/og/templates.ts:L6-L6'
  - symbol: VNode
    kind: type
    at: 'projects/_archive/snapog/src/og/templates.ts:L8-L15'
  - symbol: AccentBar
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L18-L33'
  - symbol: Header
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L36-L83'
  - symbol: Footer
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L86-L133'
  - symbol: defaultTemplate
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L136-L202'
  - symbol: blogTemplate
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L205-L286'
  - symbol: articleTemplate
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L289-L461'
  - symbol: buildElement
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L463-L472'
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

A Hono-based Cloudflare Worker (projects/_archive/snapog) that generates Open Graph images on demand. Routes: GET /og (validate API key, enforce monthly limits, cache to R2), / and /register (landing + key creation with waitlist since Stripe isn't wired), /dashboard (usage stats), and a scheduled cron for cost alerts. Key design decisions: API keys are SHA-256 hashed before storage (never raw), usage is counted even on cache hits, R2 writes are bypassed when the per-key monthly cache-key cap (30) is exceeded (still rendering and counting, returning X-Cache: BYPASSED), and waitUntil is used for fire-and-forget operations. The OG renderer produces deterministic SHA-256 cache keys by JSON-stringifying params with sorted keys to avoid hash instability from object key ordering.

## Related

- uses [[snapog-cost-alerting]] — Scheduled cron invokes runCostAlertCheck from the alerts module.
- depends on [[snapog-data-schema]] — Uses D1 tables (users, api_keys, usage_events, api_key_cache_keys) for persistence and rate limiting.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
