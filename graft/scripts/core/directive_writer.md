# scripts/core/directive_writer.py · [[directive-governance-staleness]] [[directive-writer]] [[human-directive-write-path]] [[runtime-environment-secrets]]

The single locked, fail-closed pipeline for writing memories/human-directive.md, enforcing that in-flight PENDING work is never clobbered and that an accepted body is immutable except via compare-and-swap status transitions.

- undefined_section_refs · function · L104-L113 — Rejects directive bodies that reference a §N section with no matching ## §N header, preventing unsatisfiable Completion clauses that freeze directives in PENDING.
- now · function · L116-L117 — Returns the current UTC time as an ISO-8601 string for timestamps in the file and audit log.
- sha · function · L120-L121 — Computes the SHA-256 hex digest of a string, used to fingerprint directive bodies for compare-and-swap and verification.
- read_live · function · L124-L130 — Reads the current directive file and returns its text, SHA-256, and Status value, with empty strings when absent.
- body_of · function · L133-L140 — Normalizes the Status value to a placeholder so a caller cannot smuggle a body edit past the immutability comparison by deleting the heading.
- audit · function · L143-L149 — Appends a timestamped action line to the audit ledger and normalizes its ownership.
- _telegram_env · function · L152-L175 — Resolves Telegram credentials from the process env, falling back to runtime.env so alerting works regardless of which door invoked the writer.
- notify · function · L178-L188 — Sends a Telegram alert for refusals, silently swallowing any failure so a notification can never fail a write.
- _why_pending · function · L191-L219 — Builds a quoted explanation of why the live directive is still PENDING, from its own Completion clause and age, for the refusal notification.
- backup · function · L222-L236 — Persists the about-to-be-destroyed content before a write, blocking the write if the backup cannot be verified.
- normalize_ownership · function · L239-L285 — Chowns written files to the memories directory owner and opens mode to 0644 so the loop/dashboard user can read them regardless of invoker identity.
- atomic_write · function · L288-L300 — Writes the directive to a temp file, fsyncs, and atomically renames it into place, cleaning up on failure.
- verify_written · function · L303-L307 — Reads the file back and raises if it differs from what was written, returning the SHA-256 of the on-disk content.
- Refused · class · L310-L311 — Marker exception indicating a gate refused the operation, which is a normal outcome rather than an error.
- live_body · function · L316-L319 — Returns everything after the '## Directive' marker line as the directive body, or empty string when the marker is absent.
- split_body · function · L322-L345 — Splits the directive body into a protected first chunk (ANA DİREKTİF + preamble) and a list of '## ' sections so append/archive can operate on individual sections without ever splitting the main directive.
- section_sizes · function · L348-L352 — Computes the UTF-8 byte size of the first chunk and each '## ' section for reporting the largest sections in size warnings.
- size_brake · function · L355-L371 — Warns on stderr+Telegram when the body exceeds WARN_BYTES and refuses append above MAX_BYTES unless --force-size, listing the largest sections to steer toward archiving.
- _pending_gate · function · L374-L390 — Fail-closed gate that refuses any write to a PENDING live directive unless --allow-pending, auditing and notifying the operator with the directive's own Completion clause explaining why it is still pending.
- _refuse_section_refs · function · L393-L401 — Rejects a body that references a '§N' section number with no matching '## §N' header, enforcing OPREQ-GOV-DIRECTIVE-BODY-001 before anything is written.
- with_lock · function · L404-L413 — Decorator that serializes a command under an exclusive flock on the directive lock file.
- wrapper · function · L405-L412 — Acquires the exclusive lock, runs the wrapped command, and always releases the lock.
- cmd_write · function · L426-L480 — Replaces the entire directive body through the full locked pipeline, gated on in-flight PENDING and undefined section references, with backup, atomic rename, read-back verify, audit, and notify.
- cmd_append · function · L484-L512 — Adds one '## ' section to the live body through the same locked pipeline, setting Status PENDING and enforcing the size brake so the loop's directive_unaudited check stays green.
- cmd_archive · function · L516-L580 — Moves closed sections verbatim into the archive file, replacing them with a short summary while never touching the ANA DİREKTİF first chunk and requiring Resolves/Decision lines to be preserved in the summary.
- cmd_status · function · L584-L618 — Compare-and-swaps the Status value, refusing if the live status or body hash differs from what the caller expected.
- cmd_restore · function · L622-L658 — Restores a snapshot only if the live file is unchanged since it was taken, otherwise saving the candidate to recovery and leaving the live file alone.
- cmd_show · function · L661-L672 — Prints the directive body, optionally with per-section heading and byte sizes via --sections.
- main · function · L675-L733 — Argparse dispatcher that routes subcommands (write/append/archive/status/restore/show) to their handlers and maps gate refusals to exit code 2 and I/O/verification failures to exit code 3.
- _refuse_forbidden · function · L714-L720 — Returns a handler that refuses a forbidden subcommand with exit code 2.
- fn · function · L715-L719 — Prints a refusal message and returns exit code 2 for a forbidden subcommand.
