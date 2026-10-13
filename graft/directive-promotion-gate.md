---
name: Directive Promotion Gate
slug: directive-promotion-gate
type: file
sources:
  - path: scripts/analyst/promote_directive.py
    hash: 9c45147f1730fc30545b94a30428d54e0bd40f04506aa3db00614880ec93d677
sources_digest: 529774ce95135d20964e1d42a6242cf44c9928383f17eac44213ac8385a782b9
links:
  - to: directive-writer
    relation: uses
    description: Writes the promoted directive through the deterministic writer.
  - to: opportunity-analyst-codex
    relation: part_of
    description: Pass-3 of the analyst pipeline.
generator:
  version: 1
covers:
  - symbol: sha256
    kind: function
    at: 'scripts/analyst/promote_directive.py:L91-L92'
  - symbol: audit
    kind: function
    at: 'scripts/analyst/promote_directive.py:L95-L98'
  - symbol: blocked
    kind: function
    at: 'scripts/analyst/promote_directive.py:L101-L104'
  - symbol: notify
    kind: function
    at: 'scripts/analyst/promote_directive.py:L107-L113'
  - symbol: main
    kind: function
    at: 'scripts/analyst/promote_directive.py:L116-L225'
---
<!-- context:generated:start -->
## Summary

Deterministic, fail-closed gate deciding whether the Opportunity Analyst's report may overwrite memories/human-directive.md. Pure regex pattern matching (never an LLM) blocks promotion on risk-keyword hits (outreach, payment, deployment, legal, external writes), missing verdict keywords, or escalation language near the current Active Validation ID from consensus.md. Requires live directive Status DONE, backs up to human-directive-backups/, writes new directive with PENDING status and audit metadata, verifies via read-back and diff. Always exits 0 printing PROMOTED or BLOCKED; deliberately over-includes risk terms to favor manual review. No blanket NO-GO auto-promotion, no partial application of mixed directives.

## Related

- uses [[directive-writer]] — Writes the promoted directive through the deterministic writer.
- part of [[opportunity-analyst-codex]] — Pass-3 of the analyst pipeline.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
