# Windows + WSL 安装指南

[中文](windows-setup.md) | [English](../i18n/en/docs/windows-setup.md) · [文档与语言设置](../i18n/README.md)

除另有说明外，本文中的项目命令在仓库根目录运行。

本项目在 Windows 上采用：

- Windows PowerShell 作为控制入口
- WSL2 (Ubuntu + systemd) 作为执行内核
- WSL `systemd --user` 提供守护与崩溃自拉起
- Windows `scripts/windows/awake-guardian-win.ps1` 提供运行时防睡眠
- Windows `scripts/windows/wsl-anchor-win.ps1` 提供 WSL 会话保活（防止空闲退出）

## 1. 一次性安装（WSL 内）

在 Ubuntu 终端执行：

```bash
sudo apt update
sudo apt install -y git make python3 curl

# 安装 Node.js（推荐 LTS）
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 Claude Code（默认引擎）
npm install -g @anthropic-ai/claude-code

# 可选：安装 Codex CLI（用于 ENGINE=codex）
npm install -g @openai/codex
```

## 2. 一次性自检（WSL 内）

```bash
make --version
claude --version
codex --version
python3 --version
systemctl --user --version
ps -p 1 -o comm=
```

判定标准：
- Python 3.10+，WSL Linux 内核 5.3+（进程身份校验需要 pidfd）
- `systemctl --user --version` 成功
- `ps -p 1 -o comm=` 输出 `systemd`
- CLI 的 `--version` 成功只证明安装，不代表已经登录；首次实际 Cycle 会使用订阅额度或 API 计费

建议额外检查引擎路径（至少检查你要使用的引擎）：

```bash
bash -lc 'command -v claude; claude --version'
bash -lc 'command -v codex; codex --version'
bash -ic 'command -v claude; claude --version'
bash -ic 'command -v codex; codex --version'
```

应优先命中 WSL 本地路径（`/home/<user>/...`），避免 `/mnt/c/...`。

建议一次性启用 linger（提高 user service 持续性）：

```powershell
wsl -d Ubuntu -u root loginctl enable-linger <your-user>
```

## 3. 前置事项（每次开始前）

1. WSL 内 Git、`make`、Python 3.10+、`claude`、`systemctl --user` 可用（如需 codex，再确认 `codex`）。
2. 目标引擎在 WSL 内已登录且可用（默认 `claude`）。
3. 建议确认目标引擎路径优先是 WSL 本地路径（`/home/...`）。

可选快速检查（PowerShell）：

```powershell
wsl -d Ubuntu bash -lc 'make --version; python3 --version; claude --version; systemctl --user --version'
wsl -d Ubuntu bash -lc 'command -v claude'
# Optional (for ENGINE=codex):
wsl -d Ubuntu bash -lc 'codex --version; command -v codex'
```

## 4. 推荐操作（标准）

在仓库根目录运行：

```powershell
# Claude：先在没有密钥的一次性克隆中试运行
.\scripts\windows\start-win.ps1 -Engine claude -ClaudePermissionMode acceptEdits -CycleTimeoutSeconds 1800 -LoopInterval 30

# 切换 Codex
.\scripts\windows\start-win.ps1 -Engine codex -SandboxMode workspace-write -CycleTimeoutSeconds 1800 -LoopInterval 30

.\scripts\windows\status-win.ps1
.\scripts\windows\monitor-win.ps1
.\scripts\windows\last-win.ps1
.\scripts\windows\cycles-win.ps1
.\scripts\windows\stop-win.ps1
.\scripts\windows\dashboard-win.ps1
```

说明：
- `.\scripts\windows\start-win.ps1` 只更新 `.auto-loop.env` 中显式传入的设置，保留已有预算等其他设置，并启动 `autonomous-company.service` + `awake guardian` + `wsl anchor`
- 启停前会校验服务绑定的仓库；若它属于其他 worktree，会拒绝操作。请先人工确认应该使用哪个工作目录，不要为绕过提示而直接重新绑定现有服务
- `.\scripts\windows\stop-win.ps1` 会停止 `autonomous-company.service` 并关闭 `awake guardian` + `wsl anchor`
- `.\scripts\windows\dashboard-win.ps1` 会启动本地 Web 看板（默认 `http://127.0.0.1:8787`）
- 也可在 WSL 仓库目录执行 `make dashboard`；Linux/WSL 看板只通过已安装的 `systemd --user autonomous-company.service` 启停运行时，不会另起前台或 `nohup` 循环

