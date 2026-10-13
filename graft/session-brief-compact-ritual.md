---
name: Session Brief & Compact Ritual
slug: session-brief-compact-ritual
type: system
sources:
  - path: scripts/session-brief.py
    hash: f71655446ca0f9824d90922f64f2bbb113d24b5fc01df2dd8ff3fdfa99827dae
  - path: tests/test_compact_anchor_sync.py
    hash: 1f6ccedb49c760b6902820e32ca23f00f80927518fff9288ab1273aca4711378
  - path: tests/test_compact_ritual_hardening.sh
    hash: 2d94865ee02e9d01b5770928d95abef8e3f9157576dc40326fb74e8a164408f9
  - path: tests/test_compact_yol.py
    hash: 707405adc7816737d22c7079fe2e3484cb6959a80f4b4323acb76f44d4074e49
sources_digest: 3c62da0ecfdd1d5ea8e18f21665f42588364eb13f72704b2fba22d19992c35a0
links:
  - to: state-snapshot-delta-probing
    relation: uses
    description: >-
      session-brief reads a fresh preflight file to surface open ⚠ items for
      verification
generator:
  version: 1
covers:
  - symbol: sh
    kind: function
    at: 'scripts/session-brief.py:L24-L28'
  - symbol: main
    kind: function
    at: 'scripts/session-brief.py:L31-L78'
  - symbol: _load
    kind: function
    at: 'tests/test_compact_anchor_sync.py:L41-L45'
  - symbol: check
    kind: function
    at: 'tests/test_compact_anchor_sync.py:L48-L53'
  - symbol: test_hepsi_gecti
    kind: function
    at: 'tests/test_compact_anchor_sync.py:L88-L89'
  - symbol: check
    kind: function
    at: 'tests/test_compact_yol.py:L31-L36'
  - symbol: _load
    kind: function
    at: 'tests/test_compact_yol.py:L39-L43'
  - symbol: git
    kind: function
    at: 'tests/test_compact_yol.py:L46-L49'
  - symbol: yeni_repo
    kind: function
    at: 'tests/test_compact_yol.py:L52-L59'
  - symbol: temiz_env
    kind: function
    at: 'tests/test_compact_yol.py:L62-L63'
  - symbol: zaman_asimi
    kind: function
    at: 'tests/test_compact_yol.py:L120-L122'
  - symbol: git_yok
    kind: function
    at: 'tests/test_compact_yol.py:L124-L125'
  - symbol: test_hepsi_gecti
    kind: function
    at: 'tests/test_compact_yol.py:L163-L164'
---
<!-- context:generated:start -->
## Summary

SessionStart hook and compact-ritual machinery that inject a measured real-time brief (git state, resume freshness, optional .claude/brief-extra.sh) without ever blocking the session, and derive ritual file paths from repository names via compact_yol.py to prevent cross-project collisions in shared /tmp paths. The brief measures current state instead of asserting claims, skips lines on any error, and injects only the resume path and freshness, not its content. Anchor strings (İLK İŞ, KARAR, etc.) must stay identical across four locations enforced by a dedicated test.

## Related

- uses [[state-snapshot-delta-probing]] — session-brief reads a fresh preflight file to surface open ⚠ items for verification
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
