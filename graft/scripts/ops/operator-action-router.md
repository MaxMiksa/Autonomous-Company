# scripts/ops/operator-action-router.py · [[operator-action-router]] [[operator-notification-escalation]] [[runtime-environment-secrets]]

Consolidated operator digest that reads local company state (LOOP_HOLD, open OPREQs, PENDING directive) and notifies the operator via Telegram only when there are actionable items and either the open set changed or the repeat window elapsed, staying silent and fail-soft otherwise.

- _now · function · L78-L79 — Returns the current UTC time, the single clock used for directive age and repeat-window math.
- read_hold · function · L82-L102 — Reads logs/LOOP_HOLD and extracts a short human reason string (from a `reason` line or the first non-latch/cleared line), returning None if the file is unreadable so the hold item is skipped fail-soft.
- read_opreqs · function · L105-L118 — Parses memories/operator-requests.md and returns the ids of OPREQ blocks whose Status is OPEN, or None if the ledger is unreadable so the item is skipped rather than invented.
- read_directive · function · L121-L134 — Reads memories/human-directive.md and returns (status, age_hours, sha8) where age is derived from file mtime and status defaults to NO-STATUS, or None if the file is unreadable/absent.
- collect_items · function · L137-L174 — Assembles the current operator-actionable item set from the three fail-soft sources, each contributing a stable hash key, priority, and a digest bullet, sorted by priority.
- render · function · L177-L183 — Formats the open-item list into the operator-facing Telegram digest text with a count header and a 'Gerisi normal' footer.
- set_hash · function · L186-L189 — Hashes the sorted stable keys of the open set into a 16-char identity used to detect whether the actionable set changed.
- should_notify · function · L192-L207 — Decides whether to speak: only when the set is non-empty AND either the identity changed or the repeat window elapsed, suppressing on dedup and treating a bad stored timestamp as a reason to notify.
- load_state · function · L210-L214 — Loads the persisted router state JSON, returning an empty dict on any read/parse failure so the watcher stays fail-soft.
- write_state · function · L217-L225 — Atomically persists the router state (hash + last_notified_iso) via a temp file and os.replace, printing a warning to stderr if persistence fails.
- clear_state · function · L228-L232 — Deletes the state file so the next open item alerts immediately, ignoring any removal error.
- notify · function · L235-L251 — Sends the digest via scripts/core/telegram-notify.sh, sourcing TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID from logs/runtime.env into a fresh shell environment, and silently no-ops if the script is missing.
- main · function · L254-L296 — CLI entrypoint that collects items, applies dedup/cadence, renders and sends the digest (or dry-runs), clears state when empty, and never lets a collection bug fail the cycle.
