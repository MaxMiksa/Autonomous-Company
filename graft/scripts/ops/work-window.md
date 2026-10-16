# scripts/ops/work-window.py · [[work-window-brake]] [[work-window-watchdog-brakes]]

A mechanical brake that opens a K-cycle work window whenever a tracked surface changes, forcing the harness to advance queued work instead of emitting a valid empty-cycle confirmation, and failing closed on any unreadable state.

- _app_dir · function · L59-L63 — Resolves the app directory from the --app argument, defaulting to the repo root derived from this script's location.
- _env_int · function · L66-L73 — Reads an integer from an environment variable, returning the provided default when unset or non-numeric.
- _parse_delta · function · L76-L85 — Classifies a snapshot block's DELTA line into none/first/changed/unknown and extracts the changed fields.
- _read_state · function · L88-L95 — Loads the work-window JSON state file, distinguishing a missing file (not corrupt) from an unreadable/corrupt one.
- _write_state · function · L98-L102 — Atomically persists the work-window state via a temp file plus rename.
- _line · function · L105-L115 — Builds the human-readable WORK-WINDOW OPEN injection line telling the model to advance one Next Action item or enumerate blocked-by-authority items.
- main · function · L118-L191 — Reads the snapshot DELTA and stored window state to decide whether the brake is engaged (exit 10, inject a WORK-WINDOW OPEN line) or idle is allowed (exit 0), applying directive-DONE and auditor-only closure rules.
