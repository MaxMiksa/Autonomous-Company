---
name: HeadInspect Data Schema
slug: headinspect-data-schema
type: concept
sources:
  - path: projects/headinspect/migrations/0001_hits.sql
    hash: 651c37d5aafbcd41932f5307a9080183fd953c8b5968f3dd2921bf1c379af022
sources_digest: 749d2c2597b768efd8b2d98fa11448a3fea8bb6aa07962bec8ae443dd5bd793b
links:
  - to: headinspect-header-inspector
    relation: implements
    description: Provides the persistence layer for anonymous hit records.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The anonymous hit counter schema (headinspect_hits) with a deliberate privacy constraint: only the hostname is stored, never the full URL, to prevent query strings from leaking PII. checked_at is stored as ISO-8601 text rather than a native timestamp. The D1 binding is intentionally left out of wrangler.toml — enabling requires a one-line uncomment on both the migration and config.

## Related

- implements [[headinspect-header-inspector]] — Provides the persistence layer for anonymous hit records.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
