---
name: Site Contact Evidence
slug: site-contact-evidence
type: concept
sources:
  - path: scripts/ops/g4-check.py
    hash: 719fa86c0e307ef71bf0bce8f49e2baab2bb522aec732b784b39c8f2d788aba8
sources_digest: e47298fddc2eacfb0ba6a82f12150cbd0deb55432756d5004128f2796ba6b41f
links:
  - to: g4-identity-verification
    relation: implements
    description: g4-check imports site-contact-evidence.py to fetch firm pages
generator:
  version: 1
covers:
  - symbol: load_key
    kind: function
    at: 'scripts/ops/g4-check.py:L71-L89'
  - symbol: norm
    kind: function
    at: 'scripts/ops/g4-check.py:L92-L100'
  - symbol: address_anchor
    kind: function
    at: 'scripts/ops/g4-check.py:L103-L132'
  - symbol: registry_id_anchor
    kind: function
    at: 'scripts/ops/g4-check.py:L135-L164'
  - symbol: field
    kind: function
    at: 'scripts/ops/g4-check.py:L167-L169'
  - symbol: domains_in
    kind: function
    at: 'scripts/ops/g4-check.py:L172-L180'
  - symbol: air_get
    kind: function
    at: 'scripts/ops/g4-check.py:L183-L187'
  - symbol: air_list
    kind: function
    at: 'scripts/ops/g4-check.py:L190-L195'
  - symbol: site_evidence
    kind: function
    at: 'scripts/ops/g4-check.py:L198-L217'
  - symbol: judge
    kind: function
    at: 'scripts/ops/g4-check.py:L220-L287'
  - symbol: main
    kind: function
    at: 'scripts/ops/g4-check.py:L290-L337'
---
<!-- context:generated:start -->
## Summary

The render-first examiner approach for fetching a firm's site and contact pages, reused by g4-check via dynamic import. The concept is that evidence must be fetched and rendered before judging, and authority domains are excluded from candidate site extraction.

## Related

- implements [[g4-identity-verification]] — g4-check imports site-contact-evidence.py to fetch firm pages
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
