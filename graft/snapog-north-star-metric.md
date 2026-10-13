---
name: SnapOG North-Star Metric
slug: snapog-north-star-metric
type: file
sources:
  - path: docs/operations/north-star-metric-query.sql
    hash: 0ef7a67fdb263a3fb09f795cc5a35372721265b7ef1f6200c5ccc369109f7ac6
sources_digest: 91dcfb3b617798695902ce25230879b0ebdf6c4ac53fe80d36c1db48d76a29a9
links:
  - to: snapog-d1-schema
    relation: depends_on
    description: Queries the D1 schema from migrations/0001_init.sql.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Canonical SQL for Weekly Active Producers (WAP): counts distinct api_key_id values generating at least one non-cached OG image (cache_hit=0) within a reporting window. Three read-only queries: Q1 daily 30-day time-series with active_producers/total_events/cache_hit_ratio; Q2 rolls up 7-day and 30-day scorecards; Q3 per-key leaderboard joining usage_events to api_keys for testimonial candidates and free-tier keys nearing monthly_limit. Core design decision: cache hits excluded from WAP because they represent edge-served static responses with near-zero marginal cost and no signal of new demand. Days with zero traffic produce no rows — zero-filling must happen client-side. Safe to run from dashboard, wrangler d1 execute, or Cloudflare MCP d1_database_query.

## Related

- depends on [[snapog-d1-schema]] — Queries the D1 schema from migrations/0001_init.sql.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
