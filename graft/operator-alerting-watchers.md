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
sources_digest: 5c3c228beb25ca54708c6ee339112c30711eb6f9e12a565531de8aa90bda240e
links:
  - to: rfq-send-pipeline
    relation: uses
    description: >-
      rfq-reply-watch deliberately omits the delivery-failure branch because
      rfq-send.py only marks successful sends; the watcher's classify logic
      depends on the send pipeline's status conventions.
  - to: telegram-notification-core
    relation: uses
    description: >-
      All watchers shell out to scripts/core/telegram-notify.sh with tokens
      loaded from logs/runtime.env.
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
---
<!-- context:generated:start -->
## Summary

A family of advisory, read-only watcher scripts that monitor Airtable queues and outreach rows to tell an operator when human attention is warranted. They never write back to Airtable or re-send; each maintains a local JSON state file for once-per-outcome throttling and shells out to scripts/core/telegram-notify.sh with secrets from logs/runtime.env. Distinct problems are deliberately separated in messages (e.g. 'operator is the bottleneck' vs 'we never asked'), and EKAP/MERSİS pending rows are treated as one shared scarce resource.

## Related

- uses [[rfq-send-pipeline]] — rfq-reply-watch deliberately omits the delivery-failure branch because rfq-send.py only marks successful sends; the watcher's classify logic depends on the send pipeline's status conventions.
- uses [[telegram-notification-core]] — All watchers shell out to scripts/core/telegram-notify.sh with tokens loaded from logs/runtime.env.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
