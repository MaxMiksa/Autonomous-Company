# scripts/ops/wowcar-revenue-vocabulary-acceptance.py · [[wowcar-revenue-relabel-acceptance]] [[wowcar-revenue-vocabulary]]

Fail-closed acceptance harness that pins the live Wowcar repo as baseline, applies the eight approved revenue-vocabulary and column-width edits to a candidate copy, and verifies the candidate's outputs match the baseline except for the intended relabeling.

- AcceptanceFailure · class · L383-L384 — Exception type raised when an acceptance check fails, distinguishing harness failures from configuration problems.
- ConfigurationFailure · class · L387-L388 — Exception type raised when the environment or baseline does not match the pinned expectations, distinct from acceptance failures.
- sha256_bytes · function · L391-L392 — Computes the hex SHA-256 digest of a byte string for content fingerprinting.
- canonical_digest · function · L395-L397 — Produces a stable canonical digest of an arbitrary value by JSON-serializing it with sorted keys and compact separators.
- require · function · L400-L402 — Raises AcceptanceFailure when a condition is false, enforcing acceptance invariants.
- config_require · function · L405-L407 — Raises ConfigurationFailure when a pinned environment or baseline condition is false.
- find_repo · function · L410-L413 — Locates the repository root from the script's own path and verifies the expected kod directory exists.
- verify_runtime · function · L416-L425 — Verifies the pinned CPython version, dependency versions, and LibreOffice version, returning the detected versions.
- baseline_records · function · L428-L444 — Walks the kod tree and builds a manifest of every member's path, mode, type, size, and hash, rejecting symlinks and other non-file/dir types.
- verify_baseline · function · L447-L450 — Confirms the live tree's manifest exactly matches the pinned baseline list and its canonical root digest.
- tree_manifest · function · L453-L472 — Builds a canonical digest and record list for one or more protected paths, capturing symlink targets and file hashes.
- inventory · function · L475-L488 — Maps every path under a root to its type, mode, and content hash (or symlink target) for comparing two trees.
- apply_candidate_edits · function · L491-L499 — Applies the width and vocabulary replacements to the candidate copy, asserting each preimage occurs the expected number of times.
- check_source_boundary · function · L502-L531 — Compares baseline and candidate inventories to confirm the only source differences are the intended edits, returning the diff.
- run · function · L534-L540 — Executes a subprocess with a timeout and captures its return code, stdout, and stderr.
- require_success · function · L543-L544 — Raises AcceptanceFailure if a run result did not exit successfully, labeling the failure.
- numeric_probe · function · L547-L551 — Runs the model probe in a subprocess and returns the parsed numeric output plus the run result.
- numeric_leaf_count · function · L554-L560 — Counts the number of numeric leaves in a nested probe structure.
- scrub_command · function · L563-L564 — Removes the command from a run result so it is not part of comparison digests.
- build_chain · function · L567-L585 — Creates the baseline and candidate working copies, applies edits to the candidate, and returns both roots plus their manifests.
- scalar · function · L588-L603 — Converts a cell value into a comparable scalar, mapping None and booleans to canonical forms.
- workbook_structure · function · L606-L634 — Extracts a canonical structural description of an xlsx workbook (sheets, dimensions, and cell values) for comparison.
- cached_cells · function · L637-L655 — Reads the cached cell values from an xlsx file and returns them with a count of cached cells.
- normalize_f4_pair · function · L658-L669 — Normalizes a baseline/candidate cell pair so only the intended relabeling differences remain, using a locate helper to find the relevant cells.
- locate · function · L659-L664 — Finds the list of cells in a workbook structure that correspond to the F4 pair being compared.
- compare_workbooks · function · L672-L683 — Compares baseline and candidate workbooks after normalization, returning counts of differing and matching cells.
- normalize_stdout · function · L686-L708 — Normalizes stdout bytes by adjusting the column widths of the known tables so baseline and candidate output align.
- compare_stdout · function · L711-L730 — Compares normalized stdout of baseline and candidate runs, returning the diff result.
- parse_args · function · L733-L738 — Parses command-line arguments for the acceptance harness.
- control_identity · function · L741-L758 — Computes a control identity digest from the repository's baseline manifest for reproducibility checks.
- main · function · L761-L911 — Orchestrates the full acceptance run: verifies runtime and baseline, builds chains, runs scenarios, and compares workbooks and stdout.
