---
name: Airtable Read/Write Wrappers
slug: airtable-read-write-wrappers
type: concept
sources:
  - path: tests/test_airtable_read.sh
    hash: f1c8fbb1b495e922c52d041bac7edbae8f100ab57606ebd987179783265325df
  - path: tests/test_airtable_write.sh
    hash: a51c25001935da566cca4a450cfc0906827eb332779f2b454b12d547b7a0e6e0
sources_digest: f36a07c38e3cd5b13c9c5c2ebd4240613fd28de5db52e96debd23170ea040e77
links:
  - to: operator-alerting-watchers
    relation: implements
    description: >-
      The scoping/query-shaping contract these watchers rely on for context-cost
      control
  - to: outreach-eligibility-gate
    relation: implements
    description: The air() wrapper with URL-quoting fix is used by send-gate.py
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The scoping and guard wrappers that gate Airtable access to control context costs and validate writes. airtable-read.py refuses unscoped reads (exit 2), caps --all-fields unless --force, caps --max-records at 200, never exceeds pageSize 100, and combines record IDs into OR(RECORD_ID()=...) formulas joined with --formula via AND. airtable-write.py's guard validates single-record writes offline: unknown fields refused unless --force, clearing non-empty fields needs --allow-clear, substantial value replacement needs --replace while appends preserving old text are allowed. The air() wrapper carries a URL-quoting fix for table names with spaces.

## Related

- implements [[operator-alerting-watchers]] — The scoping/query-shaping contract these watchers rely on for context-cost control
- implements [[outreach-eligibility-gate]] — The air() wrapper with URL-quoting fix is used by send-gate.py
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
