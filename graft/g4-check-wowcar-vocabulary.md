---
name: g4-check & wowcar vocabulary
slug: g4-check-wowcar-vocabulary
type: system
sources:
  - path: tests/test_g4_check.sh
    hash: 426129aa4d430db932523139037190cd1c5106394e917a10fc73e29b823bc4d2
  - path: tests/test_wowcar_revenue_vocabulary_acceptance.sh
    hash: 2d2ccfe9406d4effbc4872168e5d1f2a48f41842d8ac28397be5a2809dd28083
sources_digest: 1ea1d9ed2cc790d85da7353fb5cba8f815e2ee94e1370ec110c108cc79a29660
links:
  - to: send-gate-rfq-send
    relation: uses
    description: g4_live() in send-gate/rfq-send relies on g4-check's matching logic
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

scripts/ops/g4-check.py is the G4 gate's pure decision logic: address_anchor (register vs website address matching with Turkish İ-ı folding and a coincidence guard), registry_id_anchor (MERSİS/vergi no/ticaret sicil matching with context requirements — 10-digit vergi no accepted bare, 6-digit sicil needs the word 'sicil' nearby), and domains_in (skips authority sources). wowcar-revenue-vocabulary-acceptance.py checks the WowCar revenue vocabulary stays unchanged or contains exactly 14 anchor terms.

## Related

- uses [[send-gate-rfq-send]] — g4_live() in send-gate/rfq-send relies on g4-check's matching logic
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
