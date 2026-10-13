# projects/_archive/snapog/src/alerts/graphql.ts · [[snapog-cost-alerts]]

Thin Cloudflare Analytics GraphQL client used only to fetch R2 bucket storage byte counts for alert checks.

- R2StorageSample · interface · L8-L12 — Data holder describing one R2 bucket's storage sample (bucket name plus payload and metadata byte sizes).
- fetchR2BucketStorage · function · L17-L93 — Queries Cloudflare GraphQL for the latest R2 storage sample, returning null on any failure so callers skip the storage check instead of firing a false alert.
