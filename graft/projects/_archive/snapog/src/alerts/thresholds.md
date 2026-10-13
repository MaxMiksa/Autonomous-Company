# projects/_archive/snapog/src/alerts/thresholds.ts

Centralizes all CFO-revisable alert thresholds for cost-model kill-switch metrics so the cron check logic stays decoupled from the numbers.

- ThresholdKey · type · L27-L27 — Derives a union type of the threshold metric names so check logic can reference them type-safely.
