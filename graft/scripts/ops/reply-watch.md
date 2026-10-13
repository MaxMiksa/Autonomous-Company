# scripts/ops/reply-watch.py · [[operator-alerting-watchers]] [[outreach-outcome-watchers]]

Advisory watcher that detects the outcome of outreach sends (reply, delivery failure, or silence) and notifies the operator once per row per outcome class, persisting state in a JSON file.

- api_key · function · L46-L56 — Resolves the Airtable API key from the environment or the app's runtime.env file, falling back to empty string.
- fetch · function · L59-L74 — Pulls all Airtable records for a table, following pagination offsets and applying an optional filter formula.
- notify · function · L77-L91 — Sends a text message to the operator via the telegram-notify.sh script, sourcing bot credentials from runtime.env.
- first_ts · function · L94-L99 — Extracts the timestamp of the newest log entry, which the worker prepends as the first line.
- hours_since · function · L102-L112 — Computes the age in hours of a timestamp relative to now, tolerating two timestamp formats.
- main · function · L115-L142 — Parses CLI args, loads rows from Airtable (or a fixture) filtered to real sent firms, and delegates to classify.
- classify · function · L145-L223 — Classifies each sent row into reply, unresolved delivery failure, or silence outcomes, alerts once per class, and persists seen-state.
