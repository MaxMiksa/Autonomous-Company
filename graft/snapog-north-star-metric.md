---
name: SnapOG North-Star Metric
slug: snapog-north-star-metric
type: concept
sources:
  - path: docs/operations/north-star-metric-query.sql
    hash: 0ef7a67fdb263a3fb09f795cc5a35372721265b7ef1f6200c5ccc369109f7ac6
sources_digest: 91dcfb3b617798695902ce25230879b0ebdf6c4ac53fe80d36c1db48d76a29a9
links:
  - to: snapog-d1-schema
    relation: depends_on
    description: Runs against the snapog-db D1 database.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Canonical SQL for Weekly Active Producers (WAP): counts distinct api_key_id values that generated at least one non-cached OG image (cache_hit=0) within a reporting window. Cache hits are excluded because they represent edge-served static responses with near-zero marginal cost and no signal of new demand. Three read-only queries: Q1 daily 30-day time-series, Q2 7/30-day scorecards, Q3 per-key leaderboard for testimonial candidates and free-tier keys nearing monthly_limit. Days with zero traffic produce no rows (zero-filling must happen client-side).

## Related

- depends on [[snapog-d1-schema]] — Runs against the snapog-db D1 database.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
