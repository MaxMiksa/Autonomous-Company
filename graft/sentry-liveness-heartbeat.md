---
name: Sentry Liveness Heartbeat
slug: sentry-liveness-heartbeat
type: file
sources:
  - path: scripts/core/sentry-heartbeat.sh
    hash: 874eccbdbde7e82f3b3f97f023c1503321380b2c7a28754386d1fb7b366ac12f
sources_digest: 478d093a57b8382e12406ee9572a739f3d97a5ae5f0b9987559cfeb7682ede19
links:
  - to: auto-company-loop-orchestration
    relation: validates
    description: Proves the loop PID is alive to catch crash-loops
  - to: opportunity-analyst-pipeline
    relation: implements
    description: >-
      The analyst cron constructs its own Sentry check-in URLs using the same
      DSN-parsing approach
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

sentry-heartbeat.sh is a background heartbeat for Sentry Crons proving the container process tree is alive independently of the dashboard or loop cycle, specifically to catch crash-loops (APP-250) that application-level error reporting misses. It verifies the dashboard's /api/status endpoint and the loop PID file, then posts ok/error statuses on a 90-second loop with an 8-second startup grace window. To avoid false positives during fast restart storms (APP-240), it only reports ok if both dashboard and loop PID are alive, and reports error immediately otherwise.

## Related

- validates [[auto-company-loop-orchestration]] — Proves the loop PID is alive to catch crash-loops
- implements [[opportunity-analyst-pipeline]] — The analyst cron constructs its own Sentry check-in URLs using the same DSN-parsing approach
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
