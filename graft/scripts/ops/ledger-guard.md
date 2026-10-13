# scripts/ops/ledger-guard.py · [[consensus-memory-state-files]] [[ledger-guard]] [[ledger-integrity-guard]]

Per-cycle integrity guard that rolls back backups of the Gate-0 conflict ledger and consensus.md and detects silent content loss by comparing section/row/byte metrics against the previous cycle, printing a violation when a drop lacks an incident marker.

- _env_int · function · L43-L48 — Reads an integer environment variable, falling back to the default when unset, non-numeric, or non-positive.
- _env_float · function · L51-L55 — Reads a float environment variable, falling back to the default on unset or non-numeric values.
- _app · function · L58-L59 — Resolves the app root path, defaulting to the repo root two levels above this script when no argument is given.
- _find_ledger · function · L62-L69 — Locates the live Gate-0 conflict ledger file, preferring the gate0-named match and returning the most recently modified candidate.
- _metrics · function · L72-L84 — Computes the integrity metrics (section count, OPEX row refs, byte size, sha16, incident marker) for a guarded file, or None if unreadable.
- _backup · function · L87-L101 — Copies the guarded file into the rolling backup dir keyed by cycle and prunes to the newest N backups per basename, swallowing all errors.
- _load_state · function · L104-L108 — Loads the previous cycle's guard state JSON, returning an empty dict on any read/parse failure.
- _save_state · function · L111-L118 — Atomically writes the guard state JSON via a temp file and os.replace, swallowing any write error.
- _rebase_after_prune · function · L125-L142 — Rebases the consensus baseline to the post-prune metrics recorded by consensus-prune.py when the held baseline exactly matches the pre-prune file, so a real deletion in the same cycle still alarms without being blinded by a permanent archive note.
- _check · function · L145-L170 — Compares current vs previous metrics and returns a violation string when content dropped beyond thresholds without an incident marker, or None otherwise.
- main · function · L173-L240 — Orchestrates the guard run: locates guarded files, backs them up, compares each against prior metrics to collect violations, keeps last-known metrics for missing files so alarms persist, and writes the violation report while always exiting 0.
