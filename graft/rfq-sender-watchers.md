---
name: RFQ sender & watchers
slug: rfq-sender-watchers
type: system
sources:
  - path: scripts/ops/rfq-reply-watch.py
    hash: a6ab97903f7cb5a67e749e16ded1a76ba0e022f2faf2e19ce7b0ad094ab441a7
  - path: scripts/ops/rfq-send.py
    hash: 09815061d704b6bd2034469e3bfe3dfac7417f25761ea9ae845be4c5367fd225
  - path: tests/test_rfq_reply_watch.sh
    hash: 67f49fb6296af24a61aa9a5b8bae530f3cb2db42d5ef68d6f6c2a5989d073cb0
  - path: tests/test_rfq_send.sh
    hash: da4d25d4be3529f89c4c62e9b7099278b95d98a4336a9762bfe6c01e31030a97
sources_digest: 380b3e4cc15d4bd3fef14174e8377dea834c4a0aec7140b2b424441d1a8139fd
links:
  - to: g4-compliance-checks
    relation: validates
    description: rfq-send.py must not use G4 gates (asserted).
  - to: outreach-outcome-watchers
    relation: uses
    description: Shares the reply/silence classification pattern with reply-watch.py.
generator:
  version: 1
covers:
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
  - symbol: _load_key
    kind: function
    at: 'scripts/ops/rfq-send.py:L61-L82'
  - symbol: _app_dir
    kind: function
    at: 'scripts/ops/rfq-send.py:L85-L87'
  - symbol: _air
    kind: function
    at: 'scripts/ops/rfq-send.py:L91-L103'
  - symbol: _record
    kind: function
    at: 'scripts/ops/rfq-send.py:L106-L107'
  - symbol: _all_rows
    kind: function
    at: 'scripts/ops/rfq-send.py:L110-L121'
  - symbol: _sponsor_ok
    kind: function
    at: 'scripts/ops/rfq-send.py:L125-L126'
  - symbol: _opted_out
    kind: function
    at: 'scripts/ops/rfq-send.py:L129-L130'
  - symbol: _already_sent
    kind: function
    at: 'scripts/ops/rfq-send.py:L133-L134'
  - symbol: _email_of
    kind: function
    at: 'scripts/ops/rfq-send.py:L137-L139'
  - symbol: _caps_now
    kind: function
    at: 'scripts/ops/rfq-send.py:L142-L152'
  - symbol: render
    kind: function
    at: 'scripts/ops/rfq-send.py:L155-L163'
  - symbol: anonymity_scan
    kind: function
    at: 'scripts/ops/rfq-send.py:L166-L171'
  - symbol: decide
    kind: function
    at: 'scripts/ops/rfq-send.py:L174-L197'
  - symbol: send_fe
    kind: function
    at: 'scripts/ops/rfq-send.py:L201-L226'
  - symbol: _mark_sent
    kind: function
    at: 'scripts/ops/rfq-send.py:L229-L232'
  - symbol: main
    kind: function
    at: 'scripts/ops/rfq-send.py:L236-L278'
---
<!-- context:generated:start -->
## Summary

Buyer-side RFQ tooling: rfq-send.py (sender with §15 sponsor-approval gate, ANON_DENY anonymity denylist, correct RFQ table tblzcGP7kNfkmPDGJ and never the frozen tender table tbl1fZbNmolrEXAMy, no G4 usage) and rfq-reply-watch.py (advisory reply/silence watcher on the RFQ table, avoiding tender-seller language like İKN/Stage 2, 72-hour silence threshold, state persistence, --dry-run writes no state).

## Related

- validates [[g4-compliance-checks]] — rfq-send.py must not use G4 gates (asserted).
- uses [[outreach-outcome-watchers]] — Shares the reply/silence classification pattern with reply-watch.py.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
