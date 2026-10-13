---
name: registry & staleness maintenance
slug: registry-staleness-maintenance
type: system
sources:
  - path: tests/test_registry_archive.sh
    hash: 4ca1be679dfb4867f1e05625b59c587e0a40e525f53c35404d535f93017e5c76
  - path: tests/test_staleness_report.py
    hash: 801eb2b9aa75f6a46c2273932b2325140b7564492dfa8b5a33943e5e81bd6c2b
  - path: tests/test_state_snapshot.sh
    hash: 44428d24f7cb21d69c1f03477dd4b07ce31b98c94879131f75d58d146aa08729
sources_digest: 00145f5e4d4c1df98f8cf64edc30a821dc03cc574d4b458efba0a1604309043f
links:
  - to: auto-loop-core-engine
    relation: uses
    description: >-
      state-snapshot.py DELTA output drives idle detection and work-window
      gating
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

Maintenance scripts for long-lived markdown state: registry-archive.py archives stale dated sections from the candidate registry while preserving a protected live span byte-identically (idempotent, eligibility-aware), and staleness-report.py generates memories/staleness-report.md flagging stale sections, archive candidates, oversized PROMPT content, weekly gaps, and backup cleanup. state-snapshot.py produces the DELTA change-detection snapshot (all fields local since 2026-08-24 re-charter).

## Related

- uses [[auto-loop-core-engine]] — state-snapshot.py DELTA output drives idle detection and work-window gating
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
