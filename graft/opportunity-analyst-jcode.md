---
name: Opportunity Analyst (jcode)
slug: opportunity-analyst-jcode
type: system
sources:
  - path: scripts/analyst/opportunity-analyst-jcode.sh
    hash: 44d5ba1f3c85dcd90621856e6db86bd24a0602c8ecbaa9ef36c4018abb28b33b
sources_digest: db7ee69c7d600da2a1b8e9633f0842bf34774174f94adcf6d8688454dbc4fb35
links:
  - to: directive-writer
    relation: uses
    description: Restores the live directive if modified.
  - to: jcode-pilot-smoke-test
    relation: validates
    description: >-
      The smoke test verifies jcode binary runnability and model round-trip
      before production use.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Live production entry point for the Wowcar 2.0 program auditor, replacing the legacy codex-based analyst since 2026-07-31 cutover. Invokes jcode CLI with Claude Opus (claude-opus-5-5) for a three-phase audit: reads skill file, runs single jcode pass with by-reference prompt, writes report to memories/analysis-directive.md. Enforces strict audit-only mode (no registry writes or directive promotion per 2026-08-24 re-charter); validates model against jcode model list to avoid silent fallback; wraps Claude OAuth tokens in claudeAiOauth JSON envelope. Persists raw ndjson event streams to logs/analyst-ndjson for cost calibration; 2400-second timeout (raised from 1500 after canary failure); 126KB prompt-size guard to prevent kernel E2BIG; fail-closed on missing credentials or model mismatch.

## Related

- uses [[directive-writer]] — Restores the live directive if modified.
- validates [[jcode-pilot-smoke-test]] — The smoke test verifies jcode binary runnability and model round-trip before production use.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
