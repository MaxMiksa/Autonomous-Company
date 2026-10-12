---
name: outreach send gate
slug: outreach-send-gate
type: system
sources:
  - path: scripts/ops/send-gate.py
    hash: 6acd746a20aff7267d711d61350ac14d8fa0c17a1af95341625aa2bfd9a63f92
  - path: tests/test_send_gate.sh
    hash: 4d0f03bd1b3e73a289e87cf0a56b25499b131e48fac01098b3f1d81755cb190d
sources_digest: 260cbac1d830524fefee8831ec62d8032fb6948e871229aae8fb6af3055fb10f
links:
  - to: g4-compliance-checks
    relation: uses
    description: calls g4_live for firm-name matching
  - to: spending-control-budget-gates
    relation: part_of
    description: send-gate is one of the spending-control mechanisms
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

send-gate.py is a fail-closed refusal policy for outreach sends, tested offline with stubbed air()/g4_live() calls. Guards: daily/total caps (3/20), duplicate outreach, opt-out, non-Qualified status, missing email, G4 failure, TEST rows excluded by STATUS, unrendered rows, GROUP_ROUTED requiring full registered title and karar no, self-contradictory rows, body-leak scanner for internal markers, procurement-phase mismatch, follow-up mode (one authorized second contact), exact normalized firm-name matching for g4_live, and phase-check scoping to first-contact sends. Refuses on any unknown or error.

## Related

- uses [[g4-compliance-checks]] — calls g4_live for firm-name matching
- part of [[spending-control-budget-gates]] — send-gate is one of the spending-control mechanisms
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
