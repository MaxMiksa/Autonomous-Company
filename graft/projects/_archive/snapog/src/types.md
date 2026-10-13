# projects/_archive/snapog/src/types.ts · [[snapog-worker]]

Shared type definitions and constants for the SnapOG worker, including tier limits, a monthly R2 cache-key cap, and interfaces for API keys, OG image params, and the Worker environment bindings.

- Tier · type · L3-L3 — Defines the three billing subscription levels that gate usage limits.
- ApiKey · interface · L16-L27 — Represents a customer API key record with its tier, monthly quota, and usage accounting fields.
- OGParams · interface · L29-L37 — Describes the query parameters accepted when rendering an Open Graph image.
- Env · interface · L39-L49 — Declares the Worker bindings and optional cost-alerting cron configuration.
