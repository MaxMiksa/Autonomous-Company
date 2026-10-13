---
name: auto-loop core loop engine
slug: auto-loop-core-loop-engine
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
  - path: tests/test_mixed_harness.sh
    hash: bd8a1f81df957e0bfdfacf44982a2274a58809d5f9bd8618c64c3efeecb868cc
  - path: tests/test_prompt_assembly.sh
    hash: 0cd8e397ee0db20d70eac066f7542b6dbabfec6bdd6d031cdc0e378da04876d6
  - path: tests/test_prompt_guardrails.sh
    hash: db057850964c46f60538024a1b3e521d4a4ca01d2671a5ee173522bf85bdf6dc
  - path: tests/test_prompt_transport.sh
    hash: c5df34a0acc0d09b63a231df392960370ab146ceea135b5bcace427223300501
  - path: tests/test_seteshape_lint.py
    hash: c75dd121edbe7aed5432f718bdfff952149464b77f9ab22baced3682261ebc98
  - path: tests/test_tier_ladder_daily.sh
    hash: d0bfb4ace48e1fa9665e17059be3f618b46fda0dcf432544a6bb16c07a3ed8db
sources_digest: 61156bc0b6613e1fb593cecf1376f5571e6b0115a1196f39656dc97d58ac6784
links:
  - to: cycle-metadata-extraction
    relation: implements
    description: >-
      extract_cycle_metadata() must not kill the loop when Codex is routed
      through alternation/fallback (APP-240); codex-final-text.py converts JSONL
      event stream to clean summary text.
  - to: escalation-one-shot-logic
    relation: implements
    description: >-
      apply_cycle_escalation() consumes an armed escalation exactly once; a
      refusal leaves it ARMED rather than burning approval.
  - to: prompt-transport-contract
    relation: implements
    description: >-
      run_claude_cycle_cli/run_codex_cycle_cli pass prompts via STDIN (codex
      uses '-' sentinel) to avoid E2BIG; run_jcode_cycle refuses prompts
      >=126000 bytes with PROMPT-TOO-LARGE before spawning.
  - to: set-e-shape-lint
    relation: validates
    description: >-
      test_seteshape_lint.py scans auto-loop.sh for the fatal '[ test ] &&
      action' pattern that propagates exit 1 and kills unguarded callers (root
      cause of APP-240).
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

The central orchestration script (scripts/core/auto-loop.sh) that drives the agent loop: cycle counter persistence, prompt assembly, engine dispatch (claude/codex/jcode), escalation, tier ladder, idle skip, discretionary budget, and cycle metadata extraction. Many tests extract its function bodies verbatim via awk/sed to drive the shipping code rather than copies, so any change to function boundaries or extraction patterns breaks tests loudly.

## Related

- implements [[cycle-metadata-extraction]] — extract_cycle_metadata() must not kill the loop when Codex is routed through alternation/fallback (APP-240); codex-final-text.py converts JSONL event stream to clean summary text.
- implements [[escalation-one-shot-logic]] — apply_cycle_escalation() consumes an armed escalation exactly once; a refusal leaves it ARMED rather than burning approval.
- implements [[prompt-transport-contract]] — run_claude_cycle_cli/run_codex_cycle_cli pass prompts via STDIN (codex uses '-' sentinel) to avoid E2BIG; run_jcode_cycle refuses prompts >=126000 bytes with PROMPT-TOO-LARGE before spawning.
- validates [[set-e-shape-lint]] — test_seteshape_lint.py scans auto-loop.sh for the fatal '[ test ] && action' pattern that propagates exit 1 and kills unguarded callers (root cause of APP-240).
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
