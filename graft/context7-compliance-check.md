---
name: Context7 Compliance Check
slug: context7-compliance-check
type: file
sources:
  - path: scripts/ops/context7-check.py
    hash: 4687b776e558caf660fad0d984e405c6a9498525648273569ac9a5feb544797e
sources_digest: 7b9324b6606ae2451e7e0e246f5f0afc951e0c21403a03d682250a5b8758309e
links:
  - to: tool-surface-compliance
    relation: implements
    description: >-
      Enforces the rule that external-library imports must be preceded by a
      Context7 call
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

Compliance checker that inspects per-cycle ndjson logs to detect whether an agent wrote code importing an external library without first calling the Context7 MCP tool. Deliberately parses JSON lines rather than regexing code payloads (which caused silent false negatives), treats missing stdlib entries as false positives only, and reports to the LOG rather than blocking.

## Related

- implements [[tool-surface-compliance]] — Enforces the rule that external-library imports must be preceded by a Context7 call
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
