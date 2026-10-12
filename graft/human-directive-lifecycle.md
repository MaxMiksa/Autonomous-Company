---
name: Human Directive Lifecycle
slug: human-directive-lifecycle
type: system
sources:
  - path: scripts/core/directive_writer.py
    hash: 447057795ab4776c589695bd00450009df0af8fff481fa7a68c89244ca93a9a3
  - path: scripts/ops/directive-rule-sweep.py
    hash: 7284bd834ff1cf86bcc5f6d104cf23388bf9258dcc827b681f578e6ce7172c57
  - path: scripts/ops/directive-staleness-watch.py
    hash: 6597a8a3666b54131d1b782a8d8ee308e705e33dbed83429da857f9b1f0360fd
sources_digest: c33cb878c31200586210f16883cbed0fb7ab8b0c0df83d67bf6c473d9edb06db
links:
  - to: operator-escalation-gate
    relation: uses
    description: >-
      operator_request_notify resolves requests via explicit directives in
      human-directive.md
  - to: operator-notification-channel
    relation: uses
    description: >-
      directive_writer and staleness-watch send Telegram alerts via
      telegram-notify.sh
generator:
  version: 1
covers:
  - symbol: undefined_section_refs
    kind: function
    at: 'scripts/core/directive_writer.py:L74-L83'
  - symbol: now
    kind: function
    at: 'scripts/core/directive_writer.py:L86-L87'
  - symbol: sha
    kind: function
    at: 'scripts/core/directive_writer.py:L90-L91'
  - symbol: read_live
    kind: function
    at: 'scripts/core/directive_writer.py:L94-L100'
  - symbol: body_of
    kind: function
    at: 'scripts/core/directive_writer.py:L103-L110'
  - symbol: audit
    kind: function
    at: 'scripts/core/directive_writer.py:L113-L119'
  - symbol: _telegram_env
    kind: function
    at: 'scripts/core/directive_writer.py:L122-L145'
  - symbol: notify
    kind: function
    at: 'scripts/core/directive_writer.py:L148-L158'
  - symbol: _why_pending
    kind: function
    at: 'scripts/core/directive_writer.py:L161-L189'
  - symbol: backup
    kind: function
    at: 'scripts/core/directive_writer.py:L192-L206'
  - symbol: normalize_ownership
    kind: function
    at: 'scripts/core/directive_writer.py:L209-L255'
  - symbol: atomic_write
    kind: function
    at: 'scripts/core/directive_writer.py:L258-L270'
  - symbol: verify_written
    kind: function
    at: 'scripts/core/directive_writer.py:L273-L277'
  - symbol: Refused
    kind: class
    at: 'scripts/core/directive_writer.py:L280-L281'
  - symbol: with_lock
    kind: function
    at: 'scripts/core/directive_writer.py:L284-L293'
  - symbol: wrapper
    kind: function
    at: 'scripts/core/directive_writer.py:L285-L292'
  - symbol: cmd_write
    kind: function
    at: 'scripts/core/directive_writer.py:L306-L359'
  - symbol: cmd_status
    kind: function
    at: 'scripts/core/directive_writer.py:L363-L397'
  - symbol: cmd_restore
    kind: function
    at: 'scripts/core/directive_writer.py:L401-L437'
  - symbol: cmd_show
    kind: function
    at: 'scripts/core/directive_writer.py:L440-L445'
  - symbol: main
    kind: function
    at: 'scripts/core/directive_writer.py:L448-L495'
  - symbol: _refuse_forbidden
    kind: function
    at: 'scripts/core/directive_writer.py:L476-L482'
  - symbol: fn
    kind: function
    at: 'scripts/core/directive_writer.py:L477-L481'
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

The single-writer, fail-closed management of memories/human-directive.md: writes are gated against clobbering in-flight PENDING directives, the body is immutable after acceptance (only ## Status changes via compare-and-swap on body hash), and staleness watchers alert when a PENDING directive ages past a threshold. Includes the operator-only baseline/reconcile path that is hard-refused in the CLI and delegated to a host-side script.

## Related

- uses [[operator-escalation-gate]] — operator_request_notify resolves requests via explicit directives in human-directive.md
- uses [[operator-notification-channel]] — directive_writer and staleness-watch send Telegram alerts via telegram-notify.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
