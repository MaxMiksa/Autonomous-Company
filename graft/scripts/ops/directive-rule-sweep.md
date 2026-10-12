# scripts/ops/directive-rule-sweep.py · [[evidence-extraction-validation]] [[human-directive-lifecycle]]

Scans directive bodies for rule-shaped lines and flags any whose distinctive tokens do not survive in standing files, reporting candidates for human review while failing loudly when coverage cannot be measured.

- key_phrases · function · L49-L52 — Extracts distinctive long tokens from a rule line, filtering out common words and pure digits, to serve as the fingerprint for coverage matching.
- covered · function · L55-L68 — Screens a rule line for coverage by measuring token overlap with standing text, trusted only in the negative direction to force human review on low scores.
