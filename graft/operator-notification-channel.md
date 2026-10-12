---
name: Operator Notification Channel
slug: operator-notification-channel
type: system
sources:
  - path: scripts/core/sentry-heartbeat.sh
    hash: 874eccbdbde7e82f3b3f97f023c1503321380b2c7a28754386d1fb7b366ac12f
  - path: scripts/core/telegram-notify.sh
    hash: a6b475c3d6e94b205066d93a4054681477be96876b0f8eac60b47f13ab2573ef
sources_digest: 78ff60ac5e5f3fdca9b6f722d229b13976178c48e2a2ac865cd829b42a6e8728
links:
  - to: auto-company-loop-orchestration
    relation: uses
    description: >-
      sentry-heartbeat verifies the loop PID file and dashboard /api/status
      liveness
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The real-time Telegram notification path shared across the system: a defensive no-op wrapper (silent when credentials unset, never returns non-zero, truncates to 3900 chars) plus the Sentry Crons heartbeat that proves the container process tree is alive independently of the loop, catching crash-loops that app-level error reporting misses.

## Related

- uses [[auto-company-loop-orchestration]] — sentry-heartbeat verifies the loop PID file and dashboard /api/status liveness
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
