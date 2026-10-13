---
name: SnapOG OG Rendering
slug: snapog-og-rendering
type: system
sources:
  - path: projects/_archive/snapog/src/og/render.ts
    hash: c74a09fcf98afae74090c3b72b8b4c7f84252e7f0aca090d1418352cd48d8094
  - path: projects/_archive/snapog/src/og/templates.ts
    hash: bfc8c9e61038224564b61c55c627b2d86d9ba2514dd47f64a717e94f0be8b810
sources_digest: 33ae7a75e47eef85db34a1438baacae47da77dae7fb7876ade82ebe4c7f21f57
links:
  - to: snapog-worker
    relation: part_of
    description: Rendering module used by the main worker entry point.
generator:
  version: 1
covers:
  - symbol: generateOGImage
    kind: function
    at: 'projects/_archive/snapog/src/og/render.ts:L11-L23'
  - symbol: buildCacheKey
    kind: function
    at: 'projects/_archive/snapog/src/og/render.ts:L26-L37'
  - symbol: StyleObject
    kind: type
    at: 'projects/_archive/snapog/src/og/templates.ts:L6-L6'
  - symbol: VNode
    kind: type
    at: 'projects/_archive/snapog/src/og/templates.ts:L8-L15'
  - symbol: AccentBar
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L18-L33'
  - symbol: Header
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L36-L83'
  - symbol: Footer
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L86-L133'
  - symbol: defaultTemplate
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L136-L202'
  - symbol: blogTemplate
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L205-L286'
  - symbol: articleTemplate
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L289-L461'
  - symbol: buildElement
    kind: function
    at: 'projects/_archive/snapog/src/og/templates.ts:L463-L472'
---
<!-- context:generated:start -->
## Summary

OG image generation module: generateOGImage builds a VNode tree via buildElement from templates, wrapped in workers-og ImageResponse at fixed 1200×630. buildCacheKey produces deterministic SHA-256 hex digest by JSON-stringifying params (watermark merged in) after sorting keys alphabetically — deliberate to avoid hash instability from object key ordering. crypto.subtle requires secure context so cache-key only works in Workers/HTTPS. Templates dispatch on template field (default/blog/article), theme-aware palettes with fixed amber accent, dynamic font sizing based on title length, watermark toggle for snapog.dev brand.

## Related

- part of [[snapog-worker]] — Rendering module used by the main worker entry point.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
