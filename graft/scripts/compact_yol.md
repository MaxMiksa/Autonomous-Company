# scripts/compact_yol.py · [[compact-ritual]] [[compact-ritual-tooling]]

Module that derives repo-specific /tmp paths for compact ritual files so concurrent projects never read each other's resume/preflight state.

- temizle · function · L57-L60 — Normalizes a raw name to lowercase [a-z0-9-] with a fallback default so path components are always safe and non-empty.
- _git · function · L63-L69 — Runs a git command with a timeout and returns trimmed stdout, failing open with empty string on any error.
- repo_adi · function · L72-L89 — Computes the repo-derived name (with worktree suffix) used to build unique compact paths, falling back to the root dir name when git is unavailable.
- yol · function · L92-L95 — Returns the path for a compact file type, preferring the env override and otherwise formatting the repo-derived /tmp path.
- main · function · L98-L107 — CLI entry that prints the requested path or repo name, validating the type argument and returning proper exit codes.
