# scripts/prod-mechanism-guard.py · [[prod-mechanism-guard]] [[production-mechanism-guard]]

PreToolUse tripwire that mechanically blocks unplanned edits/writes to protected prod surfaces unless a fresh operator-approval marker exists, and can verify the rule section in CLAUDE.md stays in sync with the protected list.

- is_protected · function · L49-L52 — Decides whether a given path is a protected prod surface by matching against configured suffixes and basenames.
- check_sync · function · L55-L81 — Detects scope drift by parsing backtick tokens from CLAUDE.md's rule section and failing if any named surface is not covered by the protected lists.
- main · function · L84-L126 — Enforces the prod-change rule at edit time: no-ops in container, parses the hook payload, and blocks writes to protected files unless a non-stale approval marker exists.
