---
name: staleness reporting
slug: staleness-reporting
type: system
sources:
  - path: scripts/ops/staleness-report.py
    hash: ebae44b614629bd12ad5e8db730b3eb731008cd740b6e73893cedb810c052516
  - path: tests/test_staleness_report.py
    hash: a44cd7942f29212d4962691ed3c4fd98e824f985aaa323307cc88db4ed53e325
sources_digest: 2dce7de19cfe256542930e480015f0f5cfcf1bf4621512f1027651cff911ece6
links: []
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
    at: 'scripts/ops/staleness-report.py:L120-L142'
  - symbol: prompt_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L145-L152'
  - symbol: weekly_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L155-L168'
  - symbol: _accepted_weekly_gaps
    kind: function
    at: 'scripts/ops/staleness-report.py:L175-L191'
  - symbol: backup_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L197-L213'
  - symbol: build
    kind: function
    at: 'scripts/ops/staleness-report.py:L216-L224'
  - symbol: main
    kind: function
    at: 'scripts/ops/staleness-report.py:L227-L244'
  - symbol: check
    kind: function
    at: 'tests/test_staleness_report.py:L17-L20'
  - symbol: main
    kind: function
    at: 'tests/test_staleness_report.py:L23-L102'
---
<!-- context:generated:start -->
## Summary

scripts/ops/staleness-report.py audits an app tree for stale or bloated memory files: archive candidates, resolved-request text, pre-recharter decisions, stale ledger headers, oversized PROMPT.md with legacy words, weekly gaps, and old backups. Avoids false positives on recent or explicitly accepted content.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
