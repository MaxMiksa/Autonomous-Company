---
name: auto-loop core engine
slug: auto-loop-core-engine
type: system
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_cycle_counter.sh
    hash: ab58cfed1b942c55ff2422535c8904c0292904f40786afc3cb7a66774d635065
  - path: tests/test_cycle_metadata.sh
    hash: ed0597fda8cb7dd8c8f45b5dea353e18374e12a7f4b247afab630f455e708c2e
  - path: tests/test_discretionary_budget.sh
    hash: 32b2f12385f1bf8cc0984fc89d1181074406a1726028d2705d2224759cf6de7e
  - path: tests/test_escalation.sh
    hash: 51d700c7d869599d1a6d48913b0097143e7b0c93a520123dd7cf3bb5c8c874fc
  - path: tests/test_idle_skip.sh
    hash: 13ce9f0b8801b94a1bc896bd2db53f2fc68c2984b45db8372050ca760e1edb53
  - path: tests/test_mcp_config_manifest_sync.sh
    hash: 372a198973bc97e73dd00c1acafe2fe458887504be2f5ef9849242d6549c1112
  - path: tests/test_mixed_harness.sh
    hash: bd8a1f81df957e0bfdfacf44982a2274a58809d5f9bd8618c64c3efeecb868cc
  - path: tests/test_prompt_assembly.sh
    hash: 0cd8e397ee0db20d70eac066f7542b6dbabfec6bdd6d031cdc0e378da04876d6
  - path: tests/test_prompt_transport.sh
    hash: c5df34a0acc0d09b63a231df392960370ab146ceea135b5bcace427223300501
  - path: tests/test_seteshape_lint.py
    hash: c75dd121edbe7aed5432f718bdfff952149464b77f9ab22baced3682261ebc98
  - path: tests/test_tier_ladder_daily.sh
    hash: d0bfb4ace48e1fa9665e17059be3f618b46fda0dcf432544a6bb16c07a3ed8db
sources_digest: b70fd453b8a462028d0f7423bebc729570ef2ccaac738d640080c6a475fc4487
links:
  - to: cycle-metadata-prompt-transport-contract
    relation: implements
    description: >-
      extract_cycle_metadata() and prompt transport rules are pinned by
      dedicated regression tests.
  - to: engine-usage-cost-adapter
    relation: uses
    description: >-
      auto-loop calls the cost adapter to price cycles; the model-hint mechanism
      handles watchdog-killed cycles with no done event.
  - to: mcp-config-manifest-sync
    relation: depends_on
    description: >-
      auto-loop's JCODE_MCP_CONFIG_REQUIRED preflight list must stay in sync
      with the manifest or boot crash-loops.
generator:
  version: 1
covers:
  - symbol: _is_fatal_shape
    kind: function
    at: 'tests/test_seteshape_lint.py:L42-L43'
  - symbol: _executable_lines
    kind: function
    at: 'tests/test_seteshape_lint.py:L46-L52'
  - symbol: find_violations
    kind: function
    at: 'tests/test_seteshape_lint.py:L55-L84'
  - symbol: SetEShapeLint
    kind: class
    at: 'tests/test_seteshape_lint.py:L87-L99'
  - symbol: test_no_fatal_test_and_shapes
    kind: method
    at: 'tests/test_seteshape_lint.py:L88-L99'
---
<!-- context:generated:start -->
## Summary

The central orchestration loop (scripts/core/auto-loop.sh) that drives per-cycle engine execution, prompt assembly, cycle metadata extraction, tier selection, escalation, idle-skip, and discretionary budget gating. It is the most safety-critical surface in the repo: a single stray quote or a `[ test ] && action` list as a function's last command can kill the whole loop (APP-240), so its internals are heavily regression-tested by extracting real function bodies via awk/sed rather than reimplementing them. Key invariants: cycle counter must be monotonic across redeploys (persisted + self-healed from cycle-NNNN logs), prompts are transported via STDIN (never argv, to avoid E2BIG), and per-cycle harness/provider variables override any global LOOP_HARNESS.

## Related

- implements [[cycle-metadata-prompt-transport-contract]] — extract_cycle_metadata() and prompt transport rules are pinned by dedicated regression tests.
- uses [[engine-usage-cost-adapter]] — auto-loop calls the cost adapter to price cycles; the model-hint mechanism handles watchdog-killed cycles with no done event.
- depends on [[mcp-config-manifest-sync]] — auto-loop's JCODE_MCP_CONFIG_REQUIRED preflight list must stay in sync with the manifest or boot crash-loops.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
