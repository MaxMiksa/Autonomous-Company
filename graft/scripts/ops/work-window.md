# scripts/ops/work-window.py · [[fail-closed-harness-brakes]] [[state-snapshot-delta-probing]]

A mechanical brake that opens a K-cycle work window whenever a tracked surface changes, forcing the harness to advance follow-on work instead of emitting a valid empty-cycle confirmation, failing closed on any unreadable state.

- _app_dir · function · L52-L56 — Resolves the app directory from the --app argument, defaulting to the repo root derived from this script's location.
- _env_int · function · L59-L66 — Reads an integer from an environment variable, returning the provided default when unset or non-numeric.
- _parse_delta · function · L69-L78 — Classifies a snapshot block's DELTA line into none/first/changed/unknown and extracts the changed fields.
- _read_state · function · L81-L88 — Loads the work-window JSON state file, distinguishing a missing file (not corrupt) from an unreadable/corrupt one.
- _write_state · function · L91-L95 — Atomically persists the work-window state via a temp file plus rename.
- _line · function · L98-L108 — Builds the human-readable WORK-WINDOW OPEN injection line telling the model to advance one Next Action item or enumerate blocked-by-authority items.
- main · function · L111-L181 — Reads the DELTA snapshot and stored window state to decide whether the brake is engaged (exit 10, inject an order) or idle is allowed (exit 0), applying the directive-DONE close rule and TTL expiry.
