---
name: Operator Action Router
slug: operator-action-router
type: file
sources:
  - path: scripts/ops/operator-action-router.py
    hash: 25fd8206f44d0baa7b87a910d0d1846fe5ef1b155289d1a769994aff6817587e
  - path: tests/test_operator_action_router.py
    hash: 20f6bd56ba2238d0242627275af5749560272630a1212f9f9f22159d655d99ae
sources_digest: eeb9735b11ba0ec109f87f095cfa8affc6afd00ebf34698caca0a50d1304a1aa
links:
  - to: consensus-memory-state-files
    relation: uses
    description: Reads operator-requests.md and human-directive.md
  - to: operator-request-resolution
    relation: uses
    description: >-
      Both read the same memories/ inputs; router renders the digest the
      operator sees.
  - to: telegram-notification-channel
    relation: uses
    description: Sends the consolidated digest via telegram-notify.sh
generator:
  version: 1
covers:
  - symbol: _now
    kind: function
    at: 'scripts/ops/operator-action-router.py:L78-L79'
  - symbol: read_hold
    kind: function
    at: 'scripts/ops/operator-action-router.py:L82-L102'
  - symbol: read_opreqs
    kind: function
    at: 'scripts/ops/operator-action-router.py:L105-L118'
  - symbol: read_directive
    kind: function
    at: 'scripts/ops/operator-action-router.py:L121-L134'
  - symbol: collect_items
    kind: function
    at: 'scripts/ops/operator-action-router.py:L137-L174'
  - symbol: render
    kind: function
    at: 'scripts/ops/operator-action-router.py:L177-L183'
  - symbol: set_hash
    kind: function
    at: 'scripts/ops/operator-action-router.py:L186-L189'
  - symbol: should_notify
    kind: function
    at: 'scripts/ops/operator-action-router.py:L192-L207'
  - symbol: load_state
    kind: function
    at: 'scripts/ops/operator-action-router.py:L210-L214'
  - symbol: write_state
    kind: function
    at: 'scripts/ops/operator-action-router.py:L217-L225'
  - symbol: clear_state
    kind: function
    at: 'scripts/ops/operator-action-router.py:L228-L232'
  - symbol: notify
    kind: function
    at: 'scripts/ops/operator-action-router.py:L235-L251'
  - symbol: main
    kind: function
    at: 'scripts/ops/operator-action-router.py:L254-L296'
  - symbol: check
    kind: function
    at: 'tests/test_operator_action_router.py:L27-L33'
  - symbol: check_true
    kind: function
    at: 'tests/test_operator_action_router.py:L36-L37'
  - symbol: make_app
    kind: function
    at: 'tests/test_operator_action_router.py:L40-L67'
---
<!-- context:generated:start -->
## Summary

operator-action-router.py is a Telegram firehose digest consolidating the operator's actionable items into a single what-needs-YOU message, covering only locally-truthful signals: a LOOP_HOLD latch, open OPREQ entries, and a PENDING directive past a floor age. It hashes the open set's stable identity into state and only speaks when the set changes or ROUTER_REPEAT_HOURS elapses, deliberately excluding Airtable-backed queues and Sentry liveness because those need network calls or run outside the container. Advisory-only, never writes to Airtable/Linear/directive.

## Related

- uses [[consensus-memory-state-files]] — Reads operator-requests.md and human-directive.md
- uses [[operator-request-resolution]] — Both read the same memories/ inputs; router renders the digest the operator sees.
- uses [[telegram-notification-channel]] — Sends the consolidated digest via telegram-notify.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
