---
name: SnapOG Validation Scripts
slug: snapog-validation-scripts
type: system
sources:
  - path: projects/_archive/snapog/sample/alerts-dry-run.sh
    hash: fabd322c673a2e7f93273116221eac10392cdbf3d6cd8eb5457e6c960b67797c
  - path: projects/_archive/snapog/sample/cache-cap-test.sh
    hash: c11830b054136c0d367415ca1a62bc16312be6ec69c45fc217b2fda9bf8a67bc
  - path: projects/_archive/snapog/sample/smoke-test.sh
    hash: 0a140d23218574add9c22c524d6ff03aea85a205f4806261fc0791a4b73c144f
sources_digest: ce9cb2a773c1290423006a58fe8d649723cb56a07022127ba072ed0d87b79c56
links: []
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

One-off Bash smoke/dry-run scripts for SnapOG: smoke-test.sh (basic /health and /og PNG size check), alerts-dry-run.sh (seeds 500 cache-miss usage_events via recursive SQL CTE to trip the 14-day cache-hit-rate threshold, then triggers /__scheduled; writes throwaway rows into local Miniflare D1 state resettable by deleting .wrangler/state/v3/d1), and cache-cap-test.sh (fires CAP+EXTRA requests with unique title params to verify X-Cache: BYPASSED after the per-key cap). Archived under _archive indicating one-off validations rather than maintained tests.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
