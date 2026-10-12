---
name: Auto-Company Site Pages Functions
slug: auto-company-site-pages-functions
type: system
sources:
  - path: projects/auto-company-site/functions/listeden-cik.js
    hash: 7da883b7faec5b5065d071608172ca1d8effa6a3e255bc1cd658181000936229
  - path: projects/auto-company-site/functions/randevu.js
    hash: 680f4267bf50111c0d6d05e9068a837e04e46dc3a7cac7d549eb3e7a35c708bb
sources_digest: d765296cba06e0858b94642f9c57598b0a01dbdbf1099116ab94c5ce24458b9c
links: []
generator:
  version: 1
covers:
  - symbol: onRequestGet
    kind: function
    at: 'projects/auto-company-site/functions/listeden-cik.js:L19-L46'
  - symbol: errorPage
    kind: function
    at: 'projects/auto-company-site/functions/listeden-cik.js:L48-L59'
  - symbol: onRequestGet
    kind: function
    at: 'projects/auto-company-site/functions/randevu.js:L17-L34'
  - symbol: page
    kind: function
    at: 'projects/auto-company-site/functions/randevu.js:L36-L47'
---
<!-- context:generated:start -->
## Summary

Cloudflare Pages Functions for the auto-company marketing site: /randevu issues a 302 redirect to the operator's Google Calendar (no booking logic — slot management, timezone, cancellation delegated to Google Calendar; validates RANDEVU_URL starts with https://, 503 with Turkish fallback if unset, never a guessed redirect), and /listeden-cik proxies the email opt-out flow to the Twilio-based comms service (deliberately no local suppression store so upstream remains single source of truth; preserves HMAC signature and email params so existing links keep working; 502 Turkish error page on upstream failure, never false success). Both set no-store and no-referrer headers for privacy and caching safety.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
