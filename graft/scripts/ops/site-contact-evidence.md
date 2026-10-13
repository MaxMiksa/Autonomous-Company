# scripts/ops/site-contact-evidence.py · [[outreach-eligibility-gate]]

Finds a firm's published contact email across escalating sources, ensuring an unrendered fetch is reported as inconclusive rather than negative.

- fetch · function · L56-L64 — Runs curl with a browser UA and returns the HTTP status code and body for a URL.
- emails · function · L67-L68 — Extracts email addresses from text, filtering out known noise/placeholder addresses.
- looks_unrendered · function · L71-L81 — Detects whether a response is a JavaScript shell with no visible content rather than a real page.
- render_dom · function · L84-L110 — Renders a page in a real browser via BrowserOS MCP and returns the built DOM as a third evidence source.
- examine · function · L113-L172 — Gathers email evidence from HTML, JS bundles, policy pages and rendered DOM, then classifies the verdict with the rendered-only-negative rule.
- main · function · L175-L196 — Parses CLI args and prints per-domain verdicts and email provenance in text or JSON.
