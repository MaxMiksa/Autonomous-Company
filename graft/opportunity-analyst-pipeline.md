---
name: Opportunity Analyst Pipeline
slug: opportunity-analyst-pipeline
type: system
sources:
  - path: >-
      scripts/analyst/codex-skill/autocompany-opportunity-director/scripts/context7_docs.sh
    hash: 79198378c25b2ff21cf5e4e2eda13f55c29ac806bd7f9d2bb0cba11a6268c447
  - path: scripts/analyst/opportunity-analyst-jcode.sh
    hash: 44d5ba1f3c85dcd90621856e6db86bd24a0602c8ecbaa9ef36c4018abb28b33b
  - path: scripts/analyst/opportunity-analyst.sh
    hash: a0a766435a1f9e501b97cca96bb30314440de72fd569313488d3b80d5f9c55a5
  - path: scripts/ops/opportunity-analyst-cron.sh
    hash: 57b25b2a7db84a5155d3a56c2cbca69f949cbc56883de0d0d52c2dbf87c63b4e
sources_digest: 7fce090afb02af123d9ebe38362164e2c02edfd8d5ee1a4120544514b3e1ef80
links:
  - to: autonomous-loop-orchestrator
    relation: uses
    description: Shares consensus.md relay and directive_writer.py with the loop.
  - to: directive-registry-management
    relation: uses
    description: >-
      Uses directive_writer.py for safe restore of human-directive.md if
      modified.
  - to: docker-disk-guard
    relation: depends_on
    description: >-
      docker-prune-safe frequently prunes the pilot image, requiring image-tag
      fallback
  - to: registry-merge-promotion-gates
    relation: uses
    description: >-
      Calls merge_registry.py to splice candidate-registry.md live span and
      promote_directive.py as the promotion gate.
  - to: sentry-liveness-heartbeat
    relation: uses
    description: Reports liveness to Sentry Crons via a constructed check-in URL
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The independent 'second-brain' auditor (APP-221) that analyzes the Tender Track portfolio and produces decision reports. Two live entry points: opportunity-analyst.sh (legacy Codex, gpt-5.6-sol) and opportunity-analyst-jcode.sh (jcode, claude-opus-5-5, current since 2026-07-31 cutover). Both run a strict audit-only mode (no registry writes or directive promotion per the 2026-08-24 re-charter), validate the model to avoid silent fallback, wrap OAuth tokens in a claudeAiOauth JSON envelope, persist raw ndjson event streams for cost calibration, and record session IDs for budget exclusion. Enforces a 2400-second timeout and a 126KB prompt-size guard to prevent kernel E2BIG errors; fail-closed on missing credentials or model mismatch.

## Related

- uses [[autonomous-loop-orchestrator]] — Shares consensus.md relay and directive_writer.py with the loop.
- uses [[directive-registry-management]] — Uses directive_writer.py for safe restore of human-directive.md if modified.
- depends on [[docker-disk-guard]] — docker-prune-safe frequently prunes the pilot image, requiring image-tag fallback
- uses [[registry-merge-promotion-gates]] — Calls merge_registry.py to splice candidate-registry.md live span and promote_directive.py as the promotion gate.
- uses [[sentry-liveness-heartbeat]] — Reports liveness to Sentry Crons via a constructed check-in URL
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
