# scripts/ops/idle-skip-note.py · [[consensus-memory-state-files]] [[idle-skip-mechanism]]

Records a model-free idle-skip as one line per UTC day in consensus.md, updated in place and written atomically, so the loop leaves auditable 'checked, nothing moved' evidence without bloating the prompt.

- build_line · function · L26-L34 — Formats the human-readable idle-skip line for consensus.md, embedding the day marker so the line can be found and updated in place on later skips.
- main · function · L37-L89 — Reads consensus.md, finds or creates the day's idle-skip line, increments its count while preserving the day's first start time, and atomically rewrites the file (or exits non-zero leaving it untouched on error).
