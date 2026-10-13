---
name: Compact Ritual Tooling
slug: compact-ritual-tooling
type: system
sources:
  - path: scripts/compact_yol.py
    hash: 617adabc76e0edaa59787115e1c95e883fa607510c8483a701a97df4539f17da
  - path: scripts/compact-postcheck.py
    hash: 9584b13bce7ed4eba756912e4a2fbd65beaa2f46bf8cb0238b29d77574ca258f
  - path: scripts/compact-preflight.py
    hash: 879a08b82fae1518773088e60a44ea3e7e941736c9e7e46593201797bf951797
  - path: scripts/compact-report.py
    hash: acbd35a8779fa472cd8164183bcc13c79e716e9e05a51473b0cd2e1b5e2375d1
  - path: scripts/compact-resume-lint.py
    hash: 721ece8bebbdbef80a1b67bb8573a3083b213175e0bda2277a9c46b976c300e1
sources_digest: 6e11740780dc883b8f9529d0b785c680a65f78067736607b6fb743ec07d0f06f
links:
  - to: context-watch-hook
    relation: uses
    description: >-
      context-watch.py emits the compact-ritual directive at 60% context usage,
      triggering these hooks.
generator:
  version: 1
covers:
  - symbol: main
    kind: function
    at: 'scripts/compact-postcheck.py:L39-L79'
  - symbol: sh
    kind: function
    at: 'scripts/compact-preflight.py:L52-L56'
  - symbol: hook_payload
    kind: function
    at: 'scripts/compact-preflight.py:L59-L68'
  - symbol: resume_lint_gecer_mi
    kind: function
    at: 'scripts/compact-preflight.py:L71-L87'
  - symbol: resume_durumu
    kind: function
    at: 'scripts/compact-preflight.py:L90-L100'
  - symbol: repo_report
    kind: function
    at: 'scripts/compact-preflight.py:L103-L120'
  - symbol: main
    kind: function
    at: 'scripts/compact-preflight.py:L123-L193'
  - symbol: sh
    kind: function
    at: 'scripts/compact-report.py:L30-L35'
  - symbol: sh_input
    kind: function
    at: 'scripts/compact-report.py:L38-L43'
  - symbol: repo_root
    kind: function
    at: 'scripts/compact-report.py:L46-L48'
  - symbol: line_repo
    kind: function
    at: 'scripts/compact-report.py:L51-L59'
  - symbol: block_prod
    kind: function
    at: 'scripts/compact-report.py:L62-L71'
  - symbol: block_loop
    kind: function
    at: 'scripts/compact-report.py:L74-L145'
  - symbol: grab
    kind: function
    at: 'scripts/compact-report.py:L101-L103'
  - symbol: block_discretionary
    kind: function
    at: 'scripts/compact-report.py:L148-L199'
  - symbol: g
    kind: function
    at: 'scripts/compact-report.py:L186-L188'
  - symbol: main
    kind: function
    at: 'scripts/compact-report.py:L202-L212'
  - symbol: main
    kind: function
    at: 'scripts/compact-resume-lint.py:L45-L77'
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

A suite of Claude Code hooks and scripts that mechanize the 'compact' ritual — the controlled context-window reset. compact_yol.py derives repo-specific temp paths (replacing shared /tmp paths that caused cross-project collisions), compact-preflight.py scans git repos for uncommitted/unpushed/stash risk and validates resume freshness (auto-block is one-shot with a 30-min TTL marker), compact-resume-lint.py enforces the 'foreign-reader test' by rejecting stale numeric measurements and requiring mandatory template sections, compact-postcheck.py audits whether the compact_summary carried the five critical anchors, and compact-report.py prints an operational digest (repo↔prod sync, OPREQ, directives, holds, loop health via SSH to the powerupp-ts host). All are fail-open and never block compact except the deliberate one-shot preflight auto-block.

## Related

- uses [[context-watch-hook]] — context-watch.py emits the compact-ritual directive at 60% context usage, triggering these hooks.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
