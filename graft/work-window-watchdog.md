---
name: work window & watchdog
slug: work-window-watchdog
type: system
sources:
  - path: tests/test_work_window_watchdog.py
    hash: 43cd4a904f4badbb8ce3a4ee88adff57b790ff6c8067435e361617f37a10de40
  - path: tests/test_work_window.py
    hash: a96f98fab6378be083bf2356d09c42ee4d0af332ec573cfa88182f2008cde326
sources_digest: 33f52d656a3eeef8e7106652b41d84f8ed252718106b720e147fc90982e78d55
links:
  - to: auto-loop-core-engine
    relation: uses
    description: Consumes DELTA lines produced by the loop's state snapshot
generator:
  version: 1
covers:
  - symbol: run
    kind: function
    at: 'tests/test_work_window.py:L21-L42'
  - symbol: check
    kind: function
    at: 'tests/test_work_window.py:L45-L48'
  - symbol: run
    kind: function
    at: 'tests/test_work_window_watchdog.py:L18-L29'
  - symbol: check
    kind: function
    at: 'tests/test_work_window_watchdog.py:L32-L35'
---
<!-- context:generated:start -->
## Summary

The empty-cycle work-window brake (work-window.py) and its alarm layer (work-window-watchdog.py). The brake opens on a changed DELTA, stays open through idle cycles until ttl_cycles elapses, closes on negative age (restart guard), fails closed on corrupt state or missing DELTA, and has a WORK_WINDOW_ENABLED=0 kill switch. A directive rule (2026-10-13) prevents DONE pulls/archives from opening the window while PENDING appends still do. The watchdog emits an alarm only once when the consecutive empty-cycle count crosses a threshold (not on every violation), resets on real work, has an escape clause for enumerated blockers, and does not count a 'failed' cycle as a violation.

## Related

- uses [[auto-loop-core-engine]] — Consumes DELTA lines produced by the loop's state snapshot
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
