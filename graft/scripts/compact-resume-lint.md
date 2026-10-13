# scripts/compact-resume-lint.py · [[compact-ritual-tooling]]

Pre-ritual lint that fails the resume step if it carries stale measurement numbers (cost/queue/budget/context) or is missing required template sections, so decisions aren't made on stale figures.

- main · function · L45-L77 — Reads the resume file, collects violations (empty file, leftover placeholders, missing sections, forbidden numbers) and exits 1 with a red report if any are found, else 0 green.
