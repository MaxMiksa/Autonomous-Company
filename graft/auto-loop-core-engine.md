---
name: auto-loop core engine
slug: auto-loop-core-engine
type: system
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
sources_digest: 5d1a44e9153a8e6e17b6bed2b5ec2c61057b12b9050bab1c1441797cb182daa4
links:
  - to: cycle-metadata-extraction
    relation: implements
    description: >-
      extract_cycle_metadata() must not kill the loop when Codex is routed
      through alternation/fallback (APP-240)
  - to: mcp-config-probe-system
    relation: uses
    description: >-
      auto-loop's JCODE_MCP_CONFIG_REQUIRED preflight list must stay in sync
      with the manifest and generated config, else boot crash-loops
  - to: prompt-transport-contract
    relation: implements
    description: >-
      run_claude_cycle_cli/run_codex_cycle_cli/run_jcode_cycle must honor the
      STDIN/argv transport and size-limit contract
  - to: set-e-lint-invariant
    relation: validates
    description: >-
      auto-loop.sh must never contain a [ test ] && action list as a function's
      last command or before bare return, which kills unguarded callers
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The central orchestration loop in scripts/core/auto-loop.sh: cycle counter persistence, engine routing (claude/jcode/codex), prompt assembly, escalation, tier ladder, idle-skip, discretionary budget, and MCP preflight. Many invariants are pinned by tests: the cycle counter must be monotonic across redeploys (never reset to 1), prompts are transported via STDIN (codex uses '-' sentinel) to avoid E2BIG, prompts ≥126000 bytes are refused with PROMPT-TOO-LARGE, escalation is consumed exactly once and a refusal leaves it ARMED, and the mixed-harness must attribute per-cycle metadata/cost overriding any global LOOP_HARNESS. The script is the primary protected surface guarded by prod-mechanism-guard.

## Related

- implements [[cycle-metadata-extraction]] — extract_cycle_metadata() must not kill the loop when Codex is routed through alternation/fallback (APP-240)
- uses [[mcp-config-probe-system]] — auto-loop's JCODE_MCP_CONFIG_REQUIRED preflight list must stay in sync with the manifest and generated config, else boot crash-loops
- implements [[prompt-transport-contract]] — run_claude_cycle_cli/run_codex_cycle_cli/run_jcode_cycle must honor the STDIN/argv transport and size-limit contract
- validates [[set-e-lint-invariant]] — auto-loop.sh must never contain a [ test ] && action list as a function's last command or before bare return, which kills unguarded callers
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
