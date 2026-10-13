# scripts/ops/work-window.py · [[cycle-escalation-brakes]] [[work-window-brake]]

A fail-closed brake that opens a K-cycle work window whenever a tracked surface changes, forcing the harness to advance one queued item instead of emitting a valid empty-cycle confirmation.

- _app_dir · function · L44-L48 — Resolves the app directory from the --app argument, defaulting to the repo root derived from this script's location.
- _env_int · function · L51-L58 — Reads an integer from an environment variable, returning the provided default when unset or non-numeric.
- _parse_delta · function · L61-L70 — Classifies a snapshot block's DELTA line into none/first/changed/unknown and extracts the changed fields.
- _read_state · function · L73-L80 — Loads the work-window JSON state file, distinguishing a missing file (not corrupt) from an unreadable/corrupt one.
- _write_state · function · L83-L87 — Atomically persists the work-window state via a temp file plus rename.
- _line · function · L90-L100 — Builds the human-readable WORK-WINDOW OPEN injection line telling the model to advance one Next Action item or enumerate blocked-by-authority items.
- main · function · L103-L160 — Orchestrates the brake: kill switch, TTL resolution, fail-closed handling of corrupt/unreadable snapshots, reopening the window on a changed DELTA, and keeping it open while a stored window is within TTL.
