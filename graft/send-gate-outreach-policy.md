---
name: send-gate & outreach policy
slug: send-gate-outreach-policy
type: system
sources:
  - path: scripts/ops/rfq-send.py
    hash: 09815061d704b6bd2034469e3bfe3dfac7417f25761ea9ae845be4c5367fd225
  - path: scripts/ops/send-gate.py
    hash: 6acd746a20aff7267d711d61350ac14d8fa0c17a1af95341625aa2bfd9a63f92
  - path: tests/test_rfq_send.sh
    hash: da4d25d4be3529f89c4c62e9b7099278b95d98a4336a9762bfe6c01e31030a97
  - path: tests/test_send_gate.sh
    hash: 4d0f03bd1b3e73a289e87cf0a56b25499b131e48fac01098b3f1d81755cb190d
sources_digest: be8f3d38e79f5823371bc4ab3b80b882b3681ce47ef4cfbf992deba1c65ac068
links:
  - to: g4-address-matching
    relation: uses
    description: >-
      g4_live() requires exact normalized firm-name matching to prevent
      cross-firm collisions.
  - to: prod-mechanism-guard
    relation: depends_on
    description: >-
      rfq-send.py must be registered in prod-mechanism-guard.py and pass
      --check-sync.
generator:
  version: 1
covers:
  - symbol: _load_key
    kind: function
    at: 'scripts/ops/rfq-send.py:L61-L82'
  - symbol: _app_dir
    kind: function
    at: 'scripts/ops/rfq-send.py:L85-L87'
  - symbol: _air
    kind: function
    at: 'scripts/ops/rfq-send.py:L91-L103'
  - symbol: _record
    kind: function
    at: 'scripts/ops/rfq-send.py:L106-L107'
  - symbol: _all_rows
    kind: function
    at: 'scripts/ops/rfq-send.py:L110-L121'
  - symbol: _sponsor_ok
    kind: function
    at: 'scripts/ops/rfq-send.py:L125-L126'
  - symbol: _opted_out
    kind: function
    at: 'scripts/ops/rfq-send.py:L129-L130'
  - symbol: _already_sent
    kind: function
    at: 'scripts/ops/rfq-send.py:L133-L134'
  - symbol: _email_of
    kind: function
    at: 'scripts/ops/rfq-send.py:L137-L139'
  - symbol: _caps_now
    kind: function
    at: 'scripts/ops/rfq-send.py:L142-L152'
  - symbol: render
    kind: function
    at: 'scripts/ops/rfq-send.py:L155-L163'
  - symbol: anonymity_scan
    kind: function
    at: 'scripts/ops/rfq-send.py:L166-L171'
  - symbol: decide
    kind: function
    at: 'scripts/ops/rfq-send.py:L174-L197'
  - symbol: send_fe
    kind: function
    at: 'scripts/ops/rfq-send.py:L201-L226'
  - symbol: _mark_sent
    kind: function
    at: 'scripts/ops/rfq-send.py:L229-L232'
  - symbol: main
    kind: function
    at: 'scripts/ops/rfq-send.py:L236-L278'
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

scripts/ops/send-gate.py is the fail-closed outreach gate enforcing daily/total caps (3/20), duplicate detection, opt-out, non-Qualified status, missing email, G4 failure, TEST-row exclusion by status, unrendered rows, GROUP_ROUTED special case, self-contradictory rows, exclusion-ground length/English-marker checks, procurement-phase mismatch, a body-leak scanner for internal markers, unsplit rows, follow-up mode, exact normalized firm-name matching for g4_live, and Website-field fallback. rfq-send.py is the buyer-side RFQ sender with §15 sponsor approval, ANON_DENY denylist, and no G4 gate usage.

## Related

- uses [[g4-address-matching]] — g4_live() requires exact normalized firm-name matching to prevent cross-firm collisions.
- depends on [[prod-mechanism-guard]] — rfq-send.py must be registered in prod-mechanism-guard.py and pass --check-sync.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
