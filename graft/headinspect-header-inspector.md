---
name: HeadInspect Header Inspector
slug: headinspect-header-inspector
type: system
sources:
  - path: projects/headinspect/migrations/0001_hits.sql
    hash: 651c37d5aafbcd41932f5307a9080183fd953c8b5968f3dd2921bf1c379af022
  - path: projects/headinspect/src/index.ts
    hash: 2c4962e89d06e9fb5bf12aad7cdd08634974a4f57f59cceaa6dca9c98e771499
  - path: projects/headinspect/src/inspect.ts
    hash: 778af3f3556aa953b9e4409c1dee1c52f7fc773639a4e8b2cee22ac8390c75c6
  - path: projects/headinspect/src/render.ts
    hash: 3792b2bd4004ee751d9ae6647d0fc58d9708ef758ad6bfda6beb0a4314bd8883
sources_digest: cb61b3ccfe05c907fe9c1d45e555e1e03b1607816df1e7ac11b12c3268891960
links: []
generator:
  version: 1
covers:
  - symbol: fetch
    kind: method
    at: 'projects/headinspect/src/index.ts:L24-L83'
  - symbol: TargetOk
    kind: type
    at: 'projects/headinspect/src/index.ts:L88-L88'
  - symbol: TargetErr
    kind: type
    at: 'projects/headinspect/src/index.ts:L89-L89'
  - symbol: extractTarget
    kind: function
    at: 'projects/headinspect/src/index.ts:L91-L104'
  - symbol: validateUrl
    kind: function
    at: 'projects/headinspect/src/index.ts:L108-L119'
  - symbol: isBlockedHost
    kind: function
    at: 'projects/headinspect/src/index.ts:L121-L147'
  - symbol: InspectOk
    kind: type
    at: 'projects/headinspect/src/index.ts:L151-L151'
  - symbol: InspectErr
    kind: type
    at: 'projects/headinspect/src/index.ts:L152-L152'
  - symbol: inspect
    kind: function
    at: 'projects/headinspect/src/index.ts:L154-L229'
  - symbol: consume
    kind: function
    at: 'projects/headinspect/src/index.ts:L232-L246'
  - symbol: json
    kind: function
    at: 'projects/headinspect/src/index.ts:L250-L259'
  - symbol: html
    kind: function
    at: 'projects/headinspect/src/index.ts:L261-L271'
  - symbol: svg
    kind: function
    at: 'projects/headinspect/src/index.ts:L275-L284'
  - symbol: Category
    kind: type
    at: 'projects/headinspect/src/inspect.ts:L4-L11'
  - symbol: HeaderEntry
    kind: interface
    at: 'projects/headinspect/src/inspect.ts:L13-L19'
  - symbol: RedirectHop
    kind: interface
    at: 'projects/headinspect/src/inspect.ts:L21-L25'
  - symbol: Grade
    kind: interface
    at: 'projects/headinspect/src/inspect.ts:L27-L31'
  - symbol: InspectReport
    kind: interface
    at: 'projects/headinspect/src/inspect.ts:L33-L42'
  - symbol: categorize
    kind: function
    at: 'projects/headinspect/src/inspect.ts:L86-L95'
  - symbol: HeaderJudgement
    kind: interface
    at: 'projects/headinspect/src/inspect.ts:L99-L102'
  - symbol: judge
    kind: function
    at: 'projects/headinspect/src/inspect.ts:L104-L213'
  - symbol: summarizeSetCookies
    kind: function
    at: 'projects/headinspect/src/inspect.ts:L217-L231'
  - symbol: categorizeHeaders
    kind: function
    at: 'projects/headinspect/src/inspect.ts:L235-L271'
  - symbol: grade
    kind: function
    at: 'projects/headinspect/src/inspect.ts:L275-L356'
  - symbol: has
    kind: function
    at: 'projects/headinspect/src/inspect.ts:L277-L277'
  - symbol: good
    kind: function
    at: 'projects/headinspect/src/inspect.ts:L278-L278'
  - symbol: escapeHtml
    kind: function
    at: 'projects/headinspect/src/render.ts:L16-L23'
  - symbol: badgeColor
    kind: function
    at: 'projects/headinspect/src/render.ts:L27-L36'
  - symbol: textWidth
    kind: function
    at: 'projects/headinspect/src/render.ts:L39-L41'
  - symbol: renderBadge
    kind: function
    at: 'projects/headinspect/src/render.ts:L46-L79'
  - symbol: renderEmbedBlock
    kind: function
    at: 'projects/headinspect/src/render.ts:L81-L94'
  - symbol: renderReport
    kind: function
    at: 'projects/headinspect/src/render.ts:L96-L137'
  - symbol: hostOf
    kind: function
    at: 'projects/headinspect/src/render.ts:L139-L141'
  - symbol: socialMeta
    kind: function
    at: 'projects/headinspect/src/render.ts:L143-L176'
  - symbol: renderPage
    kind: function
    at: 'projects/headinspect/src/render.ts:L178-L242'
---
<!-- context:generated:start -->
## Summary

Cloudflare Worker that fetches a user-supplied URL and reports on its response headers with a security letter grade. Strict SSRF protections via validateUrl and isBlockedHost (rejects non-HTTPS, localhost, private IP ranges, cloud metadata endpoints), follows up to 5 redirects manually, drains bodies to free sockets, 10s AbortController timeout. Pure logic in inspect.ts: deterministic category ordering, regex-based best-effort split for multi-cookie set-cookie (due to Cloudflare's joining behavior), grading that penalizes fingerprint-leaking headers and caps at C when no enforced CSP. Single-template HTML renderer with inline CSS, no client framework; badge endpoint always returns 200 with edge caching so broken embeds never render as broken images. Privacy constraint: only hostname stored, never full URL, to prevent query-string PII leaks.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
