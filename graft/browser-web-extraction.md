---
name: Browser & web extraction
slug: browser-web-extraction
type: system
sources:
  - path: scripts/ops/browse-extract.py
    hash: ec67b37ee0a24df3eb9d5b06f16e7172c456153e7c7b8bd61edc2b54f7543aa1
sources_digest: 7514f4be06d24fc6714b50b6a7ae6ea56f424c1b9ce6bc87210364785a9290f3
links: []
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
---
<!-- context:generated:start -->
## Summary

Collapses multi-step MCP browse-and-extract workflows into single invocations to cut context re-billing: browse-extract walks URLs in one background tab via the BrowserOS MCP gateway with server-side grep over rendered content (so SPAs are searched post-render), and is read-only by design. Airtable reads similarly refuse unscoped pulls. Both report truncation and treat timed-out waits as inconclusive rather than zero matches.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