推荐参数：
- `CycleTimeoutSeconds`：`900-1800`
- `LoopInterval`：`30-60`
- `Engine`：`claude`（默认）或 `codex`
- `SandboxMode`：仅在 `ENGINE=codex` 时生效（兼容旧参数 `CodexSandboxMode`）
- `ClaudePermissionMode`：为兼容保留 `bypassPermissions` 默认；首次试运行显式使用 `acceptEdits`，可能因需要交互确认而失败。放宽权限前先评估仓库、网络和凭据风险

脚本定位说明：
- 所有脚本实现位于 `scripts/windows/`、`scripts/core/`、`scripts/wsl/`、`scripts/macos/`
- 日常执行入口也统一使用 `scripts/` 下脚本
- 如需维护逻辑，请直接修改 `scripts/` 下对应实现文件

### 运行与界面语言

首次默认读取 Windows 显示语言，而不是 WSL 的区域设置。中文显示语言使用 `zh-CN`，其他语言使用 `en`。Dashboard 和运行过程使用同一设置，可随时在 Dashboard 保存偏好，或执行：

```powershell
python scripts/core/localization.py set --language en
```

启动参数 `./scripts/windows/start-win.ps1 -Language en` 也保存同一个偏好。已有产品周期仍保持原语言，暂停、重启不会改变；新偏好从下一个产品周期生效。所有技能统一英文，面向用户的结果跟随产品语言。完整说明见[语言设置](../i18n/README.md)。

## 5. 可选：登录后自启

默认不启用。需要时执行：

```powershell
.\scripts\windows\enable-autostart-win.ps1
.\scripts\windows\autostart-status-win.ps1
```

关闭：

```powershell
.\scripts\windows\disable-autostart-win.ps1
```

自启任务名：`AutonomousCompany-WSL-Start`（触发器：At logon）。
若提示 `Access is denied`，请使用管理员 PowerShell 重新执行。

## 6. Chat-first 模式（和 Claude/Codex 对话）

如果你不想手动执行命令，可直接在 Windows 里和 Claude/Codex 对话，让它代你操作。

底层链路：

`scripts/windows/start-win.ps1` -> WSL `systemd --user` -> `scripts/core/auto-loop.sh`

与手动命令的核心行为一致，差异只在入口方式。

## 7. 常见问题

### `bad interpreter: /bin/bash^M`

- 原因：文件是 CRLF
- 处理：

```bash
git config core.autocrlf false
git config core.eol lf
```

### `claude`/`codex` 命令不存在（或 node not found）

- 原因：WSL 中缺 Node 或缺目标引擎 CLI
- 处理：回到第 1 步重新安装

### Claude 运行时卡在权限确认

- 原因：`CLAUDE_PERMISSION_MODE` 设置过严，导致非交互流程被阻塞
- 处理：先检查需要批准的操作；只有确认能够信任工作目录与执行内容后，才考虑显式传 `-ClaudePermissionMode bypassPermissions`。它会跳过权限保护，不是通用修复
- 排查：查看 `logs/auto-loop.log` 中 `Engine: claude | ... | PermissionMode: ...`

### `systemctl --user` 不可用

- 原因：WSL 未启用 systemd 或会话未正确初始化
- 处理：
  - 先确认 `ps -p 1 -o comm=` 是 `systemd`
  - 再验证 `systemctl --user --version`
  - 必要时重开 WSL 会话后重试

### 日志显示 Engine bin 在 `/mnt/c/...`

- 原因：PATH 先命中 Windows 侧 CLI
- 影响：版本和行为可能与 WSL 本地终端不一致
- 处理：在 WSL 内安装并优先使用本地 CLI（`/home/<user>/...`）

### guardian 启动失败

- 现象：`scripts/windows/start-win.ps1` 提示 daemon 已启动，但 guardian 启动失败并返回非零
- 处理：先执行 `.\scripts\windows\status-win.ps1` 确认服务状态，再手动执行 `.\scripts\windows\awake-guardian-win.ps1 -Action start`

### 频繁出现 `Cycle #1 START` 且伴随 `Auto Loop Shutting Down`

- 原因：WSL 会话被回收（常见于 linger 未开启或缺少 keepalive）
- 处理：
  - 确认 `wsl-anchor` 为 RUNNING：`.\scripts\windows\status-win.ps1`
  - 一次性启用 linger：`wsl -d Ubuntu -u root loginctl enable-linger <your-user>`
  - 重启服务：`.\scripts\windows\stop-win.ps1` 然后 `.\scripts\windows\start-win.ps1`

### 自启脚本提示 `Access is denied`

- 原因：当前 PowerShell 权限不足以写入计划任务
- 处理：使用管理员 PowerShell 执行：
  - `.\scripts\windows\enable-autostart-win.ps1`
  - `.\scripts\windows\disable-autostart-win.ps1`
