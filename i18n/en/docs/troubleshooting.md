# Common operations and troubleshooting

[English](troubleshooting.md) · [中文](../../../docs/troubleshooting.md) · [Language settings](../README.md)

Run these commands from the Autonomous-Company repository root. `make` commands apply to Linux/WSL and macOS; Windows has PowerShell entrypoints. Keep the original error when troubleshooting: translated guidance explains the next step without replacing the underlying evidence.

## Everyday operations

| Goal | Linux/WSL and macOS | Windows PowerShell |
|---|---|---|
| List commands | `make help` | See the [Windows guide](windows-setup.md) |
| Start | Foreground: `make start`; install background service: `make install` | `./scripts/windows/start-win.ps1` |
| Stop | Foreground loop: `make stop`; background service: `make pause` | `./scripts/windows/stop-win.ps1` |
| Check status | `make status` | `./scripts/windows/status-win.ps1` |
| Read the last cycle | `make last` | `./scripts/windows/last-win.ps1` |
| Save English | `make language LANGUAGE=en` | `python scripts/core/localization.py set --language en` |
| Save Chinese | `make language LANGUAGE=zh-CN` | `python scripts/core/localization.py set --language zh-CN` |

Language preferences can be saved while a product is running. Its current language stays fixed; the preference applies to the next product cycle. Pausing or restarting alone does not begin a new product. See the [language guide](../README.md).

## Installation and startup

| Symptom or original message | Meaning | Next step |
|---|---|---|
| `wsl.exe not found` | Windows cannot invoke WSL | Install and configure WSL using the [Windows guide](windows-setup.md), then start the project. |
| WSL distribution or path conversion fails | The selected distribution is unavailable, or the repository path cannot be converted | Check distribution names with `wsl --list --verbose`; pass the matching `-Distro` to the entrypoint and keep the original path error. |
| Engine executable not found | The selected engine is missing from the execution environment or PATH | On Windows, check the CLI inside the same WSL distribution; configure its entrypoint using the [engine guide](../../../ENGINE_ADAPTERS.md). Do not automatically switch engines. |
| `systemctl --user` cannot connect | The WSL/Linux user service manager is unavailable | Follow the installation guide to enable systemd and reopen the target distribution; retain the full systemctl diagnostic. |
| Already running | Another loop holds this repository's lock | Check status first; stop normally before changing configuration. Do not bypass the lock by deleting PID/lock files. |
| An installed macOS service fails to start | Service configuration, paths or the underlying launchd operation need investigation | Check `make status` and the original launchctl error; stop before correcting configuration. Do not recreate the service merely to change interface language. |

## Language did not change as expected

1. Check the Dashboard's current and next product language. A difference means the preference was saved and is waiting for the next product cycle.
2. Pausing, restarting or beginning another AI iteration of the same product does not change its language.
3. Explicitly start the next product cycle to apply the preference; see [cycle transitions](../README.md).
4. Only `zh-CN` and `en` are accepted. A saved preference takes precedence over an old service environment. Without one, a compatible environment value or system display language supplies the initial choice.
5. Skill sources are English. Commands, protocol fields, history and original errors remain unchanged. Existing products and customized documents are not rewritten automatically.

## Budget pauses and manual recovery

| State | Action |
|---|---|
| Hard budget reached | Read `make usage-status` and `make usage-day` to check usage and limits; resolve the cause before resuming. |
| Hard budget cannot be verified | Usage may be missing; unknown does not mean zero. Check records and engine responses without clearing the ledger. |
| Human-rule or P1 blocker | Read the pause reason, `Human Overrides` and `Priority Issues`; resolve the blocker before resuming instead of removing the rule to bypass it. |

For a Linux/WSL or macOS background service, use `make resume` after resolving the cause. For a foreground loop, stop normally, clear the budget pause with `python3 scripts/core/usage.py resume`, then run `make start` again. Windows users can run the background recovery command inside the matching WSL repository. Resuming does not clear recorded usage; the loop pauses again if the limit is still exceeded. See [usage governance](../../../docs/usage-governance.md).

## P1 issues and human edits

A P1 under `Priority Issues` is a blocker requiring human action. An agent may append an unresolved `- [ ] P1: description`; it must preserve pre-cycle P1 entries and their descriptions verbatim, including history already checked off by a human. Deleting, rewriting or downgrading an existing entry, or adding a checked-off entry, restores the pre-cycle consensus and pauses with reason `priority_issue_mutated`. This recovery does not undo product files or external actions.

Put descriptions that belong to an entry in indented continuation lines beneath it. Another P1, a heading or a sibling list item starts new content. Blank separator lines are not part of the entry.

For a human-rule or P1 content violation, the program attempts to save the rejected draft under `memories/rejected/` and records its location in the log for human review. It is not a successful-cycle snapshot. An archive failure is reported explicitly; the loop remains paused and still attempts to restore the pre-cycle consensus.

Before editing, stop the foreground loop or pause the background service and confirm it has stopped. If the previous cycle was forcibly interrupted, run `bash scripts/core/consensus-guard.sh recover` in the matching Linux/WSL or macOS repository to complete pending recovery first. Successful recovery retains the pause and returns 42; no pending cycle returns 0. If recovery fails, address the original error rather than deleting recovery markers or baselines.

After resolving the issue, a human may change its entry to `- [x] P1: description`, then start or resume the loop. Do not edit this file directly while the model is executing: before/after comparisons cannot reliably preserve content added and then overwritten between checks, and this is not a live interrupt channel.

## What to include in a report

Include your operating system, WSL distribution if applicable, project version, command, selected language, original error and relevant log excerpts. Remove keys, tokens and private business content before sharing; the entire configuration directory is unnecessary.
