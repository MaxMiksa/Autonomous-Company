---
name: directive writer & lifecycle
slug: directive-writer-lifecycle
type: system
sources:
  - path: scripts/core/directive_writer.py
    hash: 276871ed21c1686f9b10a2179256e93b609c818f77a7b7e5f31a7e6681829da4
  - path: tests/test_directive_section_refs.sh
    hash: 413742241d956ae77feb01e20780757ee86fa63f3699e3926a2ddeea81a53a71
  - path: tests/test_directive_writer.py
    hash: 8246a641c797789b53117ec96cd0a3922bad2d9c5dc9ba873e13daf579f35a73
sources_digest: f456d20cd989a7b06f252662d99da68444662a3f7e242702ea50c53655786971
links:
  - to: auto-loop-core-engine
    relation: uses
    description: >-
      The loop reads directive status/pending state to gate escalation and cycle
      behavior.
  - to: operator-request-resolution
    relation: produces
    description: >-
      Directive decisions (Decision for OPREQ-<id> lines) are consumed by
      operator_request_notify.py to resolve requests.
generator:
  version: 1
covers:
  - symbol: undefined_section_refs
    kind: function
    at: 'scripts/core/directive_writer.py:L100-L109'
  - symbol: now
    kind: function
    at: 'scripts/core/directive_writer.py:L112-L113'
  - symbol: sha
    kind: function
    at: 'scripts/core/directive_writer.py:L116-L117'
  - symbol: read_live
    kind: function
    at: 'scripts/core/directive_writer.py:L120-L126'
  - symbol: body_of
    kind: function
    at: 'scripts/core/directive_writer.py:L129-L136'
  - symbol: audit
    kind: function
    at: 'scripts/core/directive_writer.py:L139-L145'
  - symbol: _telegram_env
    kind: function
    at: 'scripts/core/directive_writer.py:L148-L171'
  - symbol: notify
    kind: function
    at: 'scripts/core/directive_writer.py:L174-L184'
  - symbol: _why_pending
    kind: function
    at: 'scripts/core/directive_writer.py:L187-L215'
  - symbol: backup
    kind: function
    at: 'scripts/core/directive_writer.py:L218-L232'
  - symbol: normalize_ownership
    kind: function
    at: 'scripts/core/directive_writer.py:L235-L281'
  - symbol: atomic_write
    kind: function
    at: 'scripts/core/directive_writer.py:L284-L296'
  - symbol: verify_written
    kind: function
    at: 'scripts/core/directive_writer.py:L299-L303'
  - symbol: Refused
    kind: class
    at: 'scripts/core/directive_writer.py:L306-L307'
  - symbol: live_body
    kind: function
    at: 'scripts/core/directive_writer.py:L312-L315'
  - symbol: split_body
    kind: function
    at: 'scripts/core/directive_writer.py:L318-L337'
  - symbol: section_sizes
    kind: function
    at: 'scripts/core/directive_writer.py:L340-L344'
  - symbol: size_brake
    kind: function
    at: 'scripts/core/directive_writer.py:L347-L363'
  - symbol: _pending_gate
    kind: function
    at: 'scripts/core/directive_writer.py:L366-L382'
  - symbol: _refuse_section_refs
    kind: function
    at: 'scripts/core/directive_writer.py:L385-L393'
  - symbol: with_lock
    kind: function
    at: 'scripts/core/directive_writer.py:L396-L405'
  - symbol: wrapper
    kind: function
    at: 'scripts/core/directive_writer.py:L397-L404'
  - symbol: cmd_write
    kind: function
    at: 'scripts/core/directive_writer.py:L418-L472'
  - symbol: cmd_append
    kind: function
    at: 'scripts/core/directive_writer.py:L476-L504'
  - symbol: cmd_archive
    kind: function
    at: 'scripts/core/directive_writer.py:L508-L572'
  - symbol: cmd_status
    kind: function
    at: 'scripts/core/directive_writer.py:L576-L610'
  - symbol: cmd_restore
    kind: function
    at: 'scripts/core/directive_writer.py:L614-L650'
  - symbol: cmd_show
    kind: function
    at: 'scripts/core/directive_writer.py:L653-L664'
  - symbol: main
    kind: function
    at: 'scripts/core/directive_writer.py:L667-L725'
  - symbol: _refuse_forbidden
    kind: function
    at: 'scripts/core/directive_writer.py:L706-L712'
  - symbol: fn
    kind: function
    at: 'scripts/core/directive_writer.py:L707-L711'
  - symbol: check
    kind: function
    at: 'tests/test_directive_writer.py:L22-L25'
  - symbol: Env
    kind: class
    at: 'tests/test_directive_writer.py:L28-L52'
  - symbol: __init__
    kind: method
    at: 'tests/test_directive_writer.py:L29-L32'
  - symbol: run
    kind: method
    at: 'tests/test_directive_writer.py:L34-L36'
  - symbol: live
    kind: method
    at: 'tests/test_directive_writer.py:L38-L39'
  - symbol: audit
    kind: method
    at: 'tests/test_directive_writer.py:L41-L43'
  - symbol: show
    kind: method
    at: 'tests/test_directive_writer.py:L45-L47'
  - symbol: f
    kind: method
    at: 'tests/test_directive_writer.py:L49-L52'
  - symbol: main
    kind: function
    at: 'tests/test_directive_writer.py:L63-L155'
---
<!-- context:generated:start -->
## Summary

scripts/core/directive_writer.py manages the human-directive.md lifecycle: write/append/status/show/archive subcommands, PENDING gate, body_sha256 staleness checks, undefined §-reference rejection, size brakes with --force-size override, and archive with resolver-section guard and prefix-matching rules. undefined_section_refs() guards against the bug that froze directive revision 11 (references to absent §6/§7).

## Related

- uses [[auto-loop-core-engine]] — The loop reads directive status/pending state to gate escalation and cycle behavior.
- produces [[operator-request-resolution]] — Directive decisions (Decision for OPREQ-<id> lines) are consumed by operator_request_notify.py to resolve requests.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
