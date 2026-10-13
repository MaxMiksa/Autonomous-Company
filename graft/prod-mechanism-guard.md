---
name: prod-mechanism guard
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
    description: auto-loop.sh is a protected path blocked from edits without approval
  - to: rfq-sender
    relation: validates
    description: rfq-send.py must be registered in the guard and pass --check-sync
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

scripts/prod-mechanism-guard.py is a PreToolUse hook that blocks edits to production-critical surfaces (scripts/core/auto-loop.sh, scripts/ops/send-gate.py, deploy/runtime.env, etc.) with exit code 2, granting a 3-hour override window via a fresh .claude/.prod-change-approved marker (stale markers rejected). Fails open on malformed JSON, no-ops on container paths like /app, and leaves non-Edit tools untouched. --check-sync parses the '## Prod-Mechanism Change Rule' section of CLAUDE.md to detect drift between documented protected surfaces and the actual PROTECTED_* list, failing closed on missing sections while tolerating mechanism-token mentions elsewhere.

## Related

- validates [[auto-loop-core-engine]] — auto-loop.sh is a protected path blocked from edits without approval
- validates [[rfq-sender]] — rfq-send.py must be registered in the guard and pass --check-sync
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
