# dashboard/sentry_client.py · [[sentry-client]]

Stdlib-only best-effort Sentry error reporter for the cockpit dashboard that POSTs exceptions to Sentry's legacy Store API without ever raising into the caller.

- _parse_dsn · function · L33-L43 — Parses a Sentry DSN into the store URL and public key, returning None when the DSN is missing or malformed.
- capture_exception · function · L49-L102 — Builds a Sentry event from the current or given exception and POSTs it to the store endpoint, swallowing all failures so monitoring never crashes the caller.
