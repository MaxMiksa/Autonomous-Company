---
name: state snapshot & staleness
slug: state-snapshot-staleness
type: system
sources:
  - path: tests/test_staleness_report.py
    hash: 801eb2b9aa75f6a46c2273932b2325140b7564492dfa8b5a33943e5e81bd6c2b
  - path: tests/test_state_snapshot.sh
    hash: 44428d24f7cb21d69c1f03477dd4b07ce31b98c94879131f75d58d146aa08729
sources_digest: 2b12e02d6b0544b4edc04b94dcc8276dbc5812d6df8add42ea0c7a25fda880b8
links:
  - to: work-window-watchdog
    relation: produces
    description: DELTA lines feed the work-window brake
generator:
  version: 1
covers:
  - symbol: check
    kind: function
    at: 'tests/test_staleness_report.py:L15-L18'
  - symbol: main
    kind: function
    at: 'tests/test_staleness_report.py:L21-L69'
---
<!-- context:generated:start -->
## Summary

state-snapshot.py produces the DELTA change-detection output (first-run, none, named changes, error exclusion) with all fields local since a 2026-08-24 re-charter (bridge/send/reply fields retired); a missing ledger prints an error but still exits 0, and errored fields are excluded from the next DELTA. staleness-report.py generates memories/staleness-report.md flagging stale sections, archive candidates, resolved-request text, pre-recharter decisions, consensus Prior counts, stale ledger headers, oversized PROMPT content with legacy words, weekly gaps, and backup cleanup recommendations.

## Related

- produces [[work-window-watchdog]] — DELTA lines feed the work-window brake
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
