---
name: SnapOG Landing & Dashboard Pages
slug: snapog-landing-dashboard-pages
type: file
sources:
  - path: projects/_archive/snapog/src/dashboard/pages.ts
    hash: 6a33d1b6152ee8ea3ee6f5617105ce757c915627156072dd9cb1f3b78e32b4af
sources_digest: aa49b78a6522f0383edeedf2bbb936457599ccfbd81b5ce65f2e99c6e243ad03
links:
  - to: snapog-worker
    relation: part_of
    description: Renders the landing and dashboard HTML served by the worker.
generator:
  version: 1
covers:
  - symbol: layout
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L340-L355'
  - symbol: nav
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L357-L367'
  - symbol: footer
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L369-L376'
  - symbol: landingPage
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L378-L588'
  - symbol: registerPage
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L590-L628'
  - symbol: keyCreatedPage
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L630-L700'
  - symbol: dashboardPage
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L702-L789'
  - symbol: errorPage
    kind: function
    at: 'projects/_archive/snapog/src/dashboard/pages.ts:L791-L805'
---
<!-- context:generated:start -->
## Summary

Server-side HTML template module for SnapOG's public landing page and dashboard. landingPage(host) renders full marketing page (hero, API reference, features, pricing) with 'Carbon Terminal' aesthetic (dark surfaces, amber accent, JetBrains Mono/DM Sans, dot-grid background). Template literals only, no client-side framework. Embeds live OG image preview hitting actual /og endpoint; hardcoded pricing tiers (Free/Pro/Business). host argument threaded into code examples and meta tags to build absolute URLs. Lives under _archive suggesting superseded.

## Related

- part of [[snapog-worker]] — Renders the landing and dashboard HTML served by the worker.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
