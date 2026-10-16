---
name: SnapOG Cache-Cap Abuse Prevention
slug: snapog-cache-cap-abuse-prevention
type: concept
sources:
  - path: projects/_archive/snapog/migrations/0003_cache_key_tracking.sql
    hash: a672bc9c2f87bedb83312ef869d3ea29305f96bcca7241131ce1130edcb4ee75
  - path: projects/_archive/snapog/sample/cache-cap-test.sh
    hash: c11830b054136c0d367415ca1a62bc16312be6ec69c45fc217b2fda9bf8a67bc
  - path: projects/_archive/snapog/src/index.ts
    hash: c484536a0f66188fa0ac986f34c605540b32efb599ec1ae08d091b89a20d2954
  - path: projects/_archive/snapog/src/og/render.ts
    hash: c74a09fcf98afae74090c3b72b8b4c7f84252e7f0aca090d1418352cd48d8094
  - path: projects/_archive/snapog/src/types.ts
    hash: 1551e13c618a1b8ceaa8b5189318810934889c1d4e822425cb830e7efb45bc15
sources_digest: c99ed0ae9e1afb5120e81607c17457145b7bc3a6b0c7297a8f2fa63cd7c99476
links:
  - to: snapog-d1-schema
    relation: depends_on
    description: Uses the api_key_cache_keys table.
  - to: snapog-og-image-service
    relation: implements
    description: Enforced in the /og route via trackCacheKeyAndCheckCap.
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
  - symbol: generateOGImage
    kind: function
    at: 'projects/_archive/snapog/src/og/render.ts:L11-L23'
  - symbol: buildCacheKey
    kind: function
    at: 'projects/_archive/snapog/src/og/render.ts:L26-L37'
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

Design decision (G8 fix) capping distinct R2 cache keys per API key per billing month at MONTHLY_CACHE_KEY_CAP=30. Beyond the cap, /og still renders and counts usage but skips OG_CACHE.put() and returns X-Cache: BYPASSED, trading cache efficiency for bounded storage growth. Tracked in the api_key_cache_keys table with a composite primary key on (api_key_id, cache_key, billing_month) for deduplication. The cache key itself is a deterministic SHA-256 of alphabetically-sorted JSON params (with watermark flag merged in) to avoid hash instability from object key ordering.

## Related

- depends on [[snapog-d1-schema]] — Uses the api_key_cache_keys table.
- implements [[snapog-og-image-service]] — Enforced in the /og route via trackCacheKeyAndCheckCap.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
