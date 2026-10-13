---
name: State File Throttling & Atomicity
slug: state-file-throttling-atomicity
type: concept
sources:
  - path: scripts/ops/registry-queue-watch.py
    hash: 0ef6723d089c54ee8272050eb2776ce81af9de986e8f6dc15b065b7bbd913497
  - path: scripts/ops/reply-watch.py
    hash: 110e009b20f709db9dda31e2e17af9fb061696a869901bd389dddedca9294070
  - path: scripts/ops/rfq-reply-watch.py
    hash: a6ab97903f7cb5a67e749e16ded1a76ba0e022f2faf2e19ce7b0ad094ab441a7
  - path: scripts/ops/state-snapshot.py
    hash: 3112f4632b64a6b531b215ea81ba82b2ceb6436942511f816de94ced3171bfe8
  - path: scripts/ops/tool-usage-audit.py
    hash: 73a75d68bab3e0b42e31ad3d268b44a8c7ac168b91c6a8d1b2f1b3cd4cdba975
  - path: scripts/ops/turn-bloat-brake.py
    hash: c4d72b732830311e89db486abb41c8a13a5760ffa043354c953b99a155ff96fb
  - path: scripts/ops/work-window-watchdog.py
    hash: 228677456f5e5634b3c6a9964c8b92e13a4c2e4992154feed8a3334779fd0a5f
sources_digest: add1f0c2f41cb0a293f0eaeb53e03e85cae8fcfb14849b7f59bc876e186b6d16
links:
  - to: cycle-cost-bloat-governance
    relation: implements
    description: >-
      tool-usage-audit and turn-bloat-brake persist state atomically and dedupe
      on robust keys.
  - to: operator-alerting-watchers
    relation: implements
    description: >-
      Each watcher maintains a local JSON state file ensuring each row alerts
      only once per outcome.
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
  - symbol: calls_from_ndjson
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L43-L65'
  - symbol: categorize
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L68-L121'
  - symbol: main
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L124-L251'
  - symbol: dump
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L177-L190'
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

A recurring pattern where ops scripts persist small JSON state files (logs/*.json) to throttle notifications, dedupe work, or track streaks, and write them atomically via temp file + os.replace so a crash never corrupts state. Dedup keys are chosen carefully: tool-usage-audit dedups on filename+size+mtime (not name alone, because the cycle counter restarts on container restart), watchers alert at most once per outcome class, and turn-bloat-brake resets its streak on any non-BLOATED verdict and stays quiet after the crossing alarm to avoid spam.

## Related

- implements [[cycle-cost-bloat-governance]] — tool-usage-audit and turn-bloat-brake persist state atomically and dedupe on robust keys.
- implements [[operator-alerting-watchers]] — Each watcher maintains a local JSON state file ensuring each row alerts only once per outcome.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
