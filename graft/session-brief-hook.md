---
name: Session Brief Hook
slug: session-brief-hook
type: file
sources:
  - path: scripts/session-brief.py
    hash: f71655446ca0f9824d90922f64f2bbb113d24b5fc01df2dd8ff3fdfa99827dae
sources_digest: e4a8204e6c994f8181835f1150720d4d83fc4a9534bc6b07fffb300d0661d6dd
links:
  - to: compact-ritual-paths
    relation: uses
    description: >-
      Uses compact_yol.yol() to resolve the resume file path and check its
      age/existence.
generator:
  version: 1
covers:
  - symbol: sh
    kind: function
    at: 'scripts/session-brief.py:L24-L28'
  - symbol: main
    kind: function
    at: 'scripts/session-brief.py:L31-L78'
---
<!-- context:generated:start -->
## Summary

session-brief.py is a SessionStart hook that injects a measured, real-time session brief into the agent's context at startup/resume/compact events. It measures current state (git branch, sync status, dirty files, stash) instead of asserting claims, enforces an 8-second timeout so the brief never blocks the session, and deliberately does not inject resume content — only its path and freshness — so the agent knows where to read after compact. It reads a fresh preflight file (under 120 minutes old) to surface open ⚠ items for verification rather than blind adoption.

## Related

- uses [[compact-ritual-paths]] — Uses compact_yol.yol() to resolve the resume file path and check its age/existence.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
