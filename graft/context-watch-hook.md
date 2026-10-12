---
name: Context Watch Hook
slug: context-watch-hook
type: file
sources:
  - path: scripts/context-watch.py
    hash: e9aa872c3ee33e6f175760da5b09d5cddda1ffdab5ac78c667547e492910bf96
sources_digest: e120476879431ac8f01406f0c7056c596e84ad05a3bdffa80c27718e3d312c80
links: []
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

Claude Code hook that monitors context-window fullness during a session. Reads the transcript JSONL, sums input/cache_read/cache_creation tokens, auto-escalates the window size through tiers up to 2M if measured usage exceeds the configured window (first live run measured 257% against default), and emits a warning at 50% or a compact-ritual directive at 60% via hookSpecificOutput.additionalContext (must be nested there or silently ignored). State persisted per session in /tmp so each threshold fires once per session; a drop below 40% after compaction re-arms thresholds. Fail-open on any error.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
