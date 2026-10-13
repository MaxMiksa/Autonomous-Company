---
name: SnapOG Waitlist Function
slug: snapog-waitlist-function
type: file
sources:
  - path: projects/_archive/snapog-landing/functions/api/waitlist.ts
    hash: 49b5d66187a49f386d4bee50c1c01042d595e5ebbd5b27c061f1fba4cffeefa0
sources_digest: 2eab55af564b0f608bf8be780ff3a47c7384bb204d191cb437072802784c073f
links: []
generator:
  version: 1
covers:
  - symbol: Env
    kind: interface
    at: 'projects/_archive/snapog-landing/functions/api/waitlist.ts:L12-L14'
  - symbol: Body
    kind: interface
    at: 'projects/_archive/snapog-landing/functions/api/waitlist.ts:L16-L20'
  - symbol: onRequestPost
    kind: function
    at: 'projects/_archive/snapog-landing/functions/api/waitlist.ts:L24-L62'
  - symbol: json
    kind: function
    at: 'projects/_archive/snapog-landing/functions/api/waitlist.ts:L64-L72'
---
<!-- context:generated:start -->
## Summary

Cloudflare Pages Function for POST /api/waitlist capturing email signups for the SnapOG landing page. Validates email, deduplicates against the WAITLIST KV namespace (email:<address> key), stores email/source/IP/user-agent/timestamp, normalizes to lowercase, truncates source and UA strings, and returns 503 if the KV binding is missing so the client falls back to Formspree or mailto. Returns a deduped:true flag when an email already exists to avoid duplicate writes.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
