---
name: outreach outcome watchers
slug: outreach-outcome-watchers
type: system
sources:
  - path: scripts/ops/reply-watch.py
    hash: 110e009b20f709db9dda31e2e17af9fb061696a869901bd389dddedca9294070
  - path: tests/test_reply_watch.sh
    hash: a1291856a346b22fd46c2d1179ae6602778674b7f930d53c4216e449e286b67f
sources_digest: ce5714749921b9400cfaa17af0fe9932f3146e57178b31a75e3812be36b83d8e
links:
  - to: rfq-sender-watchers
    relation: uses
    description: Shares the reply/silence classification pattern.
generator:
  version: 1
covers:
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
---
<!-- context:generated:start -->
## Summary

reply-watch.py classifies email replies, bounces, and silence for firms: replies reported once and never as silence, bounces flagged as delivery failures (explicitly 'SESSİZLİK DEĞİLDİR'), fresh sends stay quiet, old unanswered rows become silence with age, silence phrased as observation ('hüküm değil'), state persistence suppresses duplicate alerts, and a failure superseded by a later Sent (Rayelsis case) is not reported as a delivery problem. Uses lexicographically comparable ISO timestamps and a 72-hour threshold.

## Related

- uses [[rfq-sender-watchers]] — Shares the reply/silence classification pattern.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
