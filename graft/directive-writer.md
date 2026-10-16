---
name: Directive Writer
slug: directive-writer
type: system
sources:
  - path: scripts/core/directive_writer.py
    hash: 2b00db428f705544c6b980dd3b76f3e35e0dc76ca44eb82a2d023c7d1b9bb45a
  - path: tests/test_directive_section_refs.sh
    hash: 413742241d956ae77feb01e20780757ee86fa63f3699e3926a2ddeea81a53a71
  - path: tests/test_directive_writer.py
    hash: 13417edeb21db6e9888dbf5a38bc6d49f896b9ec4968f7b2c09f0861eb578c4a
sources_digest: 4778a1629546ca7018dac56ecd3a0338daafb547a2b6cd49ca9de11f0ceab9c3
links:
  - to: cockpit-dashboard
    relation: uses
    description: Dashboard's write_directive appends via this module.
  - to: escalation-directive-gating
    relation: implements
    description: >-
      Provides the PENDING state and directive body that escalation and
      staleness checks read.
  - to: operator-request-resolution
    relation: uses
    description: >-
      Legal/financial/adjudication decisions and expenditure authorizations are
      recorded as structured lines in human-directive.md.
  - to: opportunity-analyst
    relation: uses
    description: Used for safe restore of human-directive.md.
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
    at: 'tests/test_directive_writer.py:L63-L174'
---
<!-- context:generated:start -->
## Summary

scripts/core/directive_writer.py manages the human-directive.md lifecycle: write baseline, append (rejecting non-heading sections, PENDING-gate enforcement, undefined § refs, backup creation), status transitions with body-SHA256 staleness checks, show --sections, and archive (resolver-section guards, PENDING gates, summary insertion, verbatim archival with stamps). English protected headings are not split into sections while Turkish ones are; size-brake warnings/refusals via DIRECTIVE_BODY_WARN_BYTES/MAX_BYTES with --force-size override; Resolves: OPREQ-X-001 lines survive archiving.

## Related

- uses [[cockpit-dashboard]] — Dashboard's write_directive appends via this module.
- implements [[escalation-directive-gating]] — Provides the PENDING state and directive body that escalation and staleness checks read.
- uses [[operator-request-resolution]] — Legal/financial/adjudication decisions and expenditure authorizations are recorded as structured lines in human-directive.md.
- uses [[opportunity-analyst]] — Used for safe restore of human-directive.md.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
