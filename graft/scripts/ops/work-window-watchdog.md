# scripts/ops/work-window-watchdog.py · [[state-file-throttling-atomicity]] [[work-window-brake]]

The alarm layer that makes a model ignoring the work-window brake visible by printing a Telegram alarm when an open window coincides with empty-cycle admissions for THRESHOLD consecutive cycles.

- _app_dir · function · L45-L48 — Resolves the app directory from the --app argument, defaulting to the repo root two levels above this file.
- _threshold · function · L51-L57 — Reads the WORK_WINDOW_WATCHDOG_THRESHOLD env var, falling back to the default of 2 and rejecting values below 1.
- _read_state · function · L60-L64 — Loads the persisted consecutive/last_cycle JSON state, returning an empty dict on any read or parse failure.
- _write_state · function · L67-L74 — Atomically persists the watchdog state via a temp file and os.replace, swallowing any error so bookkeeping never fails the loop.
- main · function · L77-L125 — Reads the cycle's model output and flags, resets the counter on closed/failed/real-work cycles, and emits a one-time alarm when the empty-cycle threshold is crossed in an open window.
