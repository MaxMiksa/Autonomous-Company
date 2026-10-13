---
name: ops watchers & guards
slug: ops-watchers-guards
type: system
sources:
  - path: tests/test_ledger_guard.py
    hash: d0118c31c5f02cb01c7ad332056d6ec8c8951338d217999eda93e15dce90a354
  - path: tests/test_registry_queue_watch.sh
    hash: 0c823a0b115d8fb57d7a64e25cb89f725943078e58504a22aa5306a416ac6668
  - path: tests/test_reply_watch.sh
    hash: a1291856a346b22fd46c2d1179ae6602778674b7f930d53c4216e449e286b67f
  - path: tests/test_rfq_reply_watch.sh
    hash: 67f49fb6296af24a61aa9a5b8bae530f3cb2db42d5ef68d6f6c2a5989d073cb0
  - path: tests/test_tool_usage_audit.sh
    hash: 4bdf9378fc2af04ed89fc9559aa1fcc8520846c6847f13302f613ec896bfde6d
  - path: tests/test_turn_audit.sh
    hash: ce3eb2af3fea266a763a0ca266f3c658f8498b604570c229141654d685f6c9e8
  - path: tests/test_turn_bloat_brake.py
    hash: 9599b12fa9480d0058872f2facb8d329c5deac8177df794c41982d955d887a74
  - path: tests/test_work_window_watchdog.py
    hash: 43cd4a904f4badbb8ce3a4ee88adff57b790ff6c8067435e361617f37a10de40
  - path: tests/test_work_window.py
    hash: 234b10df540fe8774d445855295b088c68cdb23003bdd95c1c22debbd93a6c5e
sources_digest: 26ee96f71590861ef94495f4ed68b9582abcc3f352d2744fff37f81872d706be
links:
  - to: auto-loop-core-engine
    relation: uses
    description: >-
      The loop invokes these watchers/brakes per cycle; work-window gates
      whether a cycle proceeds
generator:
  version: 1
covers:
  - symbol: newapp
    kind: function
    at: 'tests/test_ledger_guard.py:L15-L20'
  - symbol: ledger
    kind: function
    at: 'tests/test_ledger_guard.py:L23-L24'
  - symbol: run
    kind: function
    at: 'tests/test_ledger_guard.py:L27-L33'
  - symbol: body
    kind: function
    at: 'tests/test_ledger_guard.py:L36-L42'
  - symbol: check
    kind: function
    at: 'tests/test_ledger_guard.py:L45-L48'
  - symbol: newapp
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L15-L18'
  - symbol: rec
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L21-L27'
  - symbol: fb
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L30-L36'
  - symbol: consecutive
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L39-L40'
  - symbol: check
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L43-L46'
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

A family of monitoring/guard scripts in scripts/ops that watch external state and emit alarms or block actions: reply-watch.py and rfq-reply-watch.py (outreach/RFQ replies, bounces, silence as observations not verdicts, state-persisted dedup), registry-queue-watch.py (bottleneck attribution distinguishing empty bridge queue from operator gap), work-window.py and work-window-watchdog.py (empty-cycle brake and alarm layer), turn-audit.py and turn-bloat-brake.py (turn-economy policy with verdict thresholds and streak alarms), ledger-guard.py (unexpected ledger changes), and tool-usage-audit.py (jcode event-stream categorization with idempotent ledger).

## Related

- uses [[auto-loop-core-engine]] — The loop invokes these watchers/brakes per cycle; work-window gates whether a cycle proceeds
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
