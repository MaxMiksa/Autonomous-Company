# scripts/analyst/merge_registry.py · [[registry-merge-tool]]

Deterministic PASS-2 merge that isolates the live decision-state span of the registry and only accepts a model-proposed replacement for that span, enforcing invariants so a model can never silently drop or rewrite protected content.

- identifier_fields · function · L66-L76 — Extracts candidate-ID-bearing fields from table rows and HOLD bullets so ID checks only look where identifiers can actually live, not in prose.
- audit · function · L79-L82 — Appends a timestamped line to the audit log for every merge outcome.
- blocked · function · L85-L88 — Logs a reason, prints BLOCKED, and exits 0 so a failed merge never breaks the caller.
- extract_ids · function · L91-L105 — Collects candidate IDs by matching the ID token anchored to the start of each identifier field, so measurements buried in sentences are not mistaken for candidates.
- extract_axes · function · L108-L120 — Finds the longest '×'-containing cell in each pipe-table row to detect duplicate axes robustly across the three column layouts.
- table_rows · function · L123-L131 — Parses every pipe-table data row into stripped cell lists, skipping separator/decoration lines.
- row_identity · function · L134-L151 — Determines whether a table row is a candidate row and returns its (id, axis, verdict), handling the rank-column layout where the ID sits in cell 1.
- sections · function · L154-L163 — Splits text into '## ' heading sections, mapping each heading to its accumulated body.
- active_candidates · function · L166-L186 — Returns the identity of candidates whose axis/verdict the merge may not rewrite: everything in ## Selected plus rank 1 of ## Pending shortlist.
- normalize_axis · function · L189-L190 — Normalizes an axis string by collapsing whitespace and lowercasing for comparison.
- resolve_span · function · L193-L232 — Dereferences the @/path shorthand pass-2 sometimes emits for the live span, reading the referenced file's content while still running all invariants on it.
- _rewind_over_separators · function · L235-L246 — Walks a heading start back over preceding blank and '---' lines so those decorations stay in the untouched suffix rather than becoming model-reproduced junk.
- split_registry · function · L249-L272 — Splits the registry into (before, live, after) at the two section headings, returning exact slices so the append-only historical journal is never modified.
- main · function · L275-L428 — Orchestrates the merge: extracts the live span, validates the model payload against ID/axis/identity invariants, and writes the reassembled registry only after read-back verification.
