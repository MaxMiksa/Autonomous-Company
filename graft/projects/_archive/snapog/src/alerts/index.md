# projects/_archive/snapog/src/alerts/index.ts · [[snapog-cost-alerts]]

Entry point for the SnapOG cost-alerting cron job, orchestrating checks and webhook delivery.

- runCostAlertCheck · function · L8-L14 — Runs all cost checks and posts alerts to the webhook only when at least one alert is found, returning the alert count.
