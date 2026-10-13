---
name: RFQ reply watch
slug: rfq-reply-watch
type: file
sources:
  - path: scripts/ops/rfq-reply-watch.py
    hash: a6ab97903f7cb5a67e749e16ded1a76ba0e022f2faf2e19ce7b0ad094ab441a7
  - path: tests/test_rfq_reply_watch.sh
    hash: 67f49fb6296af24a61aa9a5b8bae530f3cb2db42d5ef68d6f6c2a5989d073cb0
sources_digest: 838c9fd50e895e3914dcdaf7b9d176d4ffbd94fa7e79f1ae1597d847673a77ef
links:
  - to: outreach-watchers
    relation: part_of
    description: Shares the reply/silence classification pattern with reply-watch.py
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
---
<!-- context:generated:start -->
## Summary

scripts/ops/rfq-reply-watch.py watches RFQ rows in Airtable for replies and silence: replied rows are reported exactly once and never marked silent, silence is reported as an observation (not a verdict) with age, and the script is advisory (no write operations) targeting the RFQ table tblzcGP7kNfkmPDGJ while avoiding the tender table tbl1fZbNmolrEXAMy and tender-seller language (İKN, Stage 2). State persists in logs/rfq-reply-watch-state.json; --dry-run leaves no state file.

## Related

- part of [[outreach-watchers]] — Shares the reply/silence classification pattern with reply-watch.py
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
