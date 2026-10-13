# scripts/ops/registry-archive.py · [[consensus-memory-state-files]] [[consensus-pruning-archival]] [[registry-operations]]

Deterministic fail-closed archival tool that moves old maintenance notes and frozen discovery sections out of candidate-registry.md into monthly archive files, preserving the protected live region byte-identical.

- die · function · L55-L57 — Aborts the run with a BLOCKED message and exit code 2, guaranteeing nothing is written on any invariant failure.
- sha · function · L60-L61 — Computes the sha256 hex digest used to verify reconstruction integrity in memory.
- heading_line_starts · function · L64-L65 — Returns byte offsets of every '## ' heading, used to delimit sections and the protected region.
- protected_span · function · L68-L80 — Locates the byte span from '## Selected' through the end of the '## Exhausted patterns / lessons' section that must never be altered, failing if anchors are not unique or ordered.
- plan_note_chunks · function · L83-L105 — Finds top-region bold maintenance-note paragraphs with a parseable date older than the cutoff, returning their byte spans for archival.
- plan_section_chunks · function · L108-L140 — Finds frozen 'PART A'/'Cycle' sections after the protected region whose newest embedded date is older than the cutoff, optionally archiving dateless sections into a stated month.
- interleave · function · L143-L149 — Recombines remaining pieces with archived chunks in order to reconstruct the original for sha verification.
- main · function · L152-L340 — Orchestrates the whole archival run: plans chunks, verifies reconstruction and protected-region integrity in memory, then writes archive files and the live file atomically with CAS.
- month_of · function · L250-L251 — Maps a chunk index to its YYYY-MM archive bucket by the chunk's content date.
