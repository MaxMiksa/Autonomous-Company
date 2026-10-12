---
name: Prod-mechanism guard
slug: prod-mechanism-guard
type: file
sources:
  - path: scripts/prod-mechanism-guard.py
    hash: e3d5c01038affa27aaed85106b6b8ff0705c6be14fa3b2caa1c21144fde5acee
  - path: tests/test_prod_mechanism_guard.sh
    hash: 1c8df67eca679e21cbbe4ea2daac7f761fc952f17b25f99d2673a4782ffa6824
sources_digest: 85f0fc7428c6e4e3dfe8a3574ea24ed99ff361f071029bc7d1a9cbef79456bc1
links:
  - to: auto-loop-core-engine
    relation: validates
    description: protects auto-loop.sh from unapproved edits
  - to: auto-loop-harness
    relation: validates
    description: >-
      Protects scripts/core/auto-loop.sh and other protected surfaces from
      unplanned edits.
  - to: outreach-send-gate
    relation: validates
    description: protects send-gate.py from unapproved edits
  - to: rfq-sender
    relation: validates
    description: rfq-send.py is registered as a protected surface
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

A PreToolUse tripwire hook for Claude Code that mechanically blocks unplanned writes to protected production surfaces (scripts/core/auto-loop.sh, dashboard/server.py, Dockerfile, runtime.env) unless a fresh marker file .claude/.prod-change-approved (120-min TTL) exists. Includes a --check-sync drift detector that parses CLAUDE.md's rule section and verifies every backtick-referenced surface is covered. Deliberately fail-open on malformed stdin so harness format changes don't lock all edits, and no-ops entirely when CLAUDE_PROJECT_DIR points to /app, deferring to PROMPT.md's OPREQ authorization machine. Known limitation: sed -i in Bash bypasses the guard entirely — it's a tripwire, not a boundary.

## Related

- validates [[auto-loop-core-engine]] — protects auto-loop.sh from unapproved edits
- validates [[auto-loop-harness]] — Protects scripts/core/auto-loop.sh and other protected surfaces from unplanned edits.
- validates [[outreach-send-gate]] — protects send-gate.py from unapproved edits
- validates [[rfq-sender]] — rfq-send.py is registered as a protected surface
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
