# scripts/ops/bloat-trend.py · [[turn-economy-trend-watch]]

Tracks whether per-cycle turn-economy metrics are improving across a rolling window, and alerts only on a genuine regression or on the two-consecutive-window target being met, so the watcher can be retired.

- ingest · function · L54-L97 — Folds new audit lines from the live log into the durable history, idempotently keyed by session id.
- is_bloated · function · L109-L110 — Classifies a cycle as bloated when any of its turns, duration, or cost exceeds the current thresholds.
- summarise · function · L113-L126 — Computes window statistics (p50/p90 turns, durations, cost, bloated share) from raw rows.
- pct · function · L117-L118 — Returns the value at a given percentile of a sorted list.
- notify · function · L129-L142 — Sends a message through the telegram-notify script, loading bot credentials from runtime.env.
- fmt · function · L145-L155 — Formats a window summary line with deltas against the previous window.
- d · function · L146-L151 — Formats a single metric with its delta arrow against the previous window.
- main · function · L158-L237 — Orchestrates the trend check: computes current/previous windows, decides target-met and regression events, and notifies once each.
- hits_target · function · L185-L187 — Tests whether a window meets the bloated-rate and p90-turns optimisation targets.
