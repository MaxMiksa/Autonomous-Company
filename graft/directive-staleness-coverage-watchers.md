---
name: Directive Staleness & Coverage Watchers
slug: directive-staleness-coverage-watchers
type: system
sources:
  - path: scripts/ops/directive-rule-sweep.py
    hash: 7284bd834ff1cf86bcc5f6d104cf23388bf9258dcc827b681f578e6ce7172c57
  - path: scripts/ops/directive-staleness-watch.py
    hash: 6597a8a3666b54131d1b782a8d8ee308e705e33dbed83429da857f9b1f0360fd
sources_digest: 72dca44a648f671b33d192ba19637eb703aa6164d5968c3652a46dd92a214e9f
links:
  - to: human-directive-write-path
    relation: validates
    description: Audits the directive's PENDING status and rule coverage
  - to: telegram-notification-channel
    relation: uses
    description: Sends staleness alerts via telegram-notify.sh
generator:
  version: 1
covers:
  - symbol: key_phrases
    kind: function
    at: 'scripts/ops/directive-rule-sweep.py:L49-L52'
  - symbol: covered
    kind: function
    at: 'scripts/ops/directive-rule-sweep.py:L55-L68'
  - symbol: read_directive
    kind: function
    at: 'scripts/ops/directive-staleness-watch.py:L40-L56'
  - symbol: last_line_matching
    kind: function
    at: 'scripts/ops/directive-staleness-watch.py:L59-L66'
  - symbol: main
    kind: function
    at: 'scripts/ops/directive-staleness-watch.py:L69-L165'
---
<!-- context:generated:start -->
## Summary

Operational watchers on the human directive: directive-staleness-watch.py alerts when human-directive.md stays PENDING beyond a threshold (because the completion clause can only be satisfied by market evidence or an explicit terminal decision), persisting last_notified to avoid spamming a 15-minute cron and never editing the directive. directive-rule-sweep.py audits which rule-like statements exist only in ephemeral directive files and are not backed by standing documentation, using a canary fixture (zibberflux) to verify the heuristic and exiting code 3 if the canary isn't flagged or the live directive can't be read.

## Related

- validates [[human-directive-write-path]] — Audits the directive's PENDING status and rule coverage
- uses [[telegram-notification-channel]] — Sends staleness alerts via telegram-notify.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
