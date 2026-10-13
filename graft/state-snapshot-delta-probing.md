---
name: State Snapshot & Delta Probing
slug: state-snapshot-delta-probing
type: system
sources:
  - path: scripts/ops/staleness-report.py
    hash: 3076f30a8be1b80c196dec59ede54a8a67f314edf5af263f37c234f09dabeb55
  - path: scripts/ops/state-snapshot.py
    hash: 3112f4632b64a6b531b215ea81ba82b2ceb6436942511f816de94ced3171bfe8
  - path: scripts/ops/work-window.py
    hash: 4c83c4f5b2509f134cdc1183e7b0e208e07e67fab50aa1946718daa98e5d68a5
sources_digest: 1d0a0057ce0df907e00e7272f398bfdf5f1a049ce1c3c6992e408080a2e0009f
links:
  - to: fail-closed-harness-brakes
    relation: produces
    description: DELTA lines drive work-window.py's open/closed decision
  - to: operator-alerting-watchers
    relation: uses
    description: Watchers read the same state files and snapshot hashes
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
  - symbol: _app_dir
    kind: function
    at: 'scripts/ops/work-window.py:L52-L56'
  - symbol: _env_int
    kind: function
    at: 'scripts/ops/work-window.py:L59-L66'
  - symbol: _parse_delta
    kind: function
    at: 'scripts/ops/work-window.py:L69-L78'
  - symbol: _read_state
    kind: function
    at: 'scripts/ops/work-window.py:L81-L88'
  - symbol: _write_state
    kind: function
    at: 'scripts/ops/work-window.py:L91-L95'
  - symbol: _line
    kind: function
    at: 'scripts/ops/work-window.py:L98-L108'
  - symbol: main
    kind: function
    at: 'scripts/ops/work-window.py:L111-L181'
---
<!-- context:generated:start -->
## Summary

One-call probes that collapse per-cycle state checks into a single turn and compute DELTA lines so an unchanged world can be dismissed without re-probing. state-snapshot.py hashes five watched surfaces (directive, OPREQ blocks, auditor report, Wowcar sources, decisions) and always exits 0 so a probe failure never kills the cycle; work-window.py consumes the DELTA line to decide whether follow-on work is orphaned. staleness-report.py is a separate deterministic read-only report measuring document age for the Program Auditor.

## Related

- produces [[fail-closed-harness-brakes]] — DELTA lines drive work-window.py's open/closed decision
- uses [[operator-alerting-watchers]] — Watchers read the same state files and snapshot hashes
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
