# scripts/core/directive_writer.py · [[escalation-directive-system]] [[human-directive-lifecycle]]

Single locked pipeline for writing the human directive file, enforcing in-flight protection and body immutability via atomic writes, backups, and audit.

- undefined_section_refs · function · L74-L83 — Rejects directive bodies that reference a §N section with no matching ## §N header, preventing unsatisfiable Completion clauses that freeze directives in PENDING.
- now · function · L86-L87 — Returns the current UTC time as an ISO-8601 string for timestamps in the file and audit log.
- sha · function · L90-L91 — Computes the SHA-256 hex digest of a string, used to fingerprint directive bodies for compare-and-swap and verification.
- read_live · function · L94-L100 — Reads the current directive file and returns its text, SHA-256, and Status value, with empty strings when absent.
- body_of · function · L103-L110 — Normalizes the Status value to a placeholder so a caller cannot smuggle a body edit past the immutability comparison by deleting the heading.
- audit · function · L113-L119 — Appends a timestamped action line to the audit ledger and normalizes its ownership.
- _telegram_env · function · L122-L145 — Resolves Telegram credentials from the process env, falling back to runtime.env so alerting works regardless of which door invoked the writer.
- notify · function · L148-L158 — Sends a Telegram alert for refusals, silently swallowing any failure so a notification can never fail a write.
- _why_pending · function · L161-L189 — Builds a quoted explanation of why the live directive is still PENDING, from its own Completion clause and age, for the refusal notification.
- backup · function · L192-L206 — Persists the about-to-be-destroyed content before a write, blocking the write if the backup cannot be verified.
- normalize_ownership · function · L209-L255 — Chowns written files to the memories directory owner and opens mode to 0644 so the loop/dashboard user can read them regardless of invoker identity.
- atomic_write · function · L258-L270 — Writes the directive to a temp file, fsyncs, and atomically renames it into place, cleaning up on failure.
- verify_written · function · L273-L277 — Reads the file back and raises if it differs from what was written, returning the SHA-256 of the on-disk content.
- Refused · class · L280-L281 — Marker exception indicating a gate refused the operation, which is a normal outcome rather than an error.
- with_lock · function · L284-L293 — Decorator that serializes a command under an exclusive flock on the directive lock file.
- wrapper · function · L285-L292 — Acquires the exclusive lock, runs the wrapped command, and always releases the lock.
- cmd_write · function · L306-L359 — Writes a new directive body as PENDING, refusing empty bodies, undefined section refs, and clobbering in-flight PENDING work unless --allow-pending.
- cmd_status · function · L363-L397 — Compare-and-swaps the Status value, refusing if the live status or body hash differs from what the caller expected.
- cmd_restore · function · L401-L437 — Restores a snapshot only if the live file is unchanged since it was taken, otherwise saving the candidate to recovery and leaving the live file alone.
- cmd_show · function · L440-L445 — Prints the current directive file contents.
- main · function · L448-L495 — Parses subcommands and dispatches to the write/status/restore/show handlers, mapping refusals to exit code 2.
- _refuse_forbidden · function · L476-L482 — Returns a handler that refuses a forbidden subcommand with exit code 2.
- fn · function · L477-L481 — Prints a refusal message and returns exit code 2 for a forbidden subcommand.
