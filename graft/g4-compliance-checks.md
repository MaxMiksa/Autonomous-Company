---
name: G4 compliance checks
slug: g4-compliance-checks
type: system
sources:
  - path: scripts/ops/g4-check.py
    hash: 719fa86c0e307ef71bf0bce8f49e2baab2bb522aec732b784b39c8f2d788aba8
  - path: tests/test_g4_check.sh
    hash: 426129aa4d430db932523139037190cd1c5106394e917a10fc73e29b823bc4d2
sources_digest: 542228c29abd6900d4324bc37cd02aeb0e7333c24f02e4c7a73a5a887d54d8a6
links:
  - to: send-gate
    relation: implements
    description: >-
      g4_live() is the live network call the send gate stubs; g4-check.py is its
      offline decision logic.
generator:
  version: 1
covers:
  - symbol: load_key
    kind: function
    at: 'scripts/ops/g4-check.py:L71-L89'
  - symbol: norm
    kind: function
    at: 'scripts/ops/g4-check.py:L92-L100'
  - symbol: address_anchor
    kind: function
    at: 'scripts/ops/g4-check.py:L103-L132'
  - symbol: registry_id_anchor
    kind: function
    at: 'scripts/ops/g4-check.py:L135-L164'
  - symbol: field
    kind: function
    at: 'scripts/ops/g4-check.py:L167-L169'
  - symbol: domains_in
    kind: function
    at: 'scripts/ops/g4-check.py:L172-L180'
  - symbol: air_get
    kind: function
    at: 'scripts/ops/g4-check.py:L183-L187'
  - symbol: air_list
    kind: function
    at: 'scripts/ops/g4-check.py:L190-L195'
  - symbol: site_evidence
    kind: function
    at: 'scripts/ops/g4-check.py:L198-L217'
  - symbol: judge
    kind: function
    at: 'scripts/ops/g4-check.py:L220-L287'
  - symbol: main
    kind: function
    at: 'scripts/ops/g4-check.py:L290-L337'
---
<!-- context:generated:start -->
## Summary

scripts/ops/g4-check.py implements the G4 gate decision logic: address_anchor (register vs website address matching with Turkish dotted/dotless İ-ı folding), registry_id_anchor (MERSİS, vergi no, ticaret sicil matching — a 10-digit vergi no is accepted bare while a 6-digit sicil requires the word 'sicil' nearby), and domains_in (skips authority sources like kik.gov.tr). Encodes real production failures: RAYELSİS (spelled-out address), ARKENOM (mahalle+cadde without door number must still anchor), MAGİM (ilçe+il alone must not), and a coincidence guard rejecting a different address on the same street pattern.

## Related

- implements [[send-gate]] — g4_live() is the live network call the send gate stubs; g4-check.py is its offline decision logic.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
