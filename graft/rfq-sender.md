---
name: RFQ sender
slug: rfq-sender
type: system
sources:
  - path: scripts/ops/rfq-send.py
    hash: 09815061d704b6bd2034469e3bfe3dfac7417f25761ea9ae845be4c5367fd225
  - path: tests/test_rfq_send.sh
    hash: da4d25d4be3529f89c4c62e9b7099278b95d98a4336a9762bfe6c01e31030a97
sources_digest: bf2e173450385e76019b2d680d7979018f692a27942a94211466a4943a05ce2d
links:
  - to: prod-mechanism-guard
    relation: validates
    description: rfq-send.py is a protected surface registered in the guard
  - to: registry-outreach-watchers
    relation: uses
    description: targets the RFQ Airtable table
generator:
  version: 1
covers:
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

rfq-send.py is the buyer-side RFQ sender with security invariants: §15 sponsor-approval field and _sponsor_ok function, absence of any G4 gate usage, ANON_DENY anonymity denylist, and correct Airtable table IDs (RFQ table tblzcGP7kNfkmPDGJ, not the frozen tender table tbl1fZbNmolrEXAMy). It is registered in prod-mechanism-guard.py and must pass --check-sync. Live --report asserts fail-closed behavior (ALLOW: 0) and the §15 REFUSE branch.

## Related

- validates [[prod-mechanism-guard]] — rfq-send.py is a protected surface registered in the guard
- uses [[registry-outreach-watchers]] — targets the RFQ Airtable table
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
