---
name: Platform Lifecycle Management
slug: platform-lifecycle-management
type: system
sources:
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
sources_digest: 7d9659b51d2105504543059c42a7134a7af62c91d1f5aebf5ed0476d57c35d6b
links:
  - to: auto-company-loop-orchestration
    relation: implements
    description: Implements the loop's lifecycle on macOS launchd vs container (Coolify)
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The macOS vs container lifecycle split: install-daemon.sh installs/uninstalls a launchd daemon generating a plist dynamically with KeepAlive tied to the .auto-loop-paused flag, status-mac.sh reports Guardian/Daemon/Autostart/Loop health on macOS, status-linux.sh emits the same Key=Value format for the container (marking sleep guard not_applicable, assuming Coolify restart policy), and noop-action.sh is a placeholder preventing the dashboard from attempting macOS/launchd actions in container mode. stop-loop.sh coordinates graceful shutdown via signal file plus SIGTERM, with pause/resume flags for the daemon.

## Related

- implements [[auto-company-loop-orchestration]] — Implements the loop's lifecycle on macOS launchd vs container (Coolify)
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
