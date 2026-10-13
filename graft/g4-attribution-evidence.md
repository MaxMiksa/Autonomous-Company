---
name: G4 Attribution Evidence
slug: g4-attribution-evidence
type: concept
sources:
  - path: scripts/ops/send-gate.py
    hash: 6acd746a20aff7267d711d61350ac14d8fa0c17a1af95341625aa2bfd9a63f92
  - path: scripts/ops/site-contact-evidence.py
    hash: 008b4735e6133445eff667f840f9c7faaeef8013b1363f6555b602a9d6fd048c
sources_digest: 83bbebb16355316c1b2fa6ca43df1b89f78e0c91d74840bba712ca314bcb692a
links:
  - to: fail-closed-harness-brakes
    relation: implements
    description: >-
      G4 live-check in send-gate depends on this evidence rule; inconclusive
      evidence must refuse, never allow
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

The cross-cutting rule that a firm's published contact email must be found before G4 attribution can be confirmed, and that a fetch returning no rendered content is inconclusive, never negative. site-contact-evidence.py escalates through browser-rendered DOM (decisive), raw HTML, and JS bundles, probing policy pages that legally carry contact addresses, and only allows a negative verdict when a rendered DOM was obtained. send-gate re-derives G4 by exact firm-name match in the Registry Bridge with a domain fallback from the Outreach row's Website field.

## Related

- implements [[fail-closed-harness-brakes]] — G4 live-check in send-gate depends on this evidence rule; inconclusive evidence must refuse, never allow
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
