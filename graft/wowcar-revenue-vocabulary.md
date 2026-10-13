---
name: WowCar revenue vocabulary
slug: wowcar-revenue-vocabulary
type: system
sources:
  - path: scripts/ops/wowcar-revenue-vocabulary-acceptance.py
    hash: bc164912338c15636cc9183c9327a6f77fdab6aebc86e2747f197f01f824fab2
  - path: tests/test_wowcar_revenue_vocabulary_acceptance.sh
    hash: 2d2ccfe9406d4effbc4872168e5d1f2a48f41842d8ac28397be5a2809dd28083
sources_digest: 4eb70e546cbb6fb7a1344012fe2a8672d9debb3e0ce1f627feeb641de13670bb
links:
  - to: outreach-and-send-gating
    relation: uses
    description: >-
      The revenue vocabulary anchors firm-name matching used by send-gate and
      g4-check.
generator:
  version: 1
covers:
  - symbol: AcceptanceFailure
    kind: class
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L383-L384'
  - symbol: ConfigurationFailure
    kind: class
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L387-L388'
  - symbol: sha256_bytes
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L391-L392'
  - symbol: canonical_digest
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L395-L397'
  - symbol: require
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L400-L402'
  - symbol: config_require
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L405-L407'
  - symbol: find_repo
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L410-L413'
  - symbol: verify_runtime
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L416-L425'
  - symbol: baseline_records
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L428-L444'
  - symbol: verify_baseline
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L447-L450'
  - symbol: tree_manifest
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L453-L472'
  - symbol: inventory
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L475-L488'
  - symbol: apply_candidate_edits
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L491-L499'
  - symbol: check_source_boundary
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L502-L531'
  - symbol: run
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L534-L540'
  - symbol: require_success
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L543-L544'
  - symbol: numeric_probe
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L547-L551'
  - symbol: numeric_leaf_count
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L554-L560'
  - symbol: scrub_command
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L563-L564'
  - symbol: build_chain
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L567-L585'
  - symbol: scalar
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L588-L603'
  - symbol: workbook_structure
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L606-L634'
  - symbol: cached_cells
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L637-L655'
  - symbol: normalize_f4_pair
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L658-L669'
  - symbol: locate
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L659-L664'
  - symbol: compare_workbooks
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L672-L683'
  - symbol: normalize_stdout
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L686-L708'
  - symbol: compare_stdout
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L711-L730'
  - symbol: parse_args
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L733-L738'
  - symbol: control_identity
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L741-L758'
  - symbol: main
    kind: function
    at: 'scripts/ops/wowcar-revenue-vocabulary-acceptance.py:L761-L911'
---
<!-- context:generated:start -->
## Summary

The WowCar revenue vocabulary acceptance logic (scripts/ops/wowcar-revenue-vocabulary-acceptance.py) checks that the candidate vocabulary in projects/wowcar/generator-source/kod either remains unchanged or contains exactly 14 anchor terms, with a thin bash harness standardizing invocation and requiring an absolute report path. The 14-anchor mode is a hard acceptance gate.

## Related

- uses [[outreach-and-send-gating]] — The revenue vocabulary anchors firm-name matching used by send-gate and g4-check.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
