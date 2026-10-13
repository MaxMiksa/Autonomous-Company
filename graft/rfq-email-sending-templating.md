---
name: RFQ Email Sending & Templating
slug: rfq-email-sending-templating
type: system
sources:
  - path: scripts/ops/rfq_template.py
    hash: 92801930c70894455bd37f93981ec701390c49b34760c88280fb0ff975bbe5e8
  - path: scripts/ops/rfq-send.py
    hash: 09815061d704b6bd2034469e3bfe3dfac7417f25761ea9ae845be4c5367fd225
sources_digest: cf3477a985d90fc7d5a49be33824fed5f260b7c47dd3c8afac8fc60c3c8b6244
links:
  - to: airtable-access-wrappers
    relation: uses
    description: >-
      rfq-send.py reads/writes the Wowcar OPEX RFQ Airtable table and patches
      status via _mark_sent
  - to: operator-alerting-watchers
    relation: uses
    description: >-
      rfq-reply-watch.py is the advisory half that detects replies/silence to
      sent RFQs; it deliberately omits the delivery-failure branch because
      rfq-send.py only marks successful sends
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
  - symbol: _read_sig
    kind: function
    at: 'scripts/ops/rfq_template.py:L53-L57'
  - symbol: _logo_b64
    kind: function
    at: 'scripts/ops/rfq_template.py:L60-L62'
  - symbol: _html_signature
    kind: function
    at: 'scripts/ops/rfq_template.py:L68-L76'
  - symbol: attachments
    kind: function
    at: 'scripts/ops/rfq_template.py:L82-L87'
  - symbol: subject
    kind: function
    at: 'scripts/ops/rfq_template.py:L98-L99'
  - symbol: body
    kind: function
    at: 'scripts/ops/rfq_template.py:L102-L119'
  - symbol: body_html
    kind: function
    at: 'scripts/ops/rfq_template.py:L122-L142'
---
<!-- context:generated:start -->
## Summary

The two-part OPEX RFQ procurement flow: rfq-send.py is a fail-closed CLI that sends anonymous RFQ emails to vendors via ForwardEmail, gated by an eligibility chain (opt-out, already-sent, caps, anonymity denylist scan, and finally the §15 'Sponsor İzni' checkbox that must be manually TRUE and cannot be set programmatically). rfq_template.py separates presentation from send logic, keeping the client anonymous and swapping a base64 logo for a cid: reference because Gmail does not render data-URIs. Form-only vendors are refused because the machine never fills web forms.

## Related

- uses [[airtable-access-wrappers]] — rfq-send.py reads/writes the Wowcar OPEX RFQ Airtable table and patches status via _mark_sent
- uses [[operator-alerting-watchers]] — rfq-reply-watch.py is the advisory half that detects replies/silence to sent RFQs; it deliberately omits the delivery-failure branch because rfq-send.py only marks successful sends
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
