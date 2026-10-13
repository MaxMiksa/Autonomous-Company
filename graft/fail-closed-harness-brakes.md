---
name: Fail-Closed Harness Brakes
slug: fail-closed-harness-brakes
type: system
sources:
  - path: scripts/ops/rfq-send.py
    hash: 09815061d704b6bd2034469e3bfe3dfac7417f25761ea9ae845be4c5367fd225
  - path: scripts/ops/send-gate.py
    hash: 6acd746a20aff7267d711d61350ac14d8fa0c17a1af95341625aa2bfd9a63f92
  - path: scripts/ops/turn-bloat-brake.py
    hash: c4d72b732830311e89db486abb41c8a13a5760ffa043354c953b99a155ff96fb
  - path: scripts/ops/work-window.py
    hash: 4c83c4f5b2509f134cdc1183e7b0e208e07e67fab50aa1946718daa98e5d68a5
sources_digest: 2502258483206157a247407a7122a411df2f6afd95cfa35862d1b2fef4515c55
links:
  - to: airtable-access-wrappers
    relation: uses
    description: >-
      send-gate and rfq-send read/write Airtable tables and parse Email log
      Sent: entries rather than trusting row counts
  - to: g4-attribution-evidence
    relation: uses
    description: >-
      send-gate re-derives G4 by importing g4-check.py and requires exact
      firm-name match in Registry Bridge
  - to: operator-alerting-watchers
    relation: uses
    description: >-
      Brakes consume state-snapshot DELTA lines and feed streak counters that
      watchers alarm on
  - to: rfq-email-content-templates
    relation: uses
    description: >-
      rfq-send renders subject/body/HTML from rfq_template and enforces
      anonymity via denylist scan
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
  - symbol: _app
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L25-L26'
  - symbol: _streak_len
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L29-L34'
  - symbol: _load
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L37-L41'
  - symbol: _save
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L44-L51'
  - symbol: main
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L63-L104'
  - symbol: _app_dir
    kind: function
    at: 'scripts/ops/work-window.py:L52-L56'
  - symbol: _env_int
    kind: function
    at: 'scripts/ops/work-window.py:L59-L66'
  - symbol: _parse_delta
    kind: function
    at: 'scripts/ops/work-window.py:L69-L78'
  - symbol: _read_state
    kind: function
    at: 'scripts/ops/work-window.py:L81-L88'
  - symbol: _write_state
    kind: function
    at: 'scripts/ops/work-window.py:L91-L95'
  - symbol: _line
    kind: function
    at: 'scripts/ops/work-window.py:L98-L108'
  - symbol: main
    kind: function
    at: 'scripts/ops/work-window.py:L111-L181'
---
<!-- context:generated:start -->
## Summary

Brake scripts that gate or escalate the auto-loop harness: work-window.py blocks empty-cycle confirmations when a tracked surface change orphaned follow-on work (fail-closed on unreadable state, exit 10), turn-bloat-brake.py emits a hard mandate after N consecutive BLOATED cycles, and send-gate.py is the eligibility brake for autonomous outreach. All are fail-closed (any check that cannot complete is a REFUSE/block, never an ALLOW), always exit 0 so they never kill the harness loop, and write state atomically via temp file + os.replace.

## Related

- uses [[airtable-access-wrappers]] — send-gate and rfq-send read/write Airtable tables and parse Email log Sent: entries rather than trusting row counts
- uses [[g4-attribution-evidence]] — send-gate re-derives G4 by importing g4-check.py and requires exact firm-name match in Registry Bridge
- uses [[operator-alerting-watchers]] — Brakes consume state-snapshot DELTA lines and feed streak counters that watchers alarm on
- uses [[rfq-email-content-templates]] — rfq-send renders subject/body/HTML from rfq_template and enforces anonymity via denylist scan
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
