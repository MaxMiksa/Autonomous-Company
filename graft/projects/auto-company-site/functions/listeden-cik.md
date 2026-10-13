# projects/auto-company-site/functions/listeden-cik.js · [[auto-company-site-functions]]

Presentation-layer Cloudflare Worker that proxies the branded opt-out URL to the comms service's /unsubscribe endpoint, preserving the existing signature scheme so in-the-wild links keep working.

- onRequestGet · function · L19-L46 — Forwards the incoming opt-out request to the upstream unsubscribe endpoint, and on any fetch failure returns a plain-language Turkish error page rather than ever pretending an opt-out succeeded.
- errorPage · function · L48-L59 — Builds a self-contained Turkish HTML error page with no-store caching so users get a clear path when the opt-out cannot be processed.
