---
name: Auto Company Site Pages
slug: auto-company-site-pages
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

Cloudflare Pages Functions for the auto-company marketing site: /randevu issues a 302 redirect to the operator's Google Calendar appointment page (no booking logic—slot management, timezone, cancellation delegated to Google Calendar), and /listeden-cik proxies the email opt-out flow to the Twilio-based comms service, preserving the original HMAC signature and email params so existing links keep working. Both deliberately avoid local state (no suppression store, no booking logic) keeping upstream services as single source of truth, return Turkish-language fallback pages on failure (never a false success), and set no-store/no-referrer headers.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
