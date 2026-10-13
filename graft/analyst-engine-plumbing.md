---
name: Analyst Engine Plumbing
slug: analyst-engine-plumbing
type: system
sources:
  - path: tests/test_analyst_engine.sh
    hash: 9975172ca363f95f265414aed7b6769801f28a4c6d4892120a76ccf6c37631c8
sources_digest: 04012c23372a9308ac83031efe3c9b9bd5450999d99b65d9a60c5cde42315e6a
links:
  - to: telegram-notification-core
    relation: uses
    description: Analyst sessions report through the same notification and ledger paths
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The analyst engine harness (opportunity-analyst-jcode.sh) that fails closed when no credential exists, picks up tokens literally (non-shell-evaluated) from runtime.env, propagates provider-specific effort env vars, and dedups done.session_id in the sessions log. Moved default engine from OpenAI gpt-5.6-sol to Claude in 2026.

## Related

- uses [[telegram-notification-core]] — Analyst sessions report through the same notification and ledger paths
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
