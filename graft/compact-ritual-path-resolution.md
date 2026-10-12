---
name: Compact ritual path resolution
slug: compact-ritual-path-resolution
type: system
sources:
  - path: scripts/compact_yol.py
    hash: 617adabc76e0edaa59787115e1c95e883fa607510c8483a701a97df4539f17da
  - path: tests/test_compact_anchor_sync.py
    hash: 1f6ccedb49c760b6902820e32ca23f00f80927518fff9288ab1273aca4711378
  - path: tests/test_compact_ritual_hardening.sh
    hash: 2d94865ee02e9d01b5770928d95abef8e3f9157576dc40326fb74e8a164408f9
  - path: tests/test_compact_yol.py
    hash: 707405adc7816737d22c7079fe2e3484cb6959a80f4b4323acb76f44d4074e49
sources_digest: dcb21a2f7db4af9dc62a59154e17ab2e9a7cd7612c72713091b6bccd954121f6
links:
  - to: session-brief-hook
    relation: produces
    description: Provides the resume path and freshness that session-brief.py surfaces.
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

The compact-ritual machinery: compact_yol.py derives ritual file paths (resume, preflight, marker, history) from repository names to prevent cross-project collisions in shared /tmp paths, handling normal repos, linked worktrees (appending branch suffix), submodules, and non-git dirs with graceful fallback. The ritual is hardened by compact-preflight.py treating a resume as stale not only by mtime but also by running compact-resume-lint.py (so a fresh but lint-failing resume is flagged), and compact-postcheck.py computing missing anchors and writing a JSON line to the history log. Core anchor strings ('İLK İŞ', 'KARAR', 'DOĞRULANMAMIŞ', 'BEKLEYEN', 'İZLEYİCİ') must stay identical across four locations, enforced by a dedicated sync test.

## Related

- produces [[session-brief-hook]] — Provides the resume path and freshness that session-brief.py surfaces.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
