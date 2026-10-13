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

Cloudflare Pages Function for POST /api/waitlist capturing email signups. Validates email, deduplicates against WAITLIST KV namespace, stores JSON record (email, source, IP, user agent, timestamp). Returns 503 if KV binding missing, prompting client fallback to Formspree or mailto. Normalizes emails to lowercase, truncates source/user-agent to fixed lengths, email:<address> key for dedup, cache-control: no-store on all responses, deduped: true flag on duplicates.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
