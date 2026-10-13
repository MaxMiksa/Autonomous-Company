---
name: Deploy & Environment Verification
slug: deploy-environment-verification
type: system
sources:
  - path: scripts/ops/verify-mcp-keys.py
    hash: a35c1f35481876cedc5bb4cf0c7fd4eceaea1c85e57d3c28e87560b3f9f342db
  - path: scripts/wsl/install-wsl-daemon.sh
    hash: 2b1d8ba1d5064ade6c138f43bd573d49b659b8bf9f5729d3d339a2ace4ee919b
  - path: scripts/wsl/uninstall-wsl-daemon.sh
    hash: 9a3367f7cbb052a83488d12ed50a81a8d09ff2a5c04ac7620b213b9f052936e3
  - path: scripts/wsl/wsl-daemon-status.sh
    hash: 55fb93df7f080f48a322d005e6b1f76ec2de1c5283de176883b0644d69f39a6a
sources_digest: 0d9ec295bdbcd2e287f100517cd71a7da3aca8b97065b8a51dd60c5673b25ca2
links:
  - to: auto-loop-harness
    relation: configures
    description: >-
      verify-mcp-keys.py inspects the running auto-loop.sh process environment;
      WSL daemon scripts run auto-loop.sh as a systemd user service
generator:
  version: 1
covers:
  - symbol: loop_env
    kind: function
    at: 'scripts/ops/verify-mcp-keys.py:L39-L51'
  - symbol: main
    kind: function
    at: 'scripts/ops/verify-mcp-keys.py:L54-L75'
---
<!-- context:generated:start -->
## Summary

Operational scripts that verify the deployed environment. verify-mcp-keys.py checks each MCP server receives a well-formed API key by reading /proc/<pid>/environ of the running auto-loop.sh process rather than its own shell (avoiding docker exec's fresh-shell false failures), never printing key values. The WSL daemon scripts install/uninstall/query a per-user systemd service running auto-loop.sh with Restart=always.

## Related

- configures [[auto-loop-harness]] — verify-mcp-keys.py inspects the running auto-loop.sh process environment; WSL daemon scripts run auto-loop.sh as a systemd user service
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
