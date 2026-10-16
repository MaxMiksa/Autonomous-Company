---
name: SnapOG D1 Schema
slug: snapog-d1-schema
type: system
sources:
  - path: projects/_archive/snapog/migrations/0001_init.sql
    hash: 5a2ecc41dbff948e5d8f895feb80ae4145864f3703776f737cda73c84fec8623
  - path: projects/_archive/snapog/migrations/0002_waitlist.sql
    hash: 541f4f76f6f87aab342fe067acbcc746587f600d1e76028fe97a4c67c8b3202a
  - path: projects/_archive/snapog/migrations/0003_cache_key_tracking.sql
    hash: a672bc9c2f87bedb83312ef869d3ea29305f96bcca7241131ce1130edcb4ee75
sources_digest: 8820226ce02d1d9ebb352867760d54a674115efb44b492597558e611bb10dc93
links:
  - to: snapog-cost-alerting
    relation: uses
    description: Alert checks query usage_events and api_keys.
  - to: snapog-north-star-metric
    relation: depends_on
    description: The WAP queries run against this schema.
  - to: snapog-og-image-service
    relation: depends_on
    description: The Worker reads/writes these tables.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Cloudflare D1 migrations defining the SnapOG data model: users, api_keys (with display-only key_prefix and SHA-256 key_hash for secure lookup, tier, monthly quota, usage count, usage_reset_at for billing cycles), usage_events (per-request generation records with template and cache_hit status), waitlist (pre-Stripe paid-tier signups), and api_key_cache_keys (distinct cache keys per key per billing month, addressing R2 storage abuse G8). Deliberately avoids storing raw keys. The billing_month format must stay aligned with the application's month-rollover logic to avoid double-counting; no foreign keys are enforced.

## Related

- uses [[snapog-cost-alerting]] — Alert checks query usage_events and api_keys.
- depends on [[snapog-north-star-metric]] — The WAP queries run against this schema.
- depends on [[snapog-og-image-service]] — The Worker reads/writes these tables.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
