---
name: Browser Automation
slug: browser-automation
type: system
sources:
  - path: scripts/ops/browse-extract.py
    hash: ec67b37ee0a24df3eb9d5b06f16e7172c456153e7c7b8bd61edc2b54f7543aa1
  - path: scripts/ops/site-contact-evidence.py
    hash: 008b4735e6133445eff667f840f9c7faaeef8013b1363f6555b602a9d6fd048c
  - path: tests/test_browse_extract.sh
    hash: 37b269657d3077acf85e81540cd0355f9e97b432f0e6e1d973c2dfc170a887a6
sources_digest: 5bb7ecdb5b83f4d16c7b5105f091f3150300778fa533c5f8ff59aa3751296fa9
links:
  - to: g4-attribution-evidence
    relation: part_of
    description: >-
      site-contact-evidence.py uses browser rendering for DOM-based contact
      extraction.
generator:
  version: 1
covers:
  - symbol: Gateway
    kind: class
    at: 'scripts/ops/browse-extract.py:L45-L83'
  - symbol: __init__
    kind: method
    at: 'scripts/ops/browse-extract.py:L46-L49'
  - symbol: post
    kind: method
    at: 'scripts/ops/browse-extract.py:L51-L67'
  - symbol: call
    kind: method
    at: 'scripts/ops/browse-extract.py:L69-L77'
  - symbol: handshake
    kind: method
    at: 'scripts/ops/browse-extract.py:L79-L83'
  - symbol: clip
    kind: function
    at: 'scripts/ops/browse-extract.py:L86-L91'
  - symbol: extract
    kind: function
    at: 'scripts/ops/browse-extract.py:L94-L119'
  - symbol: ToolError
    kind: class
    at: 'scripts/ops/browse-extract.py:L122-L123'
  - symbol: main
    kind: function
    at: 'scripts/ops/browse-extract.py:L126-L201'
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

Browser-driven tooling: browse-extract.py drives an MCP browser gateway to grep/read page content with a hard invariant that the tab is always closed even on error paths, and site-contact-evidence.py's render_dom drives BrowserOS via ekap-run.py. The fake-gateway test suite asserts the tab-close invariant across usage rejection, tool errors, and unreachable gateways with distinct exit codes.

## Related

- part of [[g4-attribution-evidence]] — site-contact-evidence.py uses browser rendering for DOM-based contact extraction.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
