---
name: Compliance & evidence checks
slug: compliance-evidence-checks
type: system
sources:
  - path: scripts/ops/context7-check.py
    hash: 4687b776e558caf660fad0d984e405c6a9498525648273569ac9a5feb544797e
  - path: scripts/ops/extract-axis-evidence.py
    hash: 3f3d55a2a285cd52ab3b0d286b1f908b877283bfde69b03e442d10758080f567
sources_digest: 585d5e97541debae2a2681bc1625726e37b37dd0645d95725d87131075642849
links: []
generator:
  version: 1
covers:
  - symbol: externals
    kind: function
    at: 'scripts/ops/context7-check.py:L59-L75'
  - symbol: scan
    kind: function
    at: 'scripts/ops/context7-check.py:L78-L108'
  - symbol: walk_calls
    kind: function
    at: 'scripts/ops/context7-check.py:L111-L122'
  - symbol: verdict
    kind: function
    at: 'scripts/ops/context7-check.py:L125-L138'
  - symbol: main
    kind: function
    at: 'scripts/ops/context7-check.py:L141-L170'
---
<!-- context:generated:start -->
## Summary

Deterministic compliance and evidence-integrity checkers: context7-check detects whether an agent imported an external library without first calling the Context7 MCP tool (parsing JSON lines rather than regexing code payloads to avoid silent false negatives), extract-axis-evidence packs screened axis headings with strict validation (any heading/body mismatch fails closed), and g4-check tests identity claims against live evidence. These report to logs rather than blocking, and are designed to be calibrated via --report flags.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
