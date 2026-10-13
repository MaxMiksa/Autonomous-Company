# scripts/ops/registry-queue-watch.py · [[operator-alerting-watchers]] [[registry-queue-watch]]

Advisory watcher that tells the operator when Registry/EKAP bridge queues have resolvable PENDING requests or when firms are Held on attribution with no bridge request ever queued, throttling notifications via a state file.

- api_key · function · L48-L58 — Resolves the Airtable API key from the environment or the app's runtime.env file so the watcher can authenticate reads.
- fetch · function · L61-L77 — Fetches all records of an Airtable table with optional server-side formula filtering, following pagination offsets until exhausted.
- main · function · L80-L215 — Computes pending bridge requests and unasked attribution-held firms, then decides whether to notify the operator (respecting threshold and repeat-hour throttle) and persists notification state.
