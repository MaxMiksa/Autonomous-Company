---
name: Compact Ritual Paths
slug: compact-ritual-paths
type: file
sources:
  - path: scripts/compact_yol.py
    hash: 617adabc76e0edaa59787115e1c95e883fa607510c8483a701a97df4539f17da
sources_digest: 05ce3c381678337934f81ea346092efb546335111ae44cc829dcdd403afd016e
links:
  - to: session-brief-hook
    relation: implements
    description: >-
      Provides the path resolution contract that session-brief.py and the
      compact ritual scripts depend on.
generator:
  version: 1
covers:
  - symbol: temizle
    kind: function
    at: 'scripts/compact_yol.py:L57-L60'
  - symbol: _git
    kind: function
    at: 'scripts/compact_yol.py:L63-L69'
  - symbol: repo_adi
    kind: function
    at: 'scripts/compact_yol.py:L72-L89'
  - symbol: yol
    kind: function
    at: 'scripts/compact_yol.py:L92-L95'
  - symbol: main
    kind: function
    at: 'scripts/compact_yol.py:L98-L107'
---
<!-- context:generated:start -->
## Summary

compact_yol.py derives ritual file paths (resume, preflight, marker, history) from repository names to prevent cross-project collisions in shared /tmp paths, handling normal repos, linked worktrees (appending branch suffix), submodules, and non-git directories with graceful fallbacks. COMPACT_* environment variables override defaults, and git timeouts or missing git binaries degrade to directory-name fallbacks without exceptions.

## Related

- implements [[session-brief-hook]] — Provides the path resolution contract that session-brief.py and the compact ritual scripts depend on.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
