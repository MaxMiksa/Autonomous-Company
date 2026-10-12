---
name: spending control & budget gates
slug: spending-control-budget-gates
type: system
sources:
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: scripts/ops/send-gate.py
    hash: 6acd746a20aff7267d711d61350ac14d8fa0c17a1af95341625aa2bfd9a63f92
  - path: tests/test_discretionary_budget.sh
    hash: 32b2f12385f1bf8cc0984fc89d1181074406a1726028d2705d2224759cf6de7e
  - path: tests/test_send_gate.sh
    hash: 4d0f03bd1b3e73a289e87cf0a56b25499b131e48fac01098b3f1d81755cb190d
  - path: tests/test_tier_ladder_daily.sh
    hash: d0bfb4ace48e1fa9665e17059be3f618b46fda0dcf432544a6bb16c07a3ed8db
sources_digest: b9e82a81adbf54f991ef211c60454873bef8ad4217d830cb804702f9adedd22f
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: 'idle detection, discretionary cap, and tier ladder live in auto-loop.sh'
  - to: outreach-send-gate
    relation: implements
    description: send-gate.py enforces the refusal policy for outreach sends
generator:
  version: 1
covers:
  - symbol: phase_of
    kind: function
    at: 'scripts/ops/send-gate.py:L66-L91'
  - symbol: body_claims
    kind: function
    at: 'scripts/ops/send-gate.py:L94-L101'
  - symbol: load_key
    kind: function
    at: 'scripts/ops/send-gate.py:L104-L122'
  - symbol: air
    kind: function
    at: 'scripts/ops/send-gate.py:L125-L135'
  - symbol: sent_rows
    kind: function
    at: 'scripts/ops/send-gate.py:L138-L148'
  - symbol: logged_sends
    kind: function
    at: 'scripts/ops/send-gate.py:L154-L177'
  - symbol: counts
    kind: function
    at: 'scripts/ops/send-gate.py:L180-L198'
  - symbol: opted_out
    kind: function
    at: 'scripts/ops/send-gate.py:L201-L215'
  - symbol: body_leak_scan
    kind: function
    at: 'scripts/ops/send-gate.py:L236-L244'
  - symbol: g4_live
    kind: function
    at: 'scripts/ops/send-gate.py:L247-L309'
  - symbol: decide
    kind: function
    at: 'scripts/ops/send-gate.py:L312-L544'
  - symbol: main
    kind: function
    at: 'scripts/ops/send-gate.py:L547-L583'
---
<!-- context:generated:start -->
## Summary

Spending-control mechanisms across the loop: discretionary daily cap injecting a warning line into the prompt once daily spend reaches a threshold (default $30, ledger discretionary-spend.ndjson), idle detection on snapshot text 'DELTA: none' (fails open), tier ladder selecting engine tier by daily budget (APP-263, per-engine independence), and the send-gate refusal policy for outreach. Idle check fails open (unavailable snapshot = not idle), ledger sum ignores non-JSON lines and missing files, cap comparison uses >= so exact match triggers warning.

## Related

- part of [[auto-loop-core-engine]] — idle detection, discretionary cap, and tier ladder live in auto-loop.sh
- implements [[outreach-send-gate]] — send-gate.py enforces the refusal policy for outreach sends
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
