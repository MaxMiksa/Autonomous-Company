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
links:
  - to: snapog-cost-alerting
    relation: validates
    description: Dry-runs the cost-alert cron handler.
  - to: snapog-og-image-service
    relation: validates
    description: Smoke-tests the /og endpoint and cache-cap behavior.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

One-off Bash smoke/dry-run scripts for SnapOG (archived under _archive/snapog/sample/): smoke-test.sh checks /health and /og PNG generation; cache-cap-test.sh verifies the per-key cache cap returns X-Cache: BYPASSED after CAP distinct keys; alerts-dry-run.sh seeds 500 cache-miss usage_events via recursive SQL CTE and triggers the cron handler via /__scheduled to verify alert logic without sending real webhooks. These are one-off validations for specific fixes, not maintained tests.

## Related

- validates [[snapog-cost-alerting]] — Dry-runs the cost-alert cron handler.
- validates [[snapog-og-image-service]] — Smoke-tests the /og endpoint and cache-cap behavior.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
