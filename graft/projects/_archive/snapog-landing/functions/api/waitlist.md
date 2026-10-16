# projects/_archive/snapog-landing/functions/api/waitlist.ts

Cloudflare Pages function that persists waitlist signups to KV with deduplication and validation.

- Env · interface · L12-L14 — Declares the optional KV namespace binding used to store waitlist entries.
- Body · interface · L16-L20 — Typed shape of the incoming JSON request body for a waitlist signup.
- onRequestPost · function · L24-L62 — Handles POST /api/waitlist by validating the email, deduplicating against KV, and storing the signup record.
- json · function · L64-L72 — Builds a JSON HTTP response with no-store caching for API replies.
