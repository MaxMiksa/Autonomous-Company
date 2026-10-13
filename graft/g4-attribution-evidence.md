---
name: G4 Attribution Evidence
slug: g4-attribution-evidence
type: system
sources:
  - path: scripts/ops/site-contact-evidence.py
    hash: 008b4735e6133445eff667f840f9c7faaeef8013b1363f6555b602a9d6fd048c
sources_digest: 5c3ab49bca83c326e54b9e154c81edea67c57863bcee0d19e964759966469ad2
links:
  - to: outreach-eligibility-gate
    relation: produces
    description: >-
      Produces the FOUND_FIRST_PARTY / FOUND_OFF_DOMAIN / INCONCLUSIVE_* /
      NONE_PUBLISHED verdicts that feed G4 attribution checks in send-gate.
generator:
  version: 1
covers:
  - symbol: fetch
    kind: function
    at: 'scripts/ops/site-contact-evidence.py:L56-L64'
  - symbol: emails
    kind: function
    at: 'scripts/ops/site-contact-evidence.py:L67-L68'
  - symbol: looks_unrendered
    kind: function
    at: 'scripts/ops/site-contact-evidence.py:L71-L81'
  - symbol: render_dom
    kind: function
    at: 'scripts/ops/site-contact-evidence.py:L84-L110'
  - symbol: examine
    kind: function
    at: 'scripts/ops/site-contact-evidence.py:L113-L172'
  - symbol: main
    kind: function
    at: 'scripts/ops/site-contact-evidence.py:L175-L196'
---
<!-- context:generated:start -->
## Summary

Tooling that finds a firm's published contact email for G4 attribution checks, encoding the rule that a fetch returning no rendered content is inconclusive, never negative. It escalates through browser-rendered DOM (via BrowserOS), raw served HTML, and JS bundles, plus probes policy pages (kvkk, aydinlatma, gizlilik, iletisim) that legally carry contact addresses. Third-party script URLs are skipped to avoid false positives, and a negative verdict is only allowed when a rendered DOM was successfully obtained.

## Related

- produces [[outreach-eligibility-gate]] — Produces the FOUND_FIRST_PARTY / FOUND_OFF_DOMAIN / INCONCLUSIVE_* / NONE_PUBLISHED verdicts that feed G4 attribution checks in send-gate.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
