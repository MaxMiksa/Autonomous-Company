---
name: Analyst Engine Plumbing
slug: analyst-engine-plumbing
type: system
sources:
  - path: tests/test_analyst_engine.sh
    hash: 9975172ca363f95f265414aed7b6769801f28a4c6d4892120a76ccf6c37631c8
sources_digest: 04012c23372a9308ac83031efe3c9b9bd5450999d99b65d9a60c5cde42315e6a
links:
  - to: auto-loop-harness
    relation: part_of
    description: >-
      The analyst engine is a separate cycle path from the main auto-loop
      harness
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The analyst engine harness (scripts/analyst/opportunity-analyst-jcode.sh) that runs jcode with a model, gated by auth (Claude default failing closed naming CLAUDE_CODE_OAUTH_TOKEN, OpenAI requiring openai-auth.json), provider-specific effort env vars, and session dedup in analyst-jcode-sessions.log. The default engine moved from OpenAI gpt-5.6-sol to Claude in 2026.

## Related

- part of [[auto-loop-harness]] — The analyst engine is a separate cycle path from the main auto-loop harness
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
