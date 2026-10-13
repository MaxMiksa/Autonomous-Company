# Windows + WSL Setup Guide

[English](windows-setup.md) | [中文](../../../docs/windows-setup.md) · [Documentation and language settings](../README.md)

Unless stated otherwise, run project commands from the repository root.

On Windows, this project uses:

- Windows PowerShell as the control entrypoint
- WSL2 (Ubuntu + systemd) as the execution environment
- WSL `systemd --user` for daemon management and automatic crash recovery
- Windows `scripts/windows/awake-guardian-win.ps1` to prevent sleep while running
- Windows `scripts/windows/wsl-anchor-win.ps1` to keep the WSL session alive and prevent idle shutdown

## 1. One-Time Installation (Inside WSL)

Run in an Ubuntu terminal:

```bash
sudo apt update
sudo apt install -y git make python3 curl

# Install Node.js (LTS recommended)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Install Claude Code (the default engine)
npm install -g @anthropic-ai/claude-code

# Optional: install Codex CLI (for ENGINE=codex)
npm install -g @openai/codex
```

## 2. One-Time Checks (Inside WSL)

```bash
make --version
claude --version
codex --version
python3 --version
systemctl --user --version
ps -p 1 -o comm=
```

Requirements:

- Python 3.10+ and WSL Linux kernel 5.3+; process identity checks require pidfd.
- `systemctl --user --version` succeeds.
- `ps -p 1 -o comm=` prints `systemd`.
- A successful CLI `--version` check confirms installation, not authentication. The first real Cycle consumes subscription quota or incurs API charges.

Also check engine paths, at least for the engine you intend to use:

```bash
bash -lc 'command -v claude; claude --version'
bash -lc 'command -v codex; codex --version'
bash -ic 'command -v claude; claude --version'
bash -ic 'command -v codex; codex --version'
```

Prefer a WSL-local path (`/home/<user>/...`) over `/mnt/c/...`.

Enable linger once to help user services stay running:

```powershell
wsl -d Ubuntu -u root loginctl enable-linger <your-user>
```

## 3. Before Each Start

1. Ensure Git, `make`, Python 3.10+, `claude`, and `systemctl --user` are available inside WSL. Check `codex` too if you plan to use it.
2. Authenticate and verify the selected engine inside WSL; the default is `claude`.
3. Check that the selected engine resolves to a WSL-local path (`/home/...`) first.

Optional quick checks from PowerShell:

```powershell
wsl -d Ubuntu bash -lc 'make --version; python3 --version; claude --version; systemctl --user --version'
wsl -d Ubuntu bash -lc 'command -v claude'
# Optional (for ENGINE=codex):
wsl -d Ubuntu bash -lc 'codex --version; command -v codex'
```

## 4. Recommended Operations

Run from the repository root:

```powershell
# Claude: first try a disposable clone without secrets
.\scripts\windows\start-win.ps1 -Engine claude -ClaudePermissionMode acceptEdits -CycleTimeoutSeconds 1800 -LoopInterval 30

# Switch to Codex
.\scripts\windows\start-win.ps1 -Engine codex -SandboxMode workspace-write -CycleTimeoutSeconds 1800 -LoopInterval 30

.\scripts\windows\status-win.ps1
.\scripts\windows\monitor-win.ps1
.\scripts\windows\last-win.ps1
.\scripts\windows\cycles-win.ps1
.\scripts\windows\stop-win.ps1
.\scripts\windows\dashboard-win.ps1
```

Notes:

- `.\scripts\windows\start-win.ps1` updates only explicitly supplied settings in `.auto-loop.env`, preserves other existing settings such as budgets, and starts `autonomous-company.service`, `awake guardian`, and `wsl anchor`.
- Start and stop operations verify the checkout bound to the service. They refuse to control a service belonging to another worktree. Confirm which working directory you intend to use; do not rebind an existing service just to bypass the check.
- `.\scripts\windows\stop-win.ps1` stops `autonomous-company.service`, `awake guardian`, and `wsl anchor`.
- `.\scripts\windows\dashboard-win.ps1` starts the local web Dashboard, at `http://127.0.0.1:8787` by default.
- You can also run `make dashboard` from the WSL repository directory. The Linux/WSL Dashboard starts and stops the runtime only through the installed `systemd --user autonomous-company.service`; it does not launch a separate foreground or `nohup` loop.

Recommended parameters:

