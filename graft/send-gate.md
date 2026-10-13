---
name: send gate
slug: send-gate
type: file
sources:
  - path: scripts/ops/send-gate.py
    hash: 6acd746a20aff7267d711d61350ac14d8fa0c17a1af95341625aa2bfd9a63f92
  - path: tests/test_send_gate.sh
    hash: 4d0f03bd1b3e73a289e87cf0a56b25499b131e48fac01098b3f1d81755cb190d
sources_digest: 260cbac1d830524fefee8831ec62d8032fb6948e871229aae8fb6af3055fb10f
links:
  - to: g4-compliance-checks
    relation: uses
    description: Calls g4_live() for firm-name matching; refuses on any G4 failure.
  - to: production-mechanism-guard
    relation: part_of
    description: send-gate.py is a protected production surface.
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

scripts/ops/send-gate.py is the fail-closed outreach refusal gate, tested offline with stubbed air()/g4_live() as pure policy. Guards include daily/total caps (3/20), duplicate outreach, opt-out, non-Qualified status, missing email, G4 failure, TEST rows excluded by STATUS, unrendered rows, GROUP_ROUTED requiring full registered title and karar no, self-contradictory rows, a body-leak scanner for internal markers, unsplit rows, follow-up mode (one authorized second contact), exact normalized firm-name matching for g4_live (rejecting token collisions), and phase-check scoping to first-contact sends only.

## Related

- uses [[g4-compliance-checks]] — Calls g4_live() for firm-name matching; refuses on any G4 failure.
- part of [[production-mechanism-guard]] — send-gate.py is a protected production surface.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
