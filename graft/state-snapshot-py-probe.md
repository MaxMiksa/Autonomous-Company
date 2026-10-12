---
name: state-snapshot.py probe
slug: state-snapshot-py-probe
type: file
sources:
  - path: scripts/ops/state-snapshot.py
    hash: 3112f4632b64a6b531b215ea81ba82b2ceb6436942511f816de94ced3171bfe8
sources_digest: b49055f6ad2667278243a5d453a6f3a32f13b362f453588327ababae654d5019
links:
  - to: work-window-brake-watchdog
    relation: produces
    description: >-
      Emits the DELTA: line that work-window.py parses to open/close the work
      window.
generator:
  version: 1
covers:
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

A one-call probe that collapses the per-cycle fan-out of state checks into a single turn, printing a compact grep-friendly report of five watched surfaces (directive status/SHA-16, open OPREQ-* blocks, auditor report hash, combined Wowcar source hash, operator-decisions hash) plus a DELTA line against the previous snapshot. Always exits 0 so a probe failure never kills the calling cycle; errored fields print as ERROR and are excluded from DELTA on both sides. Implements OPREQ-INFRA-ANALYST-ROUTING-001 Option B by making the auditor report hash delta-visible; DELTA semantics explicitly state 'none' does not mean 'nothing to do' — standing orders still apply.

## Related

- produces [[work-window-brake-watchdog]] — Emits the DELTA: line that work-window.py parses to open/close the work window.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
