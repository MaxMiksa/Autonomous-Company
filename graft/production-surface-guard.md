---
name: Production Surface Guard
slug: production-surface-guard
type: system
sources:
  - path: scripts/prod-mechanism-guard.py
    hash: e3d5c01038affa27aaed85106b6b8ff0705c6be14fa3b2caa1c21144fde5acee
sources_digest: a8778c76c2d84b2d7e9fe72981362b4bad9b3fde2625b2005cf87674c41bea8c
links:
  - to: harness-loop-core
    relation: validates
    description: >-
      Enforces the Prod-Mechanism Change Rule from CLAUDE.md against writes to
      scripts/core/auto-loop.sh, dashboard/server.py, Dockerfile, runtime.env.
generator:
  version: 1
covers:
  - symbol: is_protected
    kind: function
    at: 'scripts/prod-mechanism-guard.py:L49-L52'
  - symbol: check_sync
    kind: function
    at: 'scripts/prod-mechanism-guard.py:L55-L81'
  - symbol: main
    kind: function
    at: 'scripts/prod-mechanism-guard.py:L84-L126'
---
<!-- context:generated:start -->
## Summary

The tripwire layer protecting production surfaces from unplanned writes. prod-mechanism-guard.py is a PreToolUse hook that blocks Edit/Write/NotebookEdit to protected suffixes/basenames unless a fresh .prod-change-approved marker (120-min TTL) exists, with a --check-sync drift detector verifying CLAUDE.md's rule section covers every backtick-referenced surface. It is deliberately fail-open on malformed stdin and no-ops when CLAUDE_PROJECT_DIR points to /app (deferring to PROMPT.md's OPREQ authorization machine). Known limitation: sed -i in Bash bypasses it entirely — it's a tripwire, not a boundary.

## Related

- validates [[harness-loop-core]] — Enforces the Prod-Mechanism Change Rule from CLAUDE.md against writes to scripts/core/auto-loop.sh, dashboard/server.py, Dockerfile, runtime.env.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
