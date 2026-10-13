---
name: Wowcar Source Modules
slug: wowcar-source-modules
type: system
sources:
  - path: scripts/ops/staleness-report.py
    hash: 3076f30a8be1b80c196dec59ede54a8a67f314edf5af263f37c234f09dabeb55
  - path: scripts/ops/state-snapshot.py
    hash: 3112f4632b64a6b531b215ea81ba82b2ceb6436942511f816de94ced3171bfe8
  - path: scripts/ops/wowcar-revenue-vocabulary-acceptance.py
    hash: bc164912338c15636cc9183c9327a6f77fdab6aebc86e2747f197f01f824fab2
sources_digest: ab7558a3a658b5361284b7ad75f8ec82ebda0b98802ce88e87ecfb3724943152
links:
  - to: state-staleness-probes
    relation: uses
    description: >-
      state-snapshot.py hashes the sorted per-file SHA-256 set of the Wowcar
      source directory.
  - to: wowcar-revenue-relabel-acceptance
    relation: implements
    description: The modules whose behavior the acceptance harness pins and validates.
generator:
  version: 1
covers:
  - symbol: _bytes
    kind: function
    at: 'scripts/ops/staleness-report.py:L37-L38'
  - symbol: _read
    kind: function
    at: 'scripts/ops/staleness-report.py:L41-L45'
  - symbol: _sections
    kind: function
    at: 'scripts/ops/staleness-report.py:L48-L55'
  - symbol: _heading_date
    kind: function
    at: 'scripts/ops/staleness-report.py:L58-L65'
  - symbol: directive_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L68-L86'
  - symbol: opreq_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L89-L99'
  - symbol: decisions_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L102-L107'
  - symbol: consensus_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L110-L117'
  - symbol: ledger_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L120-L132'
  - symbol: prompt_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L135-L142'
  - symbol: weekly_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L145-L155'
  - symbol: backup_rows
    kind: function
    at: 'scripts/ops/staleness-report.py:L158-L168'
  - symbol: build
    kind: function
    at: 'scripts/ops/staleness-report.py:L171-L179'
  - symbol: main
    kind: function
    at: 'scripts/ops/staleness-report.py:L182-L199'
  - symbol: file_sha16
    kind: function
    at: 'scripts/ops/state-snapshot.py:L54-L61'
  - symbol: directive_state
    kind: function
    at: 'scripts/ops/state-snapshot.py:L64-L72'
  - symbol: opreq_open
    kind: function
    at: 'scripts/ops/state-snapshot.py:L75-L87'
  - symbol: wowcar_sources
    kind: function
    at: 'scripts/ops/state-snapshot.py:L90-L104'
  - symbol: main
    kind: function
    at: 'scripts/ops/state-snapshot.py:L107-L166'
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

The internal Wowcar financial modeling modules (model.py, build_xlsx.py, recalc.py, test.py, capraz.py, tanila.py, kohort.py) that produce the revenue workbook. These are the subject of the vocabulary-relabel acceptance harness and are hashed by state-snapshot's wowcar_sources function.

## Related

- uses [[state-staleness-probes]] — state-snapshot.py hashes the sorted per-file SHA-256 set of the Wowcar source directory.
- implements [[wowcar-revenue-relabel-acceptance]] — The modules whose behavior the acceptance harness pins and validates.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
