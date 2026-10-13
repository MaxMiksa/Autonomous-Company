---
name: SnapOG Data Schema
slug: snapog-data-schema
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
    relation: implements
    description: Provides the tables the alert checks query.
  - to: snapog-og-image-service
    relation: implements
    description: >-
      Provides the persistence layer the Worker's API key resolution, usage
      counting, and cache-key cap logic depend on.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Cloudflare D1 schema for SnapOG (migrations 0001-0003): users, api_keys (with key_prefix display + SHA-256 key_hash for secure lookup, tier, monthly quota, usage_reset_at), usage_events (per-request generation records with cache_hit flag), and api_key_cache_keys (distinct cache keys per key per billing month to address R2 storage abuse, G8). Deliberately avoids storing raw keys. billing_month format must stay aligned with the application's month-rollover logic to avoid double-counting; no foreign keys enforced.

## Related

- implements [[snapog-cost-alerting]] — Provides the tables the alert checks query.
- implements [[snapog-og-image-service]] — Provides the persistence layer the Worker's API key resolution, usage counting, and cache-key cap logic depend on.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
