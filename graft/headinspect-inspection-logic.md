---
name: HeadInspect Inspection Logic
slug: headinspect-inspection-logic
type: file
sources:
  - path: projects/headinspect/src/inspect.ts
    hash: 778af3f3556aa953b9e4409c1dee1c52f7fc773639a4e8b2cee22ac8390c75c6
sources_digest: 8d2336c69721310ec5798dc9040b95d4e02506d8a61539e3b7f87a1b22612515
links:
  - to: headinspect-worker
    relation: part_of
    description: Pure logic module used by the worker entry point.
generator:
  version: 1
covers:
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
---
<!-- context:generated:start -->
## Summary

Pure logic for inspecting HTTP response headers with no I/O or external dependencies. summarizeSetCookies (privacy-safe cookie counting), categorizeHeaders (maps Headers to sorted HeaderEntry[] with per-header commentary and sanity flags), grade (security letter grade with weighted scoring and hard caps). Deterministic category ordering; regex-based best-effort split for multi-cookie set-cookie values due to Cloudflare's joining behavior; grading penalizes fingerprint-leaking headers and caps grade at C when no enforced CSP present.

## Related

- part of [[headinspect-worker]] — Pure logic module used by the worker entry point.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
