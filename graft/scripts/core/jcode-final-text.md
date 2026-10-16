# scripts/core/jcode-final-text.py · [[final-text-extraction]]

Extracts the full assistant text from a jcode --ndjson stream, preferring concatenated text_delta events over done.text to avoid silent truncation of the final answer.

- final_text · function · L30-L48 — Reads an ndjson event stream and returns the longest of the concatenated text_delta payloads or the done message, guarding against done.text carrying only a fragment of the final answer.
- main · function · L51-L61 — CLI entry that reads the events file, prints the extracted text, and returns a nonzero exit code when the result is empty.
