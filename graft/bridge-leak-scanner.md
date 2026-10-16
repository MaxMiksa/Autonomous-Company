---
name: Bridge Leak Scanner
slug: bridge-leak-scanner
type: concept
sources:
  - path: scripts/core/bridge_leak_scan.py
    hash: e5b7b7ecf614217b79e93037d780bdd0314f4953d8e6308939a49fe5b5b92bcf
sources_digest: b640af07b633d17a562a8a5f854a19c94a33c6169c66e46291f8978bc47e1945
links: []
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

Value-sensitive session-leak scanner (bridge_leak_scan.py) for EKAP Bridge records that flags only key-plus-value adjacencies (Set-Cookie: name=value, Authorization: Bearer <token>, named credential keys with values, populated localStorage dumps) while passing assurance sentences and public evidence fields. Hardened from 2026-07-29: authorization headers are matched only when followed by a known scheme or opaque token of credential length, never by bare prose, to avoid the original word-presence false positive. Includes an embedded selftest with two negative and six positive fixtures that exits 3 on any misbehavior—a canary gate preventing the scanner from being trusted after a regression.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
