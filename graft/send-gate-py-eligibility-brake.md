---
name: send-gate.py eligibility brake
slug: send-gate-py-eligibility-brake
type: file
sources:
  - path: scripts/ops/send-gate.py
    hash: 6acd746a20aff7267d711d61350ac14d8fa0c17a1af95341625aa2bfd9a63f92
sources_digest: 5ab131417a8c8279edfc66290905fedf1a1dd1427669fc3449e20dab94f45e26
links:
  - to: g4-attribution-evidence
    relation: uses
    description: >-
      g4_live() re-derives G4 by importing g4-check.py and requires an exact
      firm-name match in the Registry Bridge, with a domain fallback from the
      Outreach row's Website field.
  - to: rfq-send-pipeline
    relation: implements
    description: >-
      Shares the fail-closed eligibility-gate design philosophy with
      rfq-send.py's decide().
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

A fail-closed eligibility brake answering one question — may this firm be emailed right now? — and exiting, never sending itself. Its decide() checks in cheapest-first order: daily/total caps (3/day, 20 total, binding on messages not firms), never-send-twice, opt-out, Status='Qualified', unresolved HOLD markers, email/subject/body presence, a body-leak scan for internal vocabulary, and the Exclusion ground's length/English-marker limits. Caps are derived by parsing 'Sent:' entries from the row's Email log rather than trusting row counts; follow-up mode derives attempts from the log; any check that cannot complete is a REFUSE, never an ALLOW. Dense with incident-driven hardening.

## Related

- uses [[g4-attribution-evidence]] — g4_live() re-derives G4 by importing g4-check.py and requires an exact firm-name match in the Registry Bridge, with a domain fallback from the Outreach row's Website field.
- implements [[rfq-send-pipeline]] — Shares the fail-closed eligibility-gate design philosophy with rfq-send.py's decide().
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
