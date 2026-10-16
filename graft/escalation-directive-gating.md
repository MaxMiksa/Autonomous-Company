---
name: escalation & directive gating
slug: escalation-directive-gating
type: concept
sources:
  - path: tests/test_directive_section_refs.sh
    hash: 413742241d956ae77feb01e20780757ee86fa63f3699e3926a2ddeea81a53a71
  - path: tests/test_directive_writer.py
    hash: 13417edeb21db6e9888dbf5a38bc6d49f896b9ec4968f7b2c09f0861eb578c4a
  - path: tests/test_escalation.sh
    hash: 51d700c7d869599d1a6d48913b0097143e7b0c93a520123dd7cf3bb5c8c874fc
sources_digest: c80a9cdd02ea8322ece2d08f5b02a9e3bc681fa8138737c30c93312662a128c2
links:
  - to: auto-loop-core-engine
    relation: uses
    description: >-
      apply_cycle_escalation() and _directive_is_pending() are extracted from
      auto-loop.sh and drive the escalation flow.
  - to: directive-writer
    relation: implements
    description: >-
      The directive lifecycle (write/append/status/show/archive) is implemented
      by directive_writer.py with PENDING gates and staleness checks.
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
    at: 'tests/test_directive_writer.py:L63-L174'
---
<!-- context:generated:start -->
## Summary

One-shot operator escalation (APP-238): an armed escalation is consumed exactly once on a PENDING directive with a Claude cycle (model override, effort override, long wall timeout); a refusal leaves it ARMED rather than burning an approval; Codex-routed cycles are refused; unrelated runtime.env keys are preserved after consumption. Directive lifecycle is append-only with PENDING gates, body-SHA256 staleness checks, and undefined-§-reference rejection (the bug that froze revision 11).

## Related

- uses [[auto-loop-core-engine]] — apply_cycle_escalation() and _directive_is_pending() are extracted from auto-loop.sh and drive the escalation flow.
- implements [[directive-writer]] — The directive lifecycle (write/append/status/show/archive) is implemented by directive_writer.py with PENDING gates and staleness checks.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
