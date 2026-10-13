# scripts/context-watch.py

A Claude Code hook that watches context-window fullness from the last assistant message's usage and emits warning/compact-ritual messages at 50%/60% thresholds, once per session, re-arming after a compact.

- kullanim · function · L33-L50 — Reads the tail of the transcript and sums input, cache-read, and cache-creation tokens from the most recent assistant message to report the current context size.
- main · function · L53-L102 — Computes the context fullness percentage, escalates the window tier if measured tokens exceed it, and fires one-time warn/act messages per session while re-arming thresholds after a compact-induced drop.
