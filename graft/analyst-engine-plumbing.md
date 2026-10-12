---
name: Analyst engine plumbing
slug: analyst-engine-plumbing
type: file
sources:
  - path: tests/test_analyst_engine.sh
    hash: 9975172ca363f95f265414aed7b6769801f28a4c6d4892120a76ccf6c37631c8
sources_digest: 04012c23372a9308ac83031efe3c9b9bd5450999d99b65d9a60c5cde42315e6a
links: []
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The analyst engine orchestration in scripts/analyst/opportunity-analyst-jcode.sh, which fails closed when no credential exists (naming CLAUDE_CODE_OAUTH_TOKEN), picks up literal (non-shell-evaluated) tokens from runtime.env, uses provider-specific effort env vars (JCODE_ANTHROPIC_REASONING_EFFORT vs JCODE_OPENAI_REASONING_EFFORT), dedups done.session_id in the sessions log, and moved the default engine from OpenAI's gpt-5.6-sol to Claude in 2026.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
