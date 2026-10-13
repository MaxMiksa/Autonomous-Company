---
name: Docker Disk Guard
slug: docker-disk-guard
type: file
sources:
  - path: scripts/ops/docker-prune-safe.sh
    hash: 7f22912e40c9235114d147f0fb3949880a970ed7104ffcee964c37b187a1cb1d
sources_digest: e24fe28b77d7c48047aeb9d7f3037b12372488dca9bbcb6208518f1e5efa731d
links:
  - to: opportunity-analyst-pipeline
    relation: depends_on
    description: >-
      Its pruning of the pilot image forces image-tag fallback in the analyst
      cron
  - to: telegram-notification-channel
    relation: uses
    description: Pipes alerts into the app container to invoke telegram-notify.sh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

docker-prune-safe.sh is a threshold-gated Docker disk-space guard preventing redeploy churn from exhausting the host's 38GB disk. At WARN (60%) it runs only non-destructive cleanup (builder prune, image prune) never touching containers so crash evidence survives; at THRESH (70%) it additionally prunes stopped containers older than 24h. Volumes are never touched per the company-data constraint. It notifies via Telegram by piping into the running app container (avoiding dot-sourcing runtime.env because values contain |), with a once-per-day WARN notification via a state file.

## Related

- depends on [[opportunity-analyst-pipeline]] — Its pruning of the pilot image forces image-tag fallback in the analyst cron
- uses [[telegram-notification-channel]] — Pipes alerts into the app container to invoke telegram-notify.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
