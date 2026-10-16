---
name: state snapshot & staleness
slug: state-snapshot-staleness
type: system
sources:
  - path: scripts/ops/staleness-report.py
    hash: fd956d858b53eb269fd45f5afcbe12917eff9170943e3a07ad758c2a25aea18e
  - path: scripts/ops/state-snapshot.py
    hash: 3112f4632b64a6b531b215ea81ba82b2ceb6436942511f816de94ced3171bfe8
  - path: tests/test_staleness_report.py
    hash: 82f05db4129519fbfe630bda2ee5e3abcfeafb393abf9fb479ba3b3900a4bd08
  - path: tests/test_state_snapshot.sh
    hash: 44428d24f7cb21d69c1f03477dd4b07ce31b98c94879131f75d58d146aa08729
sources_digest: deb740463ad5e72be728200a4f8a39866570b58e2be8c1e3cbe6740fc8aec8c4
links:
  - to: work-window-watchdog-brakes
    relation: produces
    description: The DELTA output feeds work-window.py's open/closed decision.
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
  - symbol: check
    kind: function
    at: 'tests/test_staleness_report.py:L17-L20'
  - symbol: main
    kind: function
    at: 'tests/test_staleness_report.py:L23-L123'
---
<!-- context:generated:start -->
## Summary

state-snapshot.py produces the DELTA change-detection snapshot (directive status/sha16, OPREQ open counts) with --skip-network, excluding errored fields from the next DELTA and exiting 0 on missing ledger; staleness-report.py audits memory files for archive candidates, stale headers, shrink flags, weekly report gaps, and backup cleanup thresholds with --today and --stdout modes.

## Related

- produces [[work-window-watchdog-brakes]] — The DELTA output feeds work-window.py's open/closed decision.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
