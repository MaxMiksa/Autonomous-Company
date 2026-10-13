---
name: Opportunity Analyst Pipeline
slug: opportunity-analyst-pipeline
type: system
sources:
  - path: scripts/ops/opportunity-analyst-cron.sh
    hash: 57b25b2a7db84a5155d3a56c2cbca69f949cbc56883de0d0d52c2dbf87c63b4e
sources_digest: 927a3e73b4ddafbf79191ec84e859e236b432d3379234edb4566977f1c47dddb
links:
  - to: docker-disk-guard
    relation: depends_on
    description: >-
      docker-prune-safe frequently prunes the pilot image, requiring image-tag
      fallback
  - to: sentry-liveness-heartbeat
    relation: uses
    description: Reports liveness to Sentry Crons via a constructed check-in URL
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The daily cron pipeline (APP-221) that runs the Opportunity Analyst, orchestrating either the legacy in-container Codex engine or the newer one-shot jcode pilot container. opportunity-analyst-cron.sh selects the engine via ANALYST_ENGINE, reports liveness to Sentry Crons, enforces a codex-idle guard to avoid CPU/token contention, launches a disposable container with production volumes mounted, refreshes live scripts/tests from the prod container (image bakes stale copies), and resolves the image tag with fallback because pilot is frequently pruned by docker-prune-safe. It records peak memory from cgroup and has a rollback path running the old in-container script byte-identically.

## Related

- depends on [[docker-disk-guard]] — docker-prune-safe frequently prunes the pilot image, requiring image-tag fallback
- uses [[sentry-liveness-heartbeat]] — Reports liveness to Sentry Crons via a constructed check-in URL
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
