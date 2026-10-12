---
name: Evidence Extraction & Validation
slug: evidence-extraction-validation
type: system
sources:
  - path: scripts/ops/directive-rule-sweep.py
    hash: 7284bd834ff1cf86bcc5f6d104cf23388bf9258dcc827b681f578e6ce7172c57
  - path: scripts/ops/extract-axis-evidence.py
    hash: 3f3d55a2a285cd52ab3b0d286b1f908b877283bfde69b03e442d10758080f567
sources_digest: 2dbeb47f834c1b3ea31040058d7248bc716dfbc31616ba7303055f3c36bcd2e5
links:
  - to: human-directive-lifecycle
    relation: validates
    description: >-
      directive-rule-sweep audits which rule-like statements lack standing
      documentation backing
generator:
  version: 1
covers:
  - symbol: key_phrases
    kind: function
    at: 'scripts/ops/directive-rule-sweep.py:L49-L52'
  - symbol: covered
    kind: function
    at: 'scripts/ops/directive-rule-sweep.py:L55-L68'
---
<!-- context:generated:start -->
## Summary

Strict-validation evidence tooling: extracts screened axis headings and bodies from discovery-scan markdown with fail-closed checks (any unreadable file, empty body, or count mismatch exits non-zero so output never silently omits evidence), and a compliance checker for directive rule coverage that treats low token-overlap as a human-review trigger and exits 3 if its canary fixture is not flagged.

## Related

- validates [[human-directive-lifecycle]] — directive-rule-sweep audits which rule-like statements lack standing documentation backing
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
