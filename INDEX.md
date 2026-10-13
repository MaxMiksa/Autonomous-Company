# Autonomous Company 索引

[中文](INDEX.md) | [English](i18n/en/INDEX.md) · [文档与语言设置](i18n/README.md)

本文中的路径相对于仓库根目录；命令也在仓库根目录运行。

## 目标

本文件用于快速定位仓库目录结构、脚本职责和调用关系，便于后续维护与排障。

## 目录结构（当前）

### 实现目录（唯一脚本入口）

- `scripts/windows/`: Windows 控制、保活、自启脚本实现
- `scripts/core/`: 主循环与核心控制脚本实现
- `scripts/wsl/`: WSL `systemd --user` 守护脚本实现
- `scripts/macos/`: macOS `launchd` 守护脚本实现

说明：根目录不再保留脚本包装层，执行与维护统一通过 `scripts/`。

### 其他关键目录

- `docs/`: 文档
- `logs/`: 运行日志
- `memories/`: 共识文件
- `projects/`: 独立本地项目仓库（框架只跟踪说明与登记表）

## 核心运行逻辑（Win + WSL）

调用链（默认）：

`scripts/windows/start-win.ps1` -> WSL `systemd --user autonomous-company.service` -> `scripts/core/auto-loop.sh`

说明：
- 默认引擎是 `ENGINE=claude`
- systemd 服务可通过 `.auto-loop.env` 或 `start-win.ps1 -Engine codex` 切换到 Codex；前台循环的引擎配置只读进程环境变量
- Cursor 与 OpenAI-compatible 适配器需显式启用，配置与契约见 `ENGINE_ADAPTERS.md`
- 不做自动引擎回退，所选引擎缺失时直接失败
- 语言首次跟随电脑显示语言；在 Dashboard 或通过 `make language LANGUAGE=en` 保存统一偏好。产品周期内语言固定，中途修改在下个产品周期生效；已保存设置优先于旧环境值。详见[语言设置](i18n/README.md)

停止链路：

`scripts/windows/stop-win.ps1` -> 停止 `autonomous-company.service` + 停止 `awake guardian` + 停止 `wsl anchor`

## 脚本职责表（入口 / 守护 / 自启 / 诊断）

| 类别 | 脚本路径 | 主要职责 |
|---|---|---|
| 入口 | `scripts/windows/start-win.ps1` | 校验服务仓库，保留配置并更新显式参数，启动 WSL daemon、防睡眠与 WSL keepalive |
| 入口 | `scripts/windows/stop-win.ps1` | 停止 daemon 并回收防睡眠与 WSL keepalive |
| 入口 | `scripts/windows/status-win.ps1` | 汇总 guardian/keepalive/autostart/daemon/loop 五层状态 |
| 诊断 | `scripts/windows/monitor-win.ps1` | 实时日志 |
| 诊断 | `scripts/windows/last-win.ps1` | 最近一轮完整输出 |
| 诊断 | `scripts/windows/cycles-win.ps1` | 周期摘要 |
| 诊断 | `scripts/windows/dashboard-win.ps1` | 启动本地 Web 可视化看板 |
| 保活 | `scripts/windows/awake-guardian-win.ps1` | 运行期防睡眠（`start/stop/status/run`） |
| 保活 | `scripts/windows/wsl-anchor-win.ps1` | 维持 WSL 会话常驻（`start/stop/status/run`） |
| 自启 | `scripts/windows/enable-autostart-win.ps1` | 创建登录自启任务 |
| 自启 | `scripts/windows/disable-autostart-win.ps1` | 删除登录自启任务 |
| 自启 | `scripts/windows/autostart-status-win.ps1` | 查询自启任务状态 |
| 守护 | `scripts/wsl/install-wsl-daemon.sh` | 安装并启用 `autonomous-company.service` |
| 守护 | `scripts/wsl/uninstall-wsl-daemon.sh` | 卸载 WSL daemon |
| 守护 | `scripts/wsl/wsl-daemon-status.sh` | 查询 WSL daemon 状态 |
| 守护 | `scripts/wsl/dashboard-wsl.sh` | 为 Linux/WSL Dashboard 查询及启停 `systemd --user` 服务 |
| 守护 | `scripts/macos/install-daemon.sh` | macOS launchd 安装/卸载 |
| 核心 | `scripts/core/auto-loop.sh` | 主循环执行、熔断、日志、共识更新 |
| 核心 | `scripts/core/engine-adapters.sh` | 统一引擎调用与结果契约，不管理服务或治理策略 |
| 核心 | `scripts/core/localization.py` | 保存运行语言、选择本地化资源；保留自定义源文件和人工规则 |
| 核心 | `scripts/core/process-supervisor.sh` | Cycle 进程生命周期；Linux 使用独立子孙监管器 |
| 核心 | `scripts/core/usage.py` | 结构化账本、日/周汇总、预算检查与人工恢复 |
| 核心 | `scripts/core/consensus-guard.sh` | Human Overrides 保护、P1 预检、回滚暂停、成功快照 |
| 核心 | `scripts/core/project.sh` | 独立项目创建、人工选择、状态与显式发布门禁 |
| 核心 | `scripts/core/monitor.sh` | 核心状态/日志输出 |
| 核心 | `scripts/core/stop-loop.sh` | 核心停止/暂停/恢复控制 |

## 快速排障路径

1. 先看 `scripts/windows/status-win.ps1`
2. 再看 `scripts/windows/dashboard-win.ps1` 或 `scripts/windows/monitor-win.ps1`
3. 守护异常看 `scripts/wsl/wsl-daemon-status.sh`
4. 自启异常看 `scripts/windows/autostart-status-win.ps1`（权限问题优先检查管理员 PowerShell）

## 维护规则

1. 新功能优先改 `scripts/` 下实现脚本。
2. 文档变更需同步更新：
   - `README.md`
   - `README-ZH.md`
   - `docs/windows-setup.md`
   - 本索引文件 `INDEX.md`
