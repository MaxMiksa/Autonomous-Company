---
name: Analyst Engine Plumbing
slug: analyst-engine-plumbing
type: system
sources:
  - path: tests/test_analyst_engine.sh
    hash: 9975172ca363f95f265414aed7b6769801f28a4c6d4892120a76ccf6c37631c8
sources_digest: 04012c23372a9308ac83031efe3c9b9bd5450999d99b65d9a60c5cde42315e6a
links:
  - to: harness-loop-core
    relation: uses
    description: The analyst engine is a separate cycle engine selected by the harness.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The analyst engine harness (scripts/analyst/opportunity-analyst-jcode.sh) that runs the analyst model, with auth gates (Claude default failing closed naming CLAUDE_CODE_OAUTH_TOKEN, OpenAI requiring openai-auth.json), provider-specific effort env vars, session dedup in the ledger, and report headers naming the engine/model. The test suite reflects a 2026 change moving the default engine from OpenAI gpt-5.6-sol to Claude.

## Related

- uses [[harness-loop-core]] — The analyst engine is a separate cycle engine selected by the harness.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
