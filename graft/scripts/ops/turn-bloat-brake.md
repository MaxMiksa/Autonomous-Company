# scripts/ops/turn-bloat-brake.py · [[telegram-notification-secrets]] [[turn-bloat-brake]] [[turn-economy-and-bloat-control]]

CLI tool that tracks consecutive BLOATED cycles and escalates to a hard persist-and-end mandate once a streak crosses a threshold, resetting on any non-BLOATED verdict.

- _app · function · L25-L26 — Resolves the app root path, defaulting to the repo root two levels above this file when no explicit path is given.
- _streak_len · function · L29-L34 — Reads the TURN_BLOAT_STREAK env var and returns a valid streak length, defaulting to 3 for missing or invalid values.
- _load · function · L37-L41 — Reads and parses the JSON state file, returning an empty dict on any read or parse failure.
- _save · function · L44-L51 — Atomically writes the streak state to a temp file then replaces the target, silently ignoring any failure.
- main · function · L63-L104 — Parses flags and either emits the hard mandate pre-cycle when a streak is active or records the verdict, incrementing/resetting the streak and alarming exactly on the crossing.
