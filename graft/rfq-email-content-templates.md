---
name: RFQ Email Content Templates
slug: rfq-email-content-templates
type: file
sources:
  - path: scripts/ops/rfq_template.py
    hash: 92801930c70894455bd37f93981ec701390c49b34760c88280fb0ff975bbe5e8
sources_digest: 28f58cfb633179fd82b4d78bf0744720f10699d2bd88924ba7f6fad6b66be2be
links:
  - to: fail-closed-harness-brakes
    relation: produces
    description: >-
      Provides subject()/body()/body_html()/attachments() consumed by
      rfq-send.py
generator:
  version: 1
covers:
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

Content templates for OPEX RFQ emails, separating presentation from send logic. Keeps the client anonymous (only sector and technical scope shared), swaps embedded base64 logo for a cid: reference because Gmail does not render data-URIs in signatures, and leaves all send logic (gates, caps, delivery) to the protected rfq-send.py module.

## Related

- produces [[fail-closed-harness-brakes]] — Provides subject()/body()/body_html()/attachments() consumed by rfq-send.py
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
