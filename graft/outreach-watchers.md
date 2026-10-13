---
name: outreach watchers
slug: outreach-watchers
type: concept
sources:
  - path: scripts/ops/reply-watch.py
    hash: 110e009b20f709db9dda31e2e17af9fb061696a869901bd389dddedca9294070
  - path: scripts/ops/rfq-reply-watch.py
    hash: a6ab97903f7cb5a67e749e16ded1a76ba0e022f2faf2e19ce7b0ad094ab441a7
  - path: tests/test_reply_watch.sh
    hash: a1291856a346b22fd46c2d1179ae6602778674b7f930d53c4216e449e286b67f
  - path: tests/test_rfq_reply_watch.sh
    hash: 67f49fb6296af24a61aa9a5b8bae530f3cb2db42d5ef68d6f6c2a5989d073cb0
sources_digest: 4dd186cd2336e4dddcf115233ea68cd711e66af380f31ea33aa621b61e810c89
links:
  - to: rfq-reply-watch
    relation: implements
    description: rfq-reply-watch.py is the RFQ-specific instance of this pattern
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

The reply/silence classification pattern shared by reply-watch.py and rfq-reply-watch.py: replies are reported once and never as silence, bounces are flagged as delivery failures (explicitly 'SESSİZLİK DEĞİLDİR'), fresh sends stay quiet, old unanswered rows become 'silence' with age, and a replied row is never also silent. Silence alerts are phrased as observations ('hüküm değil'), state persistence suppresses duplicate alerts on a second run, --dry-run writes no state file, and a failure superseded by a later Sent (the Rayelsis case) is not reported as a delivery problem. Uses lexicographically comparable ISO timestamps and a 72-hour silence threshold.

## Related

- implements [[rfq-reply-watch]] — rfq-reply-watch.py is the RFQ-specific instance of this pattern
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
