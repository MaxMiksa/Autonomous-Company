---
name: Auto Company Loop Orchestration
slug: auto-company-loop-orchestration
type: system
sources:
  - path: scripts/core/monitor.sh
    hash: 9a104b2efb99c2712cbff51c614b1dc964f3a8be29ba7bc990c3d63d7c58bd03
  - path: scripts/core/sentry-heartbeat.sh
    hash: 874eccbdbde7e82f3b3f97f023c1503321380b2c7a28754386d1fb7b366ac12f
  - path: scripts/core/stop-loop.sh
    hash: 4ea7f4b5ce31ce14039bf5cedd3c6a9718e2357906fe289906d06debe11f3fe3
  - path: scripts/linux/noop-action.sh
    hash: 0f0aaa7c6c79e6c7844c7528a253084811b9a9b7277f557a1a60a8011347f4d9
  - path: scripts/linux/status-linux.sh
    hash: 1dc4a455fe8ffdd5e1696608d50d02311afd701906d80ee26d5708374d3947d8
  - path: scripts/macos/install-daemon.sh
    hash: 21f1e9576d7552530f20812f04232c75a2dadb4a7f5e3819045a35dec10037e9
  - path: scripts/macos/status-mac.sh
    hash: ba8bc08141ca80245bea6ccb35984221942d6a855ce856e5a492a38c4c151418
sources_digest: 70f5124c9f4a6e9fe9a49ad0f8ac9841733a80e231959a056c0bf40e73807226
links:
  - to: consensus-memory-state-files
    relation: uses
    description: >-
      Reads and writes consensus.md, .auto-loop-state, .auto-loop.pid,
      .auto-loop-paused
  - to: human-directive-write-path
    relation: uses
    description: >-
      The loop's directive handling is gated by directive_writer.py's
      fail-closed rules
  - to: operator-escalation-gate
    relation: uses
    description: >-
      The loop's IDLE-SKIP and hold paths interact with operator-requests.md and
      the escalation gate
  - to: platform-lifecycle-management
    relation: implements
    description: >-
      install-daemon/status scripts implement the loop's lifecycle on macOS
      launchd vs container (Coolify)
  - to: sentry-liveness-heartbeat
    relation: uses
    description: sentry-heartbeat.sh proves the loop PID is alive to catch crash-loops
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The background automation loop that drives the Auto Company: auto-loop.sh (referenced by install-daemon, status scripts, monitor) runs cycles, writes state to .auto-loop-state, PID to .auto-loop.pid, and logs to logs/auto-loop.log. It enforces brakes (PROMPT-SIZE, BUDGET, LIMIT, BREAKER) and IDLE-SKIP paths, and is the main process in the container (Coolify-managed) or a launchd daemon on macOS. The loop is the central consumer of consensus.md, human-directive.md, and the operator-requests ledger, and the producer of cycle verdicts and turn-audit lines.

## Related

- uses [[consensus-memory-state-files]] — Reads and writes consensus.md, .auto-loop-state, .auto-loop.pid, .auto-loop-paused
- uses [[human-directive-write-path]] — The loop's directive handling is gated by directive_writer.py's fail-closed rules
- uses [[operator-escalation-gate]] — The loop's IDLE-SKIP and hold paths interact with operator-requests.md and the escalation gate
- implements [[platform-lifecycle-management]] — install-daemon/status scripts implement the loop's lifecycle on macOS launchd vs container (Coolify)
- uses [[sentry-liveness-heartbeat]] — sentry-heartbeat.sh proves the loop PID is alive to catch crash-loops
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
