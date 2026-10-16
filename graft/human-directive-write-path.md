---
name: Human directive write path
slug: human-directive-write-path
type: file
sources:
  - path: scripts/core/directive_writer.py
    hash: 2b00db428f705544c6b980dd3b76f3e35e0dc76ca44eb82a2d023c7d1b9bb45a
sources_digest: 023c56a03d6ec25b996a5340319855374414f507c1169e8f3832a0e9e3b207fc
links: []
generator:
  version: 1
covers:
  - symbol: undefined_section_refs
    kind: function
    at: 'scripts/core/directive_writer.py:L104-L113'
  - symbol: now
    kind: function
    at: 'scripts/core/directive_writer.py:L116-L117'
  - symbol: sha
    kind: function
    at: 'scripts/core/directive_writer.py:L120-L121'
  - symbol: read_live
    kind: function
    at: 'scripts/core/directive_writer.py:L124-L130'
  - symbol: body_of
    kind: function
    at: 'scripts/core/directive_writer.py:L133-L140'
  - symbol: audit
    kind: function
    at: 'scripts/core/directive_writer.py:L143-L149'
  - symbol: _telegram_env
    kind: function
    at: 'scripts/core/directive_writer.py:L152-L175'
  - symbol: notify
    kind: function
    at: 'scripts/core/directive_writer.py:L178-L188'
  - symbol: _why_pending
    kind: function
    at: 'scripts/core/directive_writer.py:L191-L219'
  - symbol: backup
    kind: function
    at: 'scripts/core/directive_writer.py:L222-L236'
  - symbol: normalize_ownership
    kind: function
    at: 'scripts/core/directive_writer.py:L239-L285'
  - symbol: atomic_write
    kind: function
    at: 'scripts/core/directive_writer.py:L288-L300'
  - symbol: verify_written
    kind: function
    at: 'scripts/core/directive_writer.py:L303-L307'
  - symbol: Refused
    kind: class
    at: 'scripts/core/directive_writer.py:L310-L311'
  - symbol: live_body
    kind: function
    at: 'scripts/core/directive_writer.py:L316-L319'
  - symbol: split_body
    kind: function
    at: 'scripts/core/directive_writer.py:L322-L345'
  - symbol: section_sizes
    kind: function
    at: 'scripts/core/directive_writer.py:L348-L352'
  - symbol: size_brake
    kind: function
    at: 'scripts/core/directive_writer.py:L355-L371'
  - symbol: _pending_gate
    kind: function
    at: 'scripts/core/directive_writer.py:L374-L390'
  - symbol: _refuse_section_refs
    kind: function
    at: 'scripts/core/directive_writer.py:L393-L401'
  - symbol: with_lock
    kind: function
    at: 'scripts/core/directive_writer.py:L404-L413'
  - symbol: wrapper
    kind: function
    at: 'scripts/core/directive_writer.py:L405-L412'
  - symbol: cmd_write
    kind: function
    at: 'scripts/core/directive_writer.py:L426-L480'
  - symbol: cmd_append
    kind: function
    at: 'scripts/core/directive_writer.py:L484-L512'
  - symbol: cmd_archive
    kind: function
    at: 'scripts/core/directive_writer.py:L516-L580'
  - symbol: cmd_status
    kind: function
    at: 'scripts/core/directive_writer.py:L584-L618'
  - symbol: cmd_restore
    kind: function
    at: 'scripts/core/directive_writer.py:L622-L658'
  - symbol: cmd_show
    kind: function
    at: 'scripts/core/directive_writer.py:L661-L672'
  - symbol: main
    kind: function
    at: 'scripts/core/directive_writer.py:L675-L733'
  - symbol: _refuse_forbidden
    kind: function
    at: 'scripts/core/directive_writer.py:L714-L720'
  - symbol: fn
    kind: function
    at: 'scripts/core/directive_writer.py:L715-L719'
---
<!-- context:generated:start -->
## Summary

The single locked write path for memories/human-directive.md, enforcing fail-closed rules: in-flight PENDING directives are never clobbered without --allow-pending, the body is immutable after acceptance except a compare-and-swap status transition, and bodies referencing undefined §N sections are rejected. Uses fcntl locking, atomic rename, read-back verification, and chowns files to the memories owner so root-invoked writes don't break the app-uid loop's read access.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
