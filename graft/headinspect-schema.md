---
name: HeadInspect Schema
slug: headinspect-schema
type: file
sources:
  - path: projects/headinspect/migrations/0001_hits.sql
    hash: 651c37d5aafbcd41932f5307a9080183fd953c8b5968f3dd2921bf1c379af022
sources_digest: 749d2c2597b768efd8b2d98fa11448a3fea8bb6aa07962bec8ae443dd5bd793b
links:
  - to: headinspect-worker
    relation: implements
    description: Persistence schema the worker writes to.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Schema for the anonymous hit counter: headinspect_hits table with auto-increment id, ISO-8601 checked_at text timestamp, host field. Two supporting indexes (checked_at, host). Binding intentionally left out of wrangler.toml — enabling requires one-line uncomment on both migration and config. Privacy constraint baked in: only hostname stored, never full URL, to prevent query strings leaking PII.

## Related

- implements [[headinspect-worker]] — Persistence schema the worker writes to.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
