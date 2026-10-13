# projects/headinspect/src/index.ts · [[headinspect-worker]]

Cloudflare Worker entrypoint that routes requests to health, badge, and inspect endpoints, validates URLs against an SSRF blocklist, follows redirects with a cap, and returns JSON/HTML/SVG responses.

- fetch · method · L24-L83 — Routes incoming requests to health, inspect, badge, and root endpoints, applying CORS and JSON/HTML content negotiation.
- TargetOk · type · L88-L88 — Type tag for a successfully validated target URL.
- TargetErr · type · L89-L89 — Type tag for a failed target URL validation carrying an error message.
- extractTarget · function · L91-L104 — Pulls the target URL from query params or a POST JSON body, falling back to validation.
- validateUrl · function · L108-L119 — Parses a raw URL and enforces https-only plus SSRF host blocking before returning a usable target.
- isBlockedHost · function · L121-L147 — Blocks SSRF-prone hosts: localhost, cloud metadata, and private/reserved IP literals.
- InspectOk · type · L151-L151 — Type tag for a successful inspection carrying the full report.
- InspectErr · type · L152-L152 — Type tag for a failed inspection carrying an error message and optional status.
- inspect · function · L154-L229 — Follows redirects (up to a cap) with manual fetch, drains bodies, and builds a graded header report.
- consume · function · L232-L246 — Drains up to a byte cap from a response body so the fetch can complete and the socket be released.
- json · function · L250-L259 — Builds a JSON response with CORS headers and no-store caching.
- html · function · L261-L271 — Builds an HTML response with security headers and no-store caching.
- svg · function · L275-L284 — Builds an always-200 edge-cached SVG badge response for README embeds.
