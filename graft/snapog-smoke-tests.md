---
name: SnapOG Smoke Tests
slug: snapog-smoke-tests
type: system
sources:
  - path: projects/_archive/snapog/sample/alerts-dry-run.sh
    hash: fabd322c673a2e7f93273116221eac10392cdbf3d6cd8eb5457e6c960b67797c
  - path: projects/_archive/snapog/sample/cache-cap-test.sh
    hash: c11830b054136c0d367415ca1a62bc16312be6ec69c45fc217b2fda9bf8a67bc
  - path: projects/_archive/snapog/sample/smoke-test.sh
    hash: 0a140d23218574add9c22c524d6ff03aea85a205f4806261fc0791a4b73c144f
sources_digest: ce9cb2a773c1290423006a58fe8d649723cb56a07022127ba072ed0d87b79c56
links:
  - to: snapog-og-image-service
    relation: validates
    description: Smoke tests verify the /og endpoint and cache-cap behavior
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

One-off validation scripts for specific fixes rather than maintained tests: a basic smoke test checking /health and /og PNG size, a cache-cap test firing CAP+EXTRA unique-title requests to verify X-Cache: BYPASSED after the per-key cap, and an alerts dry-run that seeds 500 cache-miss rows via recursive SQL CTE and triggers /__scheduled to verify alert logic without real webhooks. The dry-run writes throwaway rows into local Miniflare D1 state resettable by deleting .wrangler/state/v3/d1.

## Related

- validates [[snapog-og-image-service]] — Smoke tests verify the /og endpoint and cache-cap behavior
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
