---
name: Human Directive Write Path
slug: human-directive-write-path
type: file
sources:
  - path: scripts/core/directive_writer.py
    hash: 276871ed21c1686f9b10a2179256e93b609c818f77a7b7e5f31a7e6681829da4
sources_digest: 6eed857116759502f9b268374ade298389b21ffe785742f41950c601357badb5
links:
  - to: consensus-memory-state-files
    relation: configures
    description: Writes and maintains memories/human-directive.md
  - to: directive-staleness-coverage-watchers
    relation: validates
    description: >-
      directive-staleness-watch.py and directive-rule-sweep.py audit the
      directive's status and rule coverage
  - to: operator-escalation-gate
    relation: uses
    description: >-
      operator_request_notify.py reads explicit directives in human-directive.md
      as resolution evidence
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
---
<!-- context:generated:start -->
## Summary

directive_writer.py is the single locked write path for memories/human-directive.md, enforcing two fail-closed rules: in-flight PENDING directives are never clobbered without --allow-pending, and the directive body is immutable after acceptance except for a compare-and-swap status transition. It runs a pipeline of file lock, in-flight gate, persistent backup, atomic rename, read-back verification, audit logging, and Telegram notification, with OPREQ-GOV-DIRECTIVE-BODY-001 rejecting bodies referencing undefined §N sections and a size brake at 50KB/90KB.

## Related

- configures [[consensus-memory-state-files]] — Writes and maintains memories/human-directive.md
- validates [[directive-staleness-coverage-watchers]] — directive-staleness-watch.py and directive-rule-sweep.py audit the directive's status and rule coverage
- uses [[operator-escalation-gate]] — operator_request_notify.py reads explicit directives in human-directive.md as resolution evidence
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
