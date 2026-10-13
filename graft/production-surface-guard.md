---
name: Production Surface Guard
slug: production-surface-guard
type: file
sources:
  - path: scripts/prod-mechanism-guard.py
    hash: e3d5c01038affa27aaed85106b6b8ff0705c6be14fa3b2caa1c21144fde5acee
sources_digest: a8778c76c2d84b2d7e9fe72981362b4bad9b3fde2625b2005cf87674c41bea8c
links:
  - to: auto-loop-harness
    relation: validates
    description: >-
      Protects scripts/core/auto-loop.sh and other prod surfaces from unplanned
      edits
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

A PreToolUse tripwire hook for Claude Code that mechanically blocks unplanned writes to protected production surfaces (scripts/core/auto-loop.sh, dashboard/server.py, Dockerfile, runtime.env) unless a fresh 120-minute marker file exists. It is deliberately fail-open on malformed stdin so harness format changes don't lock all edits, no-ops when CLAUDE_PROJECT_DIR points to /app (deferring to PROMPT.md's OPREQ authorization machine), and includes a --check-sync drift detector that verifies every backtick-referenced surface in CLAUDE.md's rule section is covered. Known limitation: sed -i in Bash bypasses the guard entirely — it's a tripwire, not a boundary.

## Related

- validates [[auto-loop-harness]] — Protects scripts/core/auto-loop.sh and other prod surfaces from unplanned edits
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
