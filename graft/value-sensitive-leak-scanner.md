---
name: Value-Sensitive Leak Scanner
slug: value-sensitive-leak-scanner
type: concept
sources:
  - path: scripts/core/bridge_leak_scan.py
    hash: e5b7b7ecf614217b79e93037d780bdd0314f4953d8e6308939a49fe5b5b92bcf
sources_digest: b640af07b633d17a562a8a5f854a19c94a33c6169c66e46291f8978bc47e1945
links:
  - to: registry-merge-promotion-gates
    relation: implements
    description: >-
      Mirrors the same trust-gating pattern as directive-rule-sweep and the
      fail-closed merge/promotion gates.
generator:
  version: 1
covers:
  - symbol: scan
    kind: function
    at: 'scripts/core/bridge_leak_scan.py:L63-L69'
  - symbol: selftest
    kind: function
    at: 'scripts/core/bridge_leak_scan.py:L98-L111'
  - symbol: main
    kind: function
    at: 'scripts/core/bridge_leak_scan.py:L114-L127'
---
<!-- context:generated:start -->
## Summary

A trust-gating pattern shared across the codebase: scanners that flag only key-plus-value adjacencies (Set-Cookie: name=value, Authorization: Bearer <token>, named credential keys, populated localStorage dumps) while passing assurance sentences and public evidence fields. bridge_leak_scan.py encodes this with five compiled regex rules, a selftest() that runs negative and positive fixtures and exits 3 if any misbehave (a canary gate preventing the scanner from being trusted after a regression), and a deliberate hardening from 2026-07-29: authorization headers are matched only when followed by a known scheme or opaque token of credential length, never by bare prose, to avoid recreating the original word-presence false positive. The scanner refuses to report CLEAN if any fixture fails.

## Related

- implements [[registry-merge-promotion-gates]] — Mirrors the same trust-gating pattern as directive-rule-sweep and the fail-closed merge/promotion gates.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
