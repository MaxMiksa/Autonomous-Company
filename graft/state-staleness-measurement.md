---
name: State & Staleness Measurement
slug: state-staleness-measurement
type: system
sources:
  - path: scripts/ops/staleness-report.py
    hash: fd956d858b53eb269fd45f5afcbe12917eff9170943e3a07ad758c2a25aea18e
  - path: scripts/ops/state-snapshot.py
    hash: 3112f4632b64a6b531b215ea81ba82b2ceb6436942511f816de94ced3171bfe8
sources_digest: 3cf046b4672b1fa2c8394ef8e2ab2dcbb0a52e339abc5155c4ee757d3de5159b
links:
  - to: harness-loop-core
    relation: uses
    description: >-
      state-snapshot is invoked per-cycle; its output feeds the work-window
      brake and the auditor report hash is delta-visible
      (OPREQ-INFRA-ANALYST-ROUTING-001 Option B).
  - to: work-window-brake
    relation: produces
    description: >-
      work-window.py consumes state-snapshot's DELTA line to decide whether a
      change opens a K-cycle window.
generator:
  version: 1
covers:
  - symbol: _bytes
    kind: function
    at: 'scripts/ops/staleness-report.py:L42-L43'
  - symbol: _read
    kind: function
    at: 'scripts/ops/staleness-report.py:L46-L50'
  - symbol: _sections
    kind: function
    at: 'scripts/ops/staleness-report.py:L53-L60'
  - symbol: _heading_date
    kind: function
    at: 'scripts/ops/staleness-report.py:L63-L70'
  - symbol: directive_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L73-L91'
  - symbol: opreq_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L94-L104'
  - symbol: decisions_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L107-L112'
  - symbol: consensus_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L115-L122'
  - symbol: ledger_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L125-L147'
  - symbol: prompt_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L150-L157'
  - symbol: weekly_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L160-L173'
  - symbol: _accepted_weekly_gaps
    kind: function
    at: 'scripts/ops/staleness-report.py:L180-L196'
  - symbol: backup_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L202-L218'
  - symbol: build
    kind: function
    at: 'scripts/ops/staleness-report.py:L221-L229'
  - symbol: main
    kind: function
    at: 'scripts/ops/staleness-report.py:L232-L249'
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

Read-only probes that measure the health and rot of the company's memory surfaces. state-snapshot.py collapses per-cycle state checks into one grep-friendly probe with a DELTA line against a previous snapshot (always exits 0 so a probe failure never kills the cycle). staleness-report.py computes mechanical 'bayatlık' flags across eight surfaces (directive, operator-requests, decisions, consensus, conflict ledger, PROMPT.md, weekly reports, backups) into memories/staleness-report.md, using section codes rather than cycle numbers to avoid false positives and mtime for backup age. Both are purely advisory — the auditor interprets, never recomputes.

## Related

- uses [[harness-loop-core]] — state-snapshot is invoked per-cycle; its output feeds the work-window brake and the auditor report hash is delta-visible (OPREQ-INFRA-ANALYST-ROUTING-001 Option B).
- produces [[work-window-brake]] — work-window.py consumes state-snapshot's DELTA line to decide whether a change opens a K-cycle window.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
