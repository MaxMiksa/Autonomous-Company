---
name: Fail-Closed Design Invariant
slug: fail-closed-design-invariant
type: concept
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: scripts/ops/send-gate.py
    hash: 6acd746a20aff7267d711d61350ac14d8fa0c17a1af95341625aa2bfd9a63f92
  - path: scripts/ops/state-snapshot.py
    hash: 3112f4632b64a6b531b215ea81ba82b2ceb6436942511f816de94ced3171bfe8
  - path: scripts/ops/verify-mcp-keys.py
    hash: a35c1f35481876cedc5bb4cf0c7fd4eceaea1c85e57d3c28e87560b3f9f342db
  - path: scripts/ops/work-window.py
    hash: fd9dd4d65c12d2d5aefc8358f830da5764f16799b2d34aa97ea3c7c5a289a096
  - path: scripts/ops/wowcar-revenue-vocabulary-acceptance.py
    hash: bc164912338c15636cc9183c9327a6f77fdab6aebc86e2747f197f01f824fab2
sources_digest: 9c6b411fe60912fe85b0e2e10320c14cf453bbec64aaa27ecde4ac0a57990462
links:
  - to: harness-loop-core
    relation: implements
    description: >-
      Budget gates latch a hold and return NA (not 0) on first-ever ccusage
      failure; degraded reads never overwrite the cache.
  - to: outreach-eligibility-gate
    relation: implements
    description: >-
      send-gate.py's core rule: any check that cannot complete is a REFUSE,
      never an ALLOW.
  - to: work-window-brake
    relation: implements
    description: >-
      Corrupt state yields exit 10 (fail-closed), while unreadable state fails
      open.
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
  - symbol: loop_env
    kind: function
    at: 'scripts/ops/verify-mcp-keys.py:L39-L51'
  - symbol: main
    kind: function
    at: 'scripts/ops/verify-mcp-keys.py:L54-L75'
  - symbol: _app_dir
    kind: function
    at: 'scripts/ops/work-window.py:L59-L63'
  - symbol: _env_int
    kind: function
    at: 'scripts/ops/work-window.py:L66-L73'
  - symbol: _parse_delta
    kind: function
    at: 'scripts/ops/work-window.py:L76-L85'
  - symbol: _read_state
    kind: function
    at: 'scripts/ops/work-window.py:L88-L95'
  - symbol: _write_state
    kind: function
    at: 'scripts/ops/work-window.py:L98-L102'
  - symbol: _line
    kind: function
    at: 'scripts/ops/work-window.py:L105-L115'
  - symbol: main
    kind: function
    at: 'scripts/ops/work-window.py:L118-L191'
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

A cross-cutting invariant across nearly every ops script: any check that cannot complete, any degraded read, any malformed input, or any missing credential must result in a REFUSE/block/fail-closed outcome, never an ALLOW or a silent pass. This appears in send-gate (any check that cannot complete is a REFUSE), budget gates (degraded reads never lower a same-period prior observation), the acceptance harness (AcceptanceFailure/ConfigurationFailure exceptions), the work-window brake (corrupt state yields exit 10), and the MCP key verifier (fails if a key is absent or malformed). The complement is that advisory scripts always exit 0 so a probe failure never kills the calling cycle.

## Related

- implements [[harness-loop-core]] — Budget gates latch a hold and return NA (not 0) on first-ever ccusage failure; degraded reads never overwrite the cache.
- implements [[outreach-eligibility-gate]] — send-gate.py's core rule: any check that cannot complete is a REFUSE, never an ALLOW.
- implements [[work-window-brake]] — Corrupt state yields exit 10 (fail-closed), while unreadable state fails open.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
