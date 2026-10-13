# scripts/ops/rfq-reply-watch.py · [[operator-alerting-watchers]] [[outreach-and-reply-monitoring]] [[telegram-notification-secrets]]

Advisory RFQ reply watcher that notices new vendor replies and long silences on the OPEX RFQ table and notifies the operator without ever writing to Airtable.

- api_key · function · L36-L46 — Resolves the Airtable API key from the environment, falling back to the runtime.env secret file.
- fetch · function · L49-L64 — Paged Airtable query that returns all records matching an optional filter formula, following offset pagination.
- notify · function · L67-L80 — Sends a Telegram message via the core notify script, injecting bot token/chat id from the runtime env.
- first_ts · function · L83-L88 — Extracts the newest entry's timestamp from the first line of the Reply log, which the worker prepends.
- hours_since · function · L91-L106 — Parses a timestamp in any of several UTC formats and returns hours elapsed since it, or None if unparseable.
- main · function · L109-L134 — Entry point that parses args, loads rows from Airtable (or a fixture) and delegates to classify.
- classify · function · L137-L195 — Classifies each sent RFQ row as a new reply or newly silent, builds the operator notice, and persists per-row state so each outcome is warned once.
