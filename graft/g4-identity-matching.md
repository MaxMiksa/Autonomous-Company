---
name: g4 identity matching
slug: g4-identity-matching
type: concept
sources:
  - path: tests/test_g4_check.sh
    hash: 426129aa4d430db932523139037190cd1c5106394e917a10fc73e29b823bc4d2
sources_digest: 3479b42197aed3dc935842f570f92dbe979db1741a919d19c8c4fce117d8490d
links:
  - to: outreach-send-gating
    relation: part_of
    description: g4-check.py is part of the outreach stack
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

g4-check.py's pure decision logic for company identity anchoring: address_anchor (register vs website address), registry_id_anchor (MERSİS, vergi no, ticaret sicil), and domains_in (skips authority sources like kik.gov.tr). Encodes real production failures: Turkish dotted/dotless İ-ı folding must not break matches, a different address on the same street pattern must be rejected (coincidence guard), and shorter numbers need more context — a 10-digit vergi no is accepted bare while a 6-digit sicil requires the word 'sicil' nearby. Mahalle+cadde without a door number can still anchor; ilçe+il alone must not.

## Related

- part of [[outreach-send-gating]] — g4-check.py is part of the outreach stack
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
