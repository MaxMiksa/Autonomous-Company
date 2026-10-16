---
name: Directive Promotion Gate
slug: directive-promotion-gate
type: concept
sources:
  - path: scripts/analyst/promote_directive.py
    hash: 9c45147f1730fc30545b94a30428d54e0bd40f04506aa3db00614880ec93d677
sources_digest: 529774ce95135d20964e1d42a6242cf44c9928383f17eac44213ac8385a782b9
links:
  - to: directive-writer
    relation: uses
    description: Writes the new directive file safely.
  - to: opportunity-analyst
    relation: part_of
    description: Runs as pass 3 of the codex-based analyst.
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

Deterministic, fail-closed gate (promote_directive.py) deciding whether the analyst's report may overwrite memories/human-directive.md. Uses pure regex pattern matching (never an LLM) to block promotion on any risk-keyword hit (outreach, payment, deployment, legal, external writes), missing verdict keywords, or escalation language near the current Active Validation ID. Requires the live directive's Status to be DONE, backs up the current file, writes the new directive with PENDING status and audit metadata, then verifies via read-back and diff. Deliberately over-includes risk terms to favor manual review over false negatives; no blanket NO-GO auto-promotion and no partial application of mixed directives.

## Related

- uses [[directive-writer]] — Writes the new directive file safely.
- part of [[opportunity-analyst]] — Runs as pass 3 of the codex-based analyst.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
