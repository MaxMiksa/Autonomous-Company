---
name: directive writer & section refs
slug: directive-writer-section-refs
type: system
sources:
  - path: tests/test_directive_section_refs.sh
    hash: 413742241d956ae77feb01e20780757ee86fa63f3699e3926a2ddeea81a53a71
  - path: tests/test_directive_writer.py
    hash: 8246a641c797789b53117ec96cd0a3922bad2d9c5dc9ba873e13daf579f35a73
sources_digest: 4309d236e4b6780cc4736a380ce85c1218d19a9f60f140cfb3b9fa156c0bb915
links:
  - to: dashboard-server
    relation: uses
    description: dashboard/server.py writes directives via directive_writer.py subprocess
  - to: operator-request-resolution
    relation: uses
    description: >-
      Directive content (Decision/Authorization lines) is consumed by
      operator_request_notify.py for resolution
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

scripts/core/directive_writer.py manages the human-directive.md lifecycle: write/append/status/show/archive subcommands with a PENDING gate, body_sha256 staleness checks, undefined §-reference rejection, size brakes (DIRECTIVE_BODY_WARN_BYTES/MAX_BYTES with --force-size override), and archive with resolver-section guard and prefix-matching. undefined_section_refs() guards against the bug that froze directive revision 11 (references to absent §6/§7). Append refuses non-heading sections (rc 3); the PENDING gate blocks append/archive without --allow-pending (rc 2).

## Related

- uses [[dashboard-server]] — dashboard/server.py writes directives via directive_writer.py subprocess
- uses [[operator-request-resolution]] — Directive content (Decision/Authorization lines) is consumed by operator_request_notify.py for resolution
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
