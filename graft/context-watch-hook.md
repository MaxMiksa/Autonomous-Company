---
name: Context Watch Hook
slug: context-watch-hook
type: concept
sources:
  - path: scripts/context-watch.py
    hash: e9aa872c3ee33e6f175760da5b09d5cddda1ffdab5ac78c667547e492910bf96
sources_digest: e120476879431ac8f01406f0c7056c596e84ad05a3bdffa80c27718e3d312c80
links:
  - to: compact-ritual-tooling
    relation: produces
    description: Emits the compact-ritual directive that triggers the compact hooks.
generator:
  version: 1
covers:
  - symbol: kullanim
    kind: function
    at: 'scripts/context-watch.py:L33-L50'
  - symbol: main
    kind: function
    at: 'scripts/context-watch.py:L53-L102'
---
<!-- context:generated:start -->
## Summary

Claude Code hook (context-watch.py) that monitors context-window fullness during an agent session by parsing the session transcript's usage field from the last assistant message. Computes percentage against a window size (default 200k, auto-escalating through tiers up to 2M if measured usage exceeds the configured window), emits a warning at 50% or a compact-ritual directive at 60% via hookSpecificOutput.additionalContext. State is persisted per session in /tmp/context-watch-<sid>.json so each threshold fires only once per session, and a drop below 40% after compaction re-arms thresholds. Notable gotcha: the additional context must be nested inside hookSpecificOutput or it is silently ignored.

## Related

- produces [[compact-ritual-tooling]] — Emits the compact-ritual directive that triggers the compact hooks.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
