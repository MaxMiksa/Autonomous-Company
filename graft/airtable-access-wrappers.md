---
name: Airtable access wrappers
slug: airtable-access-wrappers
type: system
sources:
  - path: tests/test_airtable_read.sh
    hash: f1c8fbb1b495e922c52d041bac7edbae8f100ab57606ebd987179783265325df
  - path: tests/test_airtable_write.sh
    hash: a51c25001935da566cca4a450cfc0906827eb332779f2b454b12d547b7a0e6e0
sources_digest: f36a07c38e3cd5b13c9c5c2ebd4240613fd28de5db52e96debd23170ea040e77
links:
  - to: operator-alerting-watchers
    relation: uses
    description: >-
      Watchers read Airtable tables through the scoping/query-shaping rules
      these wrappers enforce.
  - to: send-gate-py-eligibility-brake
    relation: uses
    description: send-gate.py talks to the Airtable API via the air() wrapper.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The gated Airtable read/write wrappers that control context costs and validate writes before they hit the API. airtable-read.py refuses unscoped reads (exit 2), caps --all-fields unless --force, caps --max-records at 200 and pageSize at 100, and turns record IDs into OR(RECORD_ID()=...) formulas combined with --formula via AND. airtable-write.py's guard validates single-record writes offline: unknown fields refused unless --force, clearing a non-empty field requires --allow-clear, substantial value replacement refused unless --replace while appends preserving old text are allowed. The air() wrapper carries a URL-quoting fix for table names with spaces.

## Related

- uses [[operator-alerting-watchers]] — Watchers read Airtable tables through the scoping/query-shaping rules these wrappers enforce.
- uses [[send-gate-py-eligibility-brake]] — send-gate.py talks to the Airtable API via the air() wrapper.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
