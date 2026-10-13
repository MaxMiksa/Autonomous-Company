# scripts/core/codex-final-text.py · [[final-text-extraction-jcode-codex]]

Standalone script that extracts the assistant's final message text from a codex exec JSONL event stream, failing soft so callers can fall back to raw content.

- final_text · function · L30-L47 — Parses each JSONL line and concatenates the text of all item.completed agent_message items, ignoring malformed lines and non-agent_message events.
- main · function · L50-L60 — CLI entry point that reads the events file, prints the extracted text, and returns exit code 1 when no agent message was found so the caller falls back to raw content.
