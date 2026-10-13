---
name: directive writer
slug: directive-writer
type: file
sources:
  - path: tests/test_directive_section_refs.sh
    hash: 413742241d956ae77feb01e20780757ee86fa63f3699e3926a2ddeea81a53a71
  - path: tests/test_directive_writer.py
    hash: 8246a641c797789b53117ec96cd0a3922bad2d9c5dc9ba873e13daf579f35a73
sources_digest: 4309d236e4b6780cc4736a380ce85c1218d19a9f60f140cfb3b9fa156c0bb915
links:
  - to: auto-loop-core-engine
    relation: uses
    description: >-
      The loop reads directive state (PENDING/DONE) to gate escalation and
      work-window behavior
  - to: operator-request-resolution
    relation: produces
    description: >-
      Directive content (Decision/Authorization lines) is what
      operator_request_notify.py parses to resolve requests
generator:
  version: 1
covers:
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

scripts/core/directive_writer.py manages the human-directive.md lifecycle: write/append/status/show/archive subcommands, PENDING gates, undefined §-reference rejection, body_sha256 staleness checks, size brakes (DIRECTIVE_BODY_WARN_BYTES/MAX_BYTES) with --force-size override, backups, and audit logging. undefined_section_refs() guards against the bug that froze directive revision 11 (references to absent §6/§7).

## Related

- uses [[auto-loop-core-engine]] — The loop reads directive state (PENDING/DONE) to gate escalation and work-window behavior
- produces [[operator-request-resolution]] — Directive content (Decision/Authorization lines) is what operator_request_notify.py parses to resolve requests
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
