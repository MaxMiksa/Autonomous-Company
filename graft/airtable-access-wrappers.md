---
name: Airtable Access Wrappers
slug: airtable-access-wrappers
type: system
sources:
  - path: scripts/ops/send-gate.py
    hash: 6acd746a20aff7267d711d61350ac14d8fa0c17a1af95341625aa2bfd9a63f92
  - path: tests/test_airtable_read.sh
    hash: f1c8fbb1b495e922c52d041bac7edbae8f100ab57606ebd987179783265325df
  - path: tests/test_airtable_write.sh
    hash: a51c25001935da566cca4a450cfc0906827eb332779f2b454b12d547b7a0e6e0
sources_digest: 9bec6a8d63e4620cd2d0aa98cdd08b60a5d87fea5a994e227786704c7e5058a8
links:
  - to: fail-closed-harness-brakes
    relation: uses
    description: >-
      send-gate and rfq-send route all Airtable traffic through the air()
      wrapper
  - to: operator-alerting-watchers
    relation: validates
    description: >-
      Watchers' Airtable reads are gated by these wrappers to control context
      cost
generator:
  version: 1
covers:
  - symbol: phase_of
    kind: function
    at: 'scripts/ops/send-gate.py:L66-L91'
  - symbol: body_claims
    kind: function
    at: 'scripts/ops/send-gate.py:L94-L101'
  - symbol: load_key
    kind: function
    at: 'scripts/ops/send-gate.py:L104-L122'
  - symbol: air
    kind: function
    at: 'scripts/ops/send-gate.py:L125-L135'
  - symbol: sent_rows
    kind: function
    at: 'scripts/ops/send-gate.py:L138-L148'
  - symbol: logged_sends
    kind: function
    at: 'scripts/ops/send-gate.py:L154-L177'
  - symbol: counts
    kind: function
    at: 'scripts/ops/send-gate.py:L180-L198'
  - symbol: opted_out
    kind: function
    at: 'scripts/ops/send-gate.py:L201-L215'
  - symbol: body_leak_scan
    kind: function
    at: 'scripts/ops/send-gate.py:L236-L244'
  - symbol: g4_live
    kind: function
    at: 'scripts/ops/send-gate.py:L247-L309'
  - symbol: decide
    kind: function
    at: 'scripts/ops/send-gate.py:L312-L544'
  - symbol: main
    kind: function
    at: 'scripts/ops/send-gate.py:L547-L583'
---
<!-- context:generated:start -->
## Summary

The gated read/write wrappers around the Airtable REST API that control context cost and validate writes. airtable-read.py refuses unscoped reads (exit 2), caps --all-fields and --max-records at 200, and never exceeds Airtable's 100 pageSize ceiling; airtable-write.py's guard refuses unknown fields, clears, and substantial replacements unless explicit flags are passed. The air() wrapper carries a URL-quoting fix for table names with spaces. These are the single choke point through which all Airtable traffic flows.

## Related

- uses [[fail-closed-harness-brakes]] — send-gate and rfq-send route all Airtable traffic through the air() wrapper
- validates [[operator-alerting-watchers]] — Watchers' Airtable reads are gated by these wrappers to control context cost
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
