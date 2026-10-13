# projects/_archive/snapog/src/alerts/webhook.ts · [[snapog-cost-alerts]]

Module that posts fired alerts to a configured webhook URL as generic JSON, compatible with Slack/Discord incoming webhooks.

- AlertPayload · interface · L8-L13 — Shape of the JSON payload sent to the webhook, tagging the project, environment, timestamp, and the fired alerts.
- postAlerts · function · L15-L42 — Posts fired alerts to the webhook, falling back to log-only mode when the URL is unset and swallowing HTTP/network failures.
