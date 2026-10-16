# scripts/ops/consensus-prune.py · [[consensus-ledger-pruning]] [[consensus-registry-maintenance]]

Harness mechanism that mechanically archives stale per-cycle narrative from consensus.md into docs/operations when the file exceeds a size threshold, with per-section byte caps, data-safety rebuild/sha verification, and env-tunable kill switches.

- _load_runtime_env · function · L123-L134 — Loads operator live-override CONSENSUS_PRUNE_* KEY=VALUE lines from logs/runtime.env so caps/switches can be tuned without redeploy.
- _env_int · function · L137-L142 — Reads an integer env/runtime value, falling back to the default when unset, non-numeric, or non-positive.
- _env_flag · function · L145-L146 — Reads a string env/runtime value with a default, returning the trimmed value.
- _app · function · L149-L150 — Resolves the app root path from an argument or defaults to the repo root two levels above this file.
- _sha16 · function · L153-L154 — Returns the first 16 hex chars of the SHA-256 digest of bytes, used for short content fingerprints.
- _load_state · function · L157-L161 — Loads the prune state JSON file, returning an empty dict on any read/parse failure so a corrupt state never blocks pruning.
- _save_state · function · L164-L171 — Atomically writes the prune state JSON via a temp file and os.replace, silently ignoring any failure.
- Skip · class · L174-L175 — Exception type signalling that pruning must be skipped for this cycle (unknown shape, non-monotonic numbers, etc.).
- Section · class · L179-L194 — Data holder describing one top-level `## ` section with its header, line range, byte size, canonical/primary flags, and parsed header number.
- __init__ · method · L182-L190 — Initializes a Section, computing canonical membership, extracting the first number from the header, and defaulting primary to False.
- kind · method · L193-L194 — Returns the header with its number replaced by 'N' to classify section kinds.
- Removal · class · L197-L206 — Data holder for a contiguous line range [a,b) removed from the file, tagged with pass, section, cycle, and whether it should be archived.
- __init__ · method · L201-L206 — Stores the removal's line range, pass name, section header, cycle number, and archive flag.
- _split_sections · function · L209-L217 — Splits the file's lines into preamble plus Section objects at each top-level `## ` header, computing each section's byte size.
- _mark_primary · function · L220-L241 — Finds the byte-largest run of consecutive canonical, pairwise-distinct sections and marks them as the primary block to protect.
- flush · function · L226-L229 — Compares the current run's total bytes against the best run and keeps the larger one.
- _tail_pass · function · L245-L249 — Archives every non-primary section except the keep_tail largest-numbered ones, which stay in place.
- _entries_wwd · function · L252-L284 — Parses What We Did bullets (`- **Cycle N`) plus continuation lines into entries, drops old archive notes, and raises Skip on unrecognized top-level bullets.
- _entries_para · function · L287-L322 — Finds removable paragraph entries in Next Action / Current Phase / Company State sections, recognizing `**Cycle N` paragraphs and the v2.1 `(Prior...)` lead-in shapes, returning (cycle, start, end) blocks including trailing blank lines.
- _entries_bullets · function · L325-L349 — Splits Execution Controls into top-level `- ` bullet blocks with their continuation lines and marks only those whose first line carries a `Cycle N` as archivable entries, pinning the rest.
- _select · function · L352-L374 — Chooses which entries to archive by removing from the smallest cycle number up until the section is under its byte cap (and keep bound), always leaving at least the floor count of entries.
- _line_offsets · function · L378-L382 — Computes the byte offset of each line's start in the file for later block extraction.
- _strip_and_blocks · function · L385-L400 — Removes the given line ranges from the data, returning stripped bytes plus (offset, bytes) blocks, and raises Skip on overlapping removals.
- _rebuild · function · L403-L412 — Inverse of _strip_and_blocks: re-inserts every removed block at its original byte offset to reconstruct the original file.
- main · function · L416-L720 — Orchestrates the whole prune run: loads env/state, splits sections, runs each pass, rebuild-verifies removals byte-exactly, appends and sha-verifies the archive before atomically rewriting consensus.md, and emits visibility logs.
- finish_skip · function · L447-L463 — Records a skip (or resets the streak) in state, prints a skip-streak alarm when over threshold, and never touches guard-facing keys.
- after_bytes · function · L531-L532 — Computes a section's byte size after its removals are applied.
- record_history · function · L549-L568 — Records the current run's pre/post sha and metrics into the guard state so the harness can detect skips and bloat across runs.
- emit_warns · function · L570-L572 — Prints accumulated bloat and non-canonical-header warnings to stdout.
