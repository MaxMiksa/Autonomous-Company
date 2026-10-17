# Autonomous Company Index

[English](INDEX.md) | [中文](../../INDEX.md) · [Documentation and language settings](../README.md)

Paths in this document are relative to the repository root. Run commands from the repository root as well.

## Purpose

Use this index to find repository directories, script responsibilities, and call relationships when maintaining or troubleshooting the project.

## Current Directory Structure

### Implementation Directories (All Script Entrypoints)

- `scripts/windows/`: Windows control, keepalive, and autostart scripts
- `scripts/core/`: the main loop and core control scripts
- `scripts/wsl/`: WSL `systemd --user` daemon scripts
- `scripts/macos/`: macOS `launchd` daemon scripts

There are no script wrappers at the repository root. Run and maintain scripts directly under `scripts/`.

### Other Key Directories

- `docs/`: documentation
- `logs/`: runtime logs
- `memories/`: consensus files
- `projects/`: independent local project repositories; the framework tracks only their documentation and registry

## Core Runtime Flow (Windows + WSL)

Default call chain:

`scripts/windows/start-win.ps1` -> WSL `systemd --user autonomous-company.service` -> `scripts/core/auto-loop.sh`

Notes:

- The default engine is `ENGINE=claude`.
- To switch a systemd service to Codex, use `.auto-loop.env` or `start-win.ps1 -Engine codex`. The foreground loop reads engine settings only from its process environment.
- Cursor and OpenAI-compatible adapters require explicit opt-in. See [Engine Adapters](../../ENGINE_ADAPTERS.md) for configuration and contracts.
- There is no automatic engine fallback. Startup fails if the selected engine is unavailable.
- Language initially follows the computer's display language. Save one preference in the Dashboard or with `make language LANGUAGE=en`. Each product keeps its starting language; changes apply to the next product cycle. Saved settings take precedence over old environment values. See [language settings](README.md).

Stop sequence:

`scripts/windows/stop-win.ps1` -> stop `autonomous-company.service` + stop `awake guardian` + stop `wsl anchor`

## Script Responsibilities (Entrypoints, Daemons, Autostart, Diagnostics)

| Category | Script Path | Main Responsibility |
|---|---|---|
| Entrypoint | `scripts/windows/start-win.ps1` | Validate the service checkout, preserve configuration while updating explicit parameters, and start the WSL daemon, sleep prevention, and WSL keepalive |
| Entrypoint | `scripts/windows/stop-win.ps1` | Stop the daemon, sleep prevention, and WSL keepalive |
| Entrypoint | `scripts/windows/status-win.ps1` | Summarize guardian, keepalive, autostart, daemon, and loop status |
| Diagnostics | `scripts/windows/monitor-win.ps1` | Stream live logs |
| Diagnostics | `scripts/windows/last-win.ps1` | Show the most recent Cycle's full output |
| Diagnostics | `scripts/windows/cycles-win.ps1` | Show Cycle summaries |
| Diagnostics | `scripts/windows/dashboard-win.ps1` | Start the product center and product details on port 8810 by default |
| Keepalive | `scripts/windows/awake-guardian-win.ps1` | Prevent sleep while running (`start/stop/status/run`) |
| Keepalive | `scripts/windows/wsl-anchor-win.ps1` | Keep the WSL session alive (`start/stop/status/run`) |
| Autostart | `scripts/windows/enable-autostart-win.ps1` | Create the logon startup task |
| Autostart | `scripts/windows/disable-autostart-win.ps1` | Remove the logon startup task |
| Autostart | `scripts/windows/autostart-status-win.ps1` | Query startup task status |
| Daemon | `scripts/wsl/install-wsl-daemon.sh` | Install and enable `autonomous-company.service` |
| Daemon | `scripts/wsl/uninstall-wsl-daemon.sh` | Uninstall the WSL daemon |
| Daemon | `scripts/wsl/wsl-daemon-status.sh` | Query WSL daemon status |
| Daemon | `scripts/wsl/dashboard-wsl.sh` | Query, start, and stop the existing `systemd --user` service with ownership checks |
| Daemon | `scripts/macos/install-daemon.sh` | Install or uninstall the macOS launchd daemon |
| Core | `scripts/core/auto-loop.sh` | Run the main loop, circuit breaker, logging, and consensus updates |
| Core | `scripts/core/engine-adapters.sh` | Provide a shared engine invocation and result contract; does not manage services or governance policy |
| Core | `scripts/core/localization.py` | Save the runtime language and select localized resources while preserving customized source files and human rules |
| Core | `scripts/core/process-supervisor.sh` | Manage Cycle process lifetimes; Linux uses a separate descendant supervisor |
| Core | `scripts/core/usage.py` | Maintain the structured ledger, daily/weekly summaries, budget checks, and manual resume |
| Core | `scripts/core/consensus-guard.sh` | Protect Human Overrides, check P1 issues before execution, roll back and pause, and save successful snapshots |
| Core | `scripts/core/project.sh` | Create independent projects, preserve human selection, report status, and enforce explicit publishing gates |
| Core | `scripts/core/monitor.sh` | Show core status and logs |
| Core | `scripts/core/stop-loop.sh` | Stop, pause, and resume the core loop |

## Quick Troubleshooting Path

1. Start with `scripts/windows/status-win.ps1`.
2. Check `scripts/windows/dashboard-win.ps1` or `scripts/windows/monitor-win.ps1`.
3. For daemon problems, check `scripts/wsl/wsl-daemon-status.sh`.
4. For autostart problems, check `scripts/windows/autostart-status-win.ps1`. For permission errors, first check whether PowerShell is running as administrator.

## Maintenance Rules

1. Implement new functionality in the scripts under `scripts/`.
2. Keep related documentation synchronized:
   - [README.md](../../README.md)
   - [README-ZH.md](../../README-ZH.md)
   - [Windows + WSL Setup Guide](docs/windows-setup.md)
   - This index and its [Chinese source](../../INDEX.md)
