---
name: Session Brief Hook
slug: session-brief-hook
type: file
sources:
  - path: scripts/session-brief.py
    hash: f71655446ca0f9824d90922f64f2bbb113d24b5fc01df2dd8ff3fdfa99827dae
sources_digest: e4a8204e6c994f8181835f1150720d4d83fc4a9534bc6b07fffb300d0661d6dd
links:
  - to: compact-ritual
    relation: uses
    description: >-
      Uses compact_yol.yol() for resume path resolution and checks resume
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

A SessionStart hook injecting a measured, real-time session brief (git state, resume freshness, optional .claude/brief-extra.sh lines, fresh preflight items) into agent context. It measures current state instead of asserting claims, skips lines on any error, and deliberately injects only the resume path and freshness — not its content — so the agent knows where to read after compact. The 8-second subprocess timeout enforces that the brief never blocks the session.

## Related

- uses [[compact-ritual]] — Uses compact_yol.yol() for resume path resolution and checks resume age/existence.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
