---
name: Waitlist Capture
slug: waitlist-capture
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

Cloudflare Pages Function for POST /api/waitlist capturing email signups, validating, deduplicating against a KV namespace (email:<address> key), and storing a JSON record with source, IP, user agent, and timestamp. Returns 503 if the KV binding is missing, prompting client fallback to Formspree or mailto. Normalizes emails to lowercase, truncates source/user-agent strings, sets cache-control: no-store, and returns a deduped: true flag on duplicates.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
