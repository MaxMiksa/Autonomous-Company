---
name: Fail-Closed Eligibility Gates
slug: fail-closed-eligibility-gates
type: system
sources:
  - path: scripts/ops/rfq-send.py
    hash: 09815061d704b6bd2034469e3bfe3dfac7417f25761ea9ae845be4c5367fd225
  - path: scripts/ops/send-gate.py
    hash: 6acd746a20aff7267d711d61350ac14d8fa0c17a1af95341625aa2bfd9a63f92
sources_digest: 966835db7e2145a9da76e566a9a65a6f00509fa2e98a3c2abde7ddc031c7a3c2
links:
  - to: airtable-access-wrappers
    relation: uses
    description: >-
      Uses the air() wrapper (with URL-quoting fix for table names with spaces)
      and parses Sent: entries from the Email log.
  - to: g4-attribution-evidence
    relation: uses
    description: >-
      send-gate's g4_live() re-derives G4 by importing g4-check.py and requires
      an exact firm-name match in the Registry Bridge, with domain fallback from
      the Outreach row's Website field.
  - to: rfq-email-pipeline
    relation: part_of
    description: rfq-send.py's decide() is the RFQ eligibility gate.
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

The eligibility brakes that answer 'may this firm be emailed right now?' and never send themselves. send-gate.py checks cheapest-first: daily/total caps (3/day, 20 total, binding on messages not firms), never-send-twice, opt-out, Status='Qualified', unresolved HOLD markers, email/subject/body presence, body-leak scan, and Exclusion length/English limits. rfq-send.py's decide() is the RFQ variant adding the §15 Sponsor İzni checkbox. Both are fail-closed: any check that cannot complete is a REFUSE, never an ALLOW, and caps are computed by scanning all rows / parsing Sent: log entries rather than trusting row counts.

## Related

- uses [[airtable-access-wrappers]] — Uses the air() wrapper (with URL-quoting fix for table names with spaces) and parses Sent: entries from the Email log.
- uses [[g4-attribution-evidence]] — send-gate's g4_live() re-derives G4 by importing g4-check.py and requires an exact firm-name match in the Registry Bridge, with domain fallback from the Outreach row's Website field.
- part of [[rfq-email-pipeline]] — rfq-send.py's decide() is the RFQ eligibility gate.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
