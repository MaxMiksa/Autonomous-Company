---
name: Memory Staleness & Snapshot Probes
slug: memory-staleness-snapshot-probes
type: system
sources:
  - path: scripts/ops/staleness-report.py
    hash: ebae44b614629bd12ad5e8db730b3eb731008cd740b6e73893cedb810c052516
  - path: scripts/ops/state-snapshot.py
    hash: 3112f4632b64a6b531b215ea81ba82b2ceb6436942511f816de94ced3171bfe8
sources_digest: f92ca02060669c378b36a34db8f70ba54e9a9e2f8ee50d32236fc84dc10c7c92
links:
  - to: memory-ledger-files
    relation: uses
    description: >-
      Both read memories/human-directive.md, operator-requests.md,
      operator-decisions.md, consensus.md and related docs
  - to: work-window-brake
    relation: produces
    description: >-
      state-snapshot.py's DELTA line is the input the work-window brake parses
      to detect surface changes
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
  - symbol: file_sha16
    kind: function
    at: 'scripts/ops/state-snapshot.py:L54-L61'
  - symbol: directive_state
    kind: function
    at: 'scripts/ops/state-snapshot.py:L64-L72'
  - symbol: opreq_open
    kind: function
    at: 'scripts/ops/state-snapshot.py:L75-L87'
  - symbol: wowcar_sources
    kind: function
    at: 'scripts/ops/state-snapshot.py:L90-L104'
  - symbol: main
    kind: function
    at: 'scripts/ops/state-snapshot.py:L107-L166'
---
<!-- context:generated:start -->
## Summary

Read-only, stdlib-only probes that mechanically measure the Program Auditor's memory surfaces. staleness-report.py writes a markdown report of 'bayatlık' flags (ARŞİV ADAYI, BÖLÜMLE, etc.) that the auditor treats as suggestions, never recomputing them; state-snapshot.py collapses per-cycle state checks into one grep-friendly DELTA line against a previous snapshot so an unchanged world can be dismissed. Both always exit 0 so a probe failure never kills the calling cycle, and both write only their own state files atomically.

## Related

- uses [[memory-ledger-files]] — Both read memories/human-directive.md, operator-requests.md, operator-decisions.md, consensus.md and related docs
- produces [[work-window-brake]] — state-snapshot.py's DELTA line is the input the work-window brake parses to detect surface changes
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
