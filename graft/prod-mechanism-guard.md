---
name: prod-mechanism guard
slug: prod-mechanism-guard
type: system
sources:
  - path: scripts/prod-mechanism-guard.py
    hash: e3d5c01038affa27aaed85106b6b8ff0705c6be14fa3b2caa1c21144fde5acee
  - path: tests/test_prod_mechanism_guard.sh
    hash: 1c8df67eca679e21cbbe4ea2daac7f761fc952f17b25f99d2673a4782ffa6824
sources_digest: 85f0fc7428c6e4e3dfe8a3574ea24ed99ff361f071029bc7d1a9cbef79456bc1
links:
  - to: auto-loop-core-engine
    relation: validates
    description: Blocks unapproved edits to auto-loop.sh and other protected surfaces.
  - to: send-gate-outreach-policy
    relation: validates
    description: rfq-send.py must be registered and pass --check-sync.
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

scripts/prod-mechanism-guard.py is a PreToolUse hook blocking edits to production-critical surfaces (auto-loop.sh, send-gate.py, deploy/runtime.env) with a 3-hour override window via a fresh .claude/.prod-change-approved marker, fail-open on malformed JSON, no-op for container paths, and a --check-sync mode that detects drift between CLAUDE.md's documented protected surfaces and the actual PROTECTED_* list.

## Related

- validates [[auto-loop-core-engine]] — Blocks unapproved edits to auto-loop.sh and other protected surfaces.
- validates [[send-gate-outreach-policy]] — rfq-send.py must be registered and pass --check-sync.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
