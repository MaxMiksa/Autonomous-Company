# scripts/compact-report.py · [[compact-ritual-tooling]]

PreCompact hook that prints a single measured operational digest (repo sync, prod drift, loop status, discretionary budget) without ever blocking the compact ritual.

- sh · function · L30-L35 — Runs a subprocess with a timeout and returns its trimmed stdout, returning an empty string on any failure so callers fail open.
- sh_input · function · L38-L43 — Runs a subprocess with stdin text and returns stripped stdout, returning empty string on any failure (fail-open).
- repo_root · function · L46-L48 — Resolves the repository root as the parent of the script's own directory.
- line_repo · function · L51-L59 — Appends a repo line showing the latest commit and whether any commits are unpushed to origin/main, flagging unpushed work with a warning.
- block_prod · function · L62-L71 — Delegates prod drift/hold/cockpit/directive/opreq measurement to the single source of truth .claude/brief-extra.sh (DRY), appending its output if executable.
- block_loop · function · L74-L145 — Fetches loop cockpit state, last telemetry/cycle line, process liveness, and empty-cycle streak via one ssh round-trip to show whether the loop is alive and productive.
- grab · function · L101-L103 — Extracts a single key=value field from the cockpit State File raw text, returning '?' when absent.
- block_discretionary · function · L148-L199 — Reads today's discretionary spend from the live ndjson and compares it against the running loop's effective cap and the runtime.env cap to report budget status and pending-restart drift.
- g · function · L186-L188 — Extracts a numeric value for a given key from the ssh output, returning None when absent.
- main · function · L202-L212 — Assembles the digest header and all measurement blocks into a printed report, always returning success.
