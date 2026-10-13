---
name: Operator Alerting Watchers
slug: operator-alerting-watchers
type: system
sources:
  - path: scripts/ops/registry-queue-watch.py
    hash: 0ef6723d089c54ee8272050eb2776ce81af9de986e8f6dc15b065b7bbd913497
  - path: scripts/ops/reply-watch.py
    hash: 110e009b20f709db9dda31e2e17af9fb061696a869901bd389dddedca9294070
  - path: scripts/ops/rfq-reply-watch.py
    hash: a6ab97903f7cb5a67e749e16ded1a76ba0e022f2faf2e19ce7b0ad094ab441a7
  - path: scripts/ops/turn-bloat-brake.py
    hash: c4d72b732830311e89db486abb41c8a13a5760ffa043354c953b99a155ff96fb
  - path: scripts/ops/work-window-watchdog.py
    hash: 228677456f5e5634b3c6a9964c8b92e13a4c2e4992154feed8a3334779fd0a5f
sources_digest: d431d8b8ff18258c3e612e92834f125e30d7c801c7f9c1aa0f8c9d04746ef185
links:
  - to: airtable-access-wrappers
    relation: uses
    description: >-
      Watchers paginate Airtable tables via the REST API, filtering to
      sent/non-TEST rows
  - to: fail-closed-harness-brakes
    relation: implements
    description: >-
      turn-bloat-brake and work-window-watchdog complement the per-cycle
      advisory brakes with streak-based hard mandates and alarms
  - to: telegram-notification-core
    relation: uses
    description: >-
      Each watcher shells out to scripts/core/telegram-notify.sh, sourcing
      secrets from logs/runtime.env
generator:
  version: 1
covers:
  - symbol: api_key
    kind: function
    at: 'scripts/ops/registry-queue-watch.py:L48-L58'
  - symbol: fetch
    kind: function
    at: 'scripts/ops/registry-queue-watch.py:L61-L77'
  - symbol: main
    kind: function
    at: 'scripts/ops/registry-queue-watch.py:L80-L215'
  - symbol: api_key
    kind: function
    at: 'scripts/ops/reply-watch.py:L46-L56'
  - symbol: fetch
    kind: function
    at: 'scripts/ops/reply-watch.py:L59-L74'
  - symbol: notify
    kind: function
    at: 'scripts/ops/reply-watch.py:L77-L91'
  - symbol: first_ts
    kind: function
    at: 'scripts/ops/reply-watch.py:L94-L99'
  - symbol: hours_since
    kind: function
    at: 'scripts/ops/reply-watch.py:L102-L112'
  - symbol: main
    kind: function
    at: 'scripts/ops/reply-watch.py:L115-L142'
  - symbol: classify
    kind: function
    at: 'scripts/ops/reply-watch.py:L145-L223'
  - symbol: api_key
    kind: function
    at: 'scripts/ops/rfq-reply-watch.py:L36-L46'
  - symbol: fetch
    kind: function
    at: 'scripts/ops/rfq-reply-watch.py:L49-L64'
  - symbol: notify
    kind: function
    at: 'scripts/ops/rfq-reply-watch.py:L67-L80'
  - symbol: first_ts
    kind: function
    at: 'scripts/ops/rfq-reply-watch.py:L83-L88'
  - symbol: hours_since
    kind: function
    at: 'scripts/ops/rfq-reply-watch.py:L91-L106'
  - symbol: main
    kind: function
    at: 'scripts/ops/rfq-reply-watch.py:L109-L134'
  - symbol: classify
    kind: function
    at: 'scripts/ops/rfq-reply-watch.py:L137-L195'
  - symbol: _app
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L25-L26'
  - symbol: _streak_len
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L29-L34'
  - symbol: _load
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L37-L41'
  - symbol: _save
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L44-L51'
  - symbol: main
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L63-L104'
  - symbol: _app_dir
    kind: function
    at: 'scripts/ops/work-window-watchdog.py:L45-L48'
  - symbol: _threshold
    kind: function
    at: 'scripts/ops/work-window-watchdog.py:L51-L57'
  - symbol: _read_state
    kind: function
    at: 'scripts/ops/work-window-watchdog.py:L60-L64'
  - symbol: _write_state
    kind: function
    at: 'scripts/ops/work-window-watchdog.py:L67-L74'
  - symbol: main
    kind: function
    at: 'scripts/ops/work-window-watchdog.py:L77-L125'
---
<!-- context:generated:start -->
## Summary

A family of advisory, read-only watcher scripts that monitor Airtable queues and local state to alert an operator via Telegram when human attention is warranted. They never write back to Airtable, never send, and never block the harness loop — they only detect conditions (pending bridge rows, replies/silence, RFQ replies, empty-cycle confirmations, bloat streaks) and notify. Each maintains its own small JSON state file for once-per-outcome throttling and supports --dry-run/--fixture so prod and test share the same classify code path.

## Related

- uses [[airtable-access-wrappers]] — Watchers paginate Airtable tables via the REST API, filtering to sent/non-TEST rows
- implements [[fail-closed-harness-brakes]] — turn-bloat-brake and work-window-watchdog complement the per-cycle advisory brakes with streak-based hard mandates and alarms
- uses [[telegram-notification-core]] — Each watcher shells out to scripts/core/telegram-notify.sh, sourcing secrets from logs/runtime.env
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
