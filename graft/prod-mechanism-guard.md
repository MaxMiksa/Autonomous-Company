---
name: prod-mechanism guard
slug: prod-mechanism-guard
type: file
sources:
  - path: tests/test_prod_mechanism_guard.sh
    hash: 1c8df67eca679e21cbbe4ea2daac7f761fc952f17b25f99d2673a4782ffa6824
sources_digest: bdb259f08d24f80a2819e8b7ef84bd6ad99c9a2524f41664136ac3d5c33790b4
links:
  - to: send-gate-rfq-send
    relation: validates
    description: Blocks edits to these production scripts unless override marker is fresh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

scripts/prod-mechanism-guard.py is a PreToolUse hook blocking edits to production-critical surfaces (auto-loop.sh, send-gate.py, deploy/runtime.env) with a 3-hour override via a fresh .claude/.prod-change-approved marker. Fails open on malformed JSON, ignores container paths like /app. --check-sync parses the '## Prod-Mechanism Change Rule' section of CLAUDE.md to detect drift between documented and actual PROTECTED_* lists.

## Related

- validates [[send-gate-rfq-send]] — Blocks edits to these production scripts unless override marker is fresh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
