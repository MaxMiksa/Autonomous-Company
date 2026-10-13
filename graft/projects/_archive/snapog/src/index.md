# projects/_archive/snapog/src/index.ts · [[snapog-worker]]

The main Cloudflare Worker entrypoint that wires Hono routes for OG image generation, key registration, dashboard, health, and a scheduled cost-alert cron.

- sha256 · function · L21-L29 — Hashes raw API keys to SHA-256 hex so only hashes are stored and compared in the DB.
- generateRawKey · function · L31-L35 — Generates a random 32-byte API key prefixed with sk_ for issuance to users.
- htmlResponse · function · L37-L42 — Wraps HTML strings in a Response with the proper content-type header.
- resolveApiKey · function · L45-L56 — Looks up an API key row by its SHA-256 hash, returning null when absent.
- billingMonthISO · function · L61-L64 — Returns the ISO timestamp of the first day of the current month, the shared rollover boundary for usage and cache-key caps.
- maybeResetUsage · function · L67-L83 — Zeroes a key's monthly usage counter when the billing month has rolled over.
- trackCacheKeyAndCheckCap · function · L90-L110 — Records a distinct cache key per key per billing month and reports whether the monthly distinct-key cap is exceeded.
- recordUsage · function · L113-L130 — Increments a key's usage counter and logs a usage event atomically in a batch.
- scheduled · method · L360-L370 — Cron trigger that runs the cost-alert check and logs how many alerts fired.
