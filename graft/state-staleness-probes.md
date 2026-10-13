---
name: State & Staleness Probes
slug: state-staleness-probes
type: system
sources:
  - path: scripts/ops/staleness-report.py
    hash: 3076f30a8be1b80c196dec59ede54a8a67f314edf5af263f37c234f09dabeb55
  - path: scripts/ops/state-snapshot.py
    hash: 3112f4632b64a6b531b215ea81ba82b2ceb6436942511f816de94ced3171bfe8
sources_digest: 29dedeec004a4ac67aaa14675d886b3baa6b91e5eafd52ccf2d96577da9b03a8
links:
  - to: harness-loop-core
    relation: uses
    description: >-
      state-snapshot is invoked per-cycle by the harness; its DELTA semantics
      state that 'none' does not mean 'nothing to do' — standing orders still
      apply.
  - to: work-window-brake
    relation: produces
    description: >-
      state-snapshot.py's DELTA line is the input the work-window brake parses
      to decide whether a change opened a K-cycle window.
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

Read-only probes that collapse per-cycle state checks into single turns and measure document staleness. state-snapshot.py computes a DELTA line against a previous snapshot so an unchanged world can be dismissed without re-probing, always exits 0 so a probe failure never kills the calling cycle, and implements OPREQ-INFRA-ANALYST-ROUTING-001 Option B by making the auditor report hash delta-visible. staleness-report.py generates a deterministic markdown report for the Program Auditor with mechanical flags like 'ARŞİV ADAYI' and 'BOŞLUK', tracking a re-charter date (2026-08-24) to identify pre-recharter decisions needing archival.

## Related

- uses [[harness-loop-core]] — state-snapshot is invoked per-cycle by the harness; its DELTA semantics state that 'none' does not mean 'nothing to do' — standing orders still apply.
- produces [[work-window-brake]] — state-snapshot.py's DELTA line is the input the work-window brake parses to decide whether a change opened a K-cycle window.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
