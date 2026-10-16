---
name: Airtable Access Wrappers
slug: airtable-access-wrappers
type: system
sources:
  - path: tests/test_airtable_read.sh
    hash: f1c8fbb1b495e922c52d041bac7edbae8f100ab57606ebd987179783265325df
  - path: tests/test_airtable_write.sh
    hash: a51c25001935da566cca4a450cfc0906827eb332779f2b454b12d547b7a0e6e0
sources_digest: f36a07c38e3cd5b13c9c5c2ebd4240613fd28de5db52e96debd23170ea040e77
links:
  - to: fail-closed-eligibility-gates
    relation: uses
    description: send-gate uses the air() wrapper for reads.
  - to: operator-alerting-watchers
    relation: uses
    description: Watchers read Airtable tables through these scoping rules.
  - to: rfq-email-pipeline
    relation: uses
    description: rfq-send.py reads/writes the RFQ table through the write guard.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The wrappers that gate Airtable reads and writes to control context cost and validate writes. airtable-read.py refuses unscoped reads (exit 2), caps --all-fields unless --force, caps --max-records at 200 and pageSize at 100, and combines record IDs into OR(RECORD_ID()=...) formulas with --formula via AND. airtable-write.py's guard validates single-record writes before the API: unknown fields refused unless --force, clearing non-empty fields needs --allow-clear, substantial value replacement needs --replace while appends preserving old text are allowed. The air() wrapper carries a URL-quoting fix for table names with spaces.

## Related

- uses [[fail-closed-eligibility-gates]] — send-gate uses the air() wrapper for reads.
- uses [[operator-alerting-watchers]] — Watchers read Airtable tables through these scoping rules.
- uses [[rfq-email-pipeline]] — rfq-send.py reads/writes the RFQ table through the write guard.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
