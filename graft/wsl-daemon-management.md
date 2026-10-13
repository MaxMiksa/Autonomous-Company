---
name: WSL Daemon Management
slug: wsl-daemon-management
type: system
sources:
  - path: scripts/wsl/install-wsl-daemon.sh
    hash: 2b1d8ba1d5064ade6c138f43bd573d49b659b8bf9f5729d3d339a2ace4ee919b
  - path: scripts/wsl/uninstall-wsl-daemon.sh
    hash: 9a3367f7cbb052a83488d12ed50a81a8d09ff2a5c04ac7620b213b9f052936e3
  - path: scripts/wsl/wsl-daemon-status.sh
    hash: 55fb93df7f080f48a322d005e6b1f76ec2de1c5283de176883b0644d69f39a6a
sources_digest: 9492ae8c037a012dbfdfbe959108c9028822a628598cab08029dd84ec43e3b99
links:
  - to: harness-loop-core
    relation: configures
    description: >-
      The daemon runs scripts/core/auto-loop.sh from the project root as a
      persistent background service.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Bash scripts to install, uninstall, and check the status of a per-user systemd service running auto-loop.sh in WSL. The install writes a unit file with Restart=always and a 10-second restart delay, optionally loading .auto-loop.env, and advises enabling linger for background persistence. The uninstall guards every systemctl call with a version check and treats file removal as the authoritative action (disable wrapped in || true).

## Related

- configures [[harness-loop-core]] — The daemon runs scripts/core/auto-loop.sh from the project root as a persistent background service.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