- `CycleTimeoutSeconds`: `900-1800`
- `LoopInterval`: `30-60`
- `Engine`: `claude` (default) or `codex`
- `SandboxMode`: applies only to `ENGINE=codex`; the older `CodexSandboxMode` parameter is still accepted.
- `ClaudePermissionMode`: retains the `bypassPermissions` default for compatibility. Explicitly use `acceptEdits` for a first trial; operations requiring interactive confirmation may fail. Assess repository, network, and credential risks before granting broader permissions.

Script locations:

- All implementations live under `scripts/windows/`, `scripts/core/`, `scripts/wsl/`, and `scripts/macos/`.
- Use these scripts directly for everyday operations.
- To maintain the logic, edit the corresponding implementation under `scripts/`.

### Runtime and Interface Language

The initial default comes from the Windows display language, not the WSL locale. Chinese display languages select `zh-CN`; other languages select `en`. The Dashboard and runtime share one setting. Save your preference in the Dashboard at any time, or run:

```powershell
python scripts/core/localization.py set --language en
```

The startup parameter `./scripts/windows/start-win.ps1 -Language en` saves the same preference. An existing product cycle keeps its original language across pauses and restarts; a changed preference applies to the next product cycle. All skills are written in English, while their user-facing results follow the product language. See [language settings](../README.md).

## 5. Optional: Start at Logon

Disabled by default. To enable it:

```powershell
.\scripts\windows\enable-autostart-win.ps1
.\scripts\windows\autostart-status-win.ps1
```

To disable it:

```powershell
.\scripts\windows\disable-autostart-win.ps1
```

The scheduled task is named `AutonomousCompany-WSL-Start`, with an At logon trigger.
If you see `Access is denied`, rerun the command in an administrator PowerShell window.

## 6. Chat-First Mode (Talk to Claude/Codex)

You can ask Claude/Codex on Windows to operate the project for you instead of entering commands manually.

The underlying call chain is:

`scripts/windows/start-win.ps1` -> WSL `systemd --user` -> `scripts/core/auto-loop.sh`

The runtime behavior is the same as with manual commands; only the entrypoint differs.

## 7. Troubleshooting

### `bad interpreter: /bin/bash^M`

- Cause: the file uses CRLF line endings.
- Fix:

```bash
git config core.autocrlf false
git config core.eol lf
```

### `claude`/`codex` Command Not Found (or node not found)

- Cause: Node or the selected engine CLI is missing inside WSL.
- Fix: repeat the installation in step 1.

### Claude Waits for Permission

- Cause: `CLAUDE_PERMISSION_MODE` is too restrictive for the noninteractive workflow.
- Fix: first inspect the operation requiring approval. Only consider explicitly passing `-ClaudePermissionMode bypassPermissions` after establishing that you trust the working directory and intended operations. This skips permission safeguards and is not a general-purpose fix.
- Diagnostics: look for `Engine: claude | ... | PermissionMode: ...` in `logs/auto-loop.log`.

### `systemctl --user` Is Unavailable

- Cause: systemd is not enabled in WSL, or the session was not initialized correctly.
- Fix:
  - Confirm that `ps -p 1 -o comm=` prints `systemd`.
  - Check `systemctl --user --version`.
  - Reopen the WSL session and retry if necessary.

### Logs Show an Engine Binary Under `/mnt/c/...`

- Cause: PATH resolves to the Windows CLI first.
- Impact: its version and behavior may differ from the CLI in your WSL terminal.
- Fix: install and prioritize a WSL-local CLI (`/home/<user>/...`).

### Guardian Fails to Start

- Symptom: `scripts/windows/start-win.ps1` reports that the daemon started, but guardian startup failed, and returns a nonzero exit code.
- Fix: run `.\scripts\windows\status-win.ps1` to confirm service status, then run `.\scripts\windows\awake-guardian-win.ps1 -Action start` manually.

### Repeated `Cycle #1 START` Followed by `Auto Loop Shutting Down`

- Cause: the WSL session is being shut down, commonly because linger is disabled or keepalive is missing.
- Fix:
  - Check that `wsl-anchor` is RUNNING: `.\scripts\windows\status-win.ps1`.
  - Enable linger once: `wsl -d Ubuntu -u root loginctl enable-linger <your-user>`.
  - Restart the service: `.\scripts\windows\stop-win.ps1`, then `.\scripts\windows\start-win.ps1`.

### Autostart Script Reports `Access is denied`

- Cause: the current PowerShell session lacks permission to modify scheduled tasks.
- Fix: use an administrator PowerShell window to run:
  - `.\scripts\windows\enable-autostart-win.ps1`
  - `.\scripts\windows\disable-autostart-win.ps1`
