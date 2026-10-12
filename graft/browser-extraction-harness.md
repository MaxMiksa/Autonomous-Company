---
name: Browser Extraction Harness
slug: browser-extraction-harness
type: file
sources:
  - path: scripts/ops/browse-extract.py
    hash: ec67b37ee0a24df3eb9d5b06f16e7172c456153e7c7b8bd61edc2b54f7543aa1
sources_digest: 7514f4be06d24fc6714b50b6a7ae6ea56f424c1b9ce6bc87210364785a9290f3
links:
  - to: ki-k-decision-evidence-pipeline
    relation: uses
    description: >-
      Alternative browser-based path for evidence extraction where direct fetch
      is insufficient
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

Collapses the multi-step MCP browse-and-extract workflow into a single bash invocation, cutting context re-billing from ~5-9 chat turns per page to one. Read-only by design, walks URLs in one background tab via the BrowserOS MCP gateway, runs optional server-side grep over rendered content (so SPAs are searched post-render), and reports a timed-out wait as inconclusive rather than zero matches.

## Related

- uses [[ki-k-decision-evidence-pipeline]] — Alternative browser-based path for evidence extraction where direct fetch is insufficient
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
