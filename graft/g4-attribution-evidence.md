---
name: G4 attribution evidence
slug: g4-attribution-evidence
type: system
sources:
  - path: scripts/ops/site-contact-evidence.py
    hash: 008b4735e6133445eff667f840f9c7faaeef8013b1363f6555b602a9d6fd048c
sources_digest: 5c3ab49bca83c326e54b9e154c81edea67c57863bcee0d19e964759966469ad2
links:
  - to: send-gate-py-eligibility-brake
    relation: produces
    description: >-
      Provides the FOUND_FIRST_PARTY / FOUND_OFF_DOMAIN / INCONCLUSIVE_* /
      NONE_PUBLISHED verdicts that G4 attribution checks consume.
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

Tooling that finds a firm's published contact email for G4 attribution checks, encoding the rule that a fetch returning no rendered content is inconclusive, never negative. site-contact-evidence.py escalates through three sources (browser-rendered DOM via BrowserOS as the decisive default, raw served HTML, and JS bundles) plus policy pages (kvkk, aydinlatma, gizlilik, iletisim) that legally carry contact addresses; it only allows a negative verdict when a rendered DOM was successfully obtained, and skips third-party script URLs to avoid false positives.

## Related

- produces [[send-gate-py-eligibility-brake]] — Provides the FOUND_FIRST_PARTY / FOUND_OFF_DOMAIN / INCONCLUSIVE_* / NONE_PUBLISHED verdicts that G4 attribution checks consume.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
