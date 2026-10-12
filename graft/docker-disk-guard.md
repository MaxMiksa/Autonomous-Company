---
name: Docker Disk Guard
slug: docker-disk-guard
type: file
sources:
  - path: scripts/ops/docker-prune-safe.sh
    hash: 7f22912e40c9235114d147f0fb3949880a970ed7104ffcee964c37b187a1cb1d
sources_digest: e24fe28b77d7c48047aeb9d7f3037b12372488dca9bbcb6208518f1e5efa731d
links:
  - to: operator-notification-channel
    relation: uses
    description: >-
      Pipes Telegram alerts into the app container which invokes
      telegram-notify.sh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Threshold-gated Docker disk-space guard preventing redeploy churn from exhausting the host's 38GB disk. Two escalation tiers: WARN runs only non-destructive cleanup (never touching containers so crash evidence survives), THRESH additionally prunes recently-stopped containers. Volumes are never touched per the company-data constraint. Notifies by piping into the running app container to avoid dot-sourcing the env file whose values contain '|'.

## Related

- uses [[operator-notification-channel]] — Pipes Telegram alerts into the app container which invokes telegram-notify.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
