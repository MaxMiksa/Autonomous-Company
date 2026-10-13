---
name: staleness reporting
slug: staleness-reporting
type: file
sources:
  - path: scripts/ops/staleness-report.py
    hash: 3076f30a8be1b80c196dec59ede54a8a67f314edf5af263f37c234f09dabeb55
  - path: tests/test_staleness_report.py
    hash: 801eb2b9aa75f6a46c2273932b2325140b7564492dfa8b5a33943e5e81bd6c2b
sources_digest: 0e0c17cb7f53f675464af4a7f10656db2f7d14e09b3e580fa6f4a11ab8f51b4e
links:
  - to: registry-tooling
    relation: uses
    description: Both scan memories/ and candidate registry files.
generator:
  version: 1
covers:
  - symbol: _bytes
    kind: function
    at: 'scripts/ops/staleness-report.py:L37-L38'
  - symbol: _read
    kind: function
    at: 'scripts/ops/staleness-report.py:L41-L45'
  - symbol: _sections
    kind: function
    at: 'scripts/ops/staleness-report.py:L48-L55'
  - symbol: _heading_date
    kind: function
    at: 'scripts/ops/staleness-report.py:L58-L65'
  - symbol: directive_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L68-L86'
  - symbol: opreq_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L89-L99'
  - symbol: decisions_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L102-L107'
  - symbol: consensus_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L110-L117'
  - symbol: ledger_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L120-L132'
  - symbol: prompt_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L135-L142'
  - symbol: weekly_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L145-L155'
  - symbol: backup_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L158-L168'
  - symbol: build
    kind: function
    at: 'scripts/ops/staleness-report.py:L171-L179'
  - symbol: main
    kind: function
    at: 'scripts/ops/staleness-report.py:L182-L199'
  - symbol: check
    kind: function
    at: 'tests/test_staleness_report.py:L15-L18'
  - symbol: main
    kind: function
    at: 'tests/test_staleness_report.py:L21-L69'
---
<!-- context:generated:start -->
## Summary

scripts/ops/staleness-report.py scans the memories/ tree and produces memories/staleness-report.md with Turkish-language flags for stale sections, archive candidates, resolved-request text, pre-recharter decisions, consensus Prior counts, stale ledger headers, oversized PROMPT content with legacy words, weekly gaps, and backup cleanup recommendations. Supports --stdout and a fixed --today date for deterministic testing.

## Related

- uses [[registry-tooling]] — Both scan memories/ and candidate registry files.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
