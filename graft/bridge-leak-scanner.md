---
name: Bridge Leak Scanner
slug: bridge-leak-scanner
type: file
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

Value-sensitive session-leak scanner for EKAP Bridge records, flagging only key-plus-value adjacencies (Set-Cookie: name=value, Authorization: Bearer <token>, named credential keys assigned values, populated localStorage dumps) while passing assurance sentences and public evidence fields like KararId and content_hash. Five compiled regex rules; selftest() runs two negative and six positive fixtures and exits 3 if any misbehave — a canary gate preventing the scanner from being trusted after a regression. Hardened 2026-07-29: authorization headers matched only when followed by known scheme or opaque token of credential length, never by bare prose like 'authorization: granted'. Refuses to report CLEAN if any fixture fails, mirroring directive-rule-sweep's trust-gating pattern.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
