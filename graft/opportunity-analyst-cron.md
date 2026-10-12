---
name: Opportunity Analyst Cron
slug: opportunity-analyst-cron
type: file
sources:
  - path: scripts/ops/opportunity-analyst-cron.sh
    hash: 57b25b2a7db84a5155d3a56c2cbca69f949cbc56883de0d0d52c2dbf87c63b4e
sources_digest: 927a3e73b4ddafbf79191ec84e859e236b432d3379234edb4566977f1c47dddb
links:
  - to: cost-budget-accounting
    relation: uses
    description: Records peak memory from cgroup for the jcode run
  - to: operator-notification-channel
    relation: uses
    description: Reports liveness to Sentry Crons via constructed check-in URL
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Daily cron entry point for the Opportunity Analyst, orchestrating either the legacy in-container Codex engine or the newer one-shot jcode pilot container. Enforces a codex-idle guard to avoid CPU/token contention, refreshes live scripts/tests from the prod container (the image bakes stale copies), resolves the image tag with fallback because pilot is frequently pruned, and reports liveness to Sentry Crons. A missing image is fatal (exit 5).

## Related

- uses [[cost-budget-accounting]] — Records peak memory from cgroup for the jcode run
- uses [[operator-notification-channel]] — Reports liveness to Sentry Crons via constructed check-in URL
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
