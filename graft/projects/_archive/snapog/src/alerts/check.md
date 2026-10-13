# projects/_archive/snapog/src/alerts/check.ts · [[snapog-cost-alerting]]

Cost-alerting check module that independently evaluates D1 write volume, cache hit rate, signups, active users, and R2 storage against thresholds to surface cost risks.

- AlertSeverity · type · L10-L10 — Union type defining the three severity levels an alert can carry.
- Alert · interface · L12-L18 — Data holder describing a fired alert's name, severity, current/threshold values, and human-readable message.
- checkD1WritesPerDay · function · L27-L44 — Estimates D1 write volume over the last 24h from usage_events and alerts when it exceeds the daily threshold, escalating severity past 1.5x.
- checkCacheHitRate · function · L46-L71 — Computes the 14-day cache hit rate and alerts when it falls below target, requiring a minimum sample to avoid noise.
- checkNewSignups · function · L73-L89 — Counts new signups in the last 30 days and warns when growth implies unsustainable R2 storage.
- checkActiveUsers · function · L91-L105 — Counts active free users this billing month and warns when the trajectory suggests reaching the paid tier.
- checkR2Storage · function · L107-L126 — Fetches live R2 bucket storage via the analytics API and alerts when usage approaches the free-tier cap, escalating past 1.5x.
- runAllChecks · function · L131-L150 — Runs every check concurrently, isolating failures so one broken check never suppresses the rest or fires false positives.
