# v3 one-time migration / 一次性更名迁移

Autonomous Company (自主公司) was formerly Auto-Company. v3 uses only the new
namespace after migration. Historical reports, releases, logs, screenshots and
third-party repository names retain their original text.

## Existing installations

1. Stop all original loops, product centers, previews, interactive teams and
   configuration writers. Disable the original systemd unit, LaunchAgent or
   Windows scheduled task. Resolve pending product transactions, Human Overrides
   and P1 recovery using the original version before changing its namespace.
2. Preserve the original checkout, Git objects/registrations, dirty files and
   service configuration. Upgrade the framework to v3 in a clean checkout;
   preserve customized instructions. Do not pass renamed state to old code.
   Both v1.6.0 and v2.2.0 state use the explicit migration below. Historical
   frozen workspaces may keep old code; they are historical evidence rather than
   upgraded execution instances.
3. Plan and apply each current runtime's state conversion. Use an absolute
   manifest path outside the moved state directory. The manifest and adjacent
   backup folder are private recovery material; do not publish them.

```sh
python3 scripts/migrate-name.py plan --root /absolute/runtime
python3 scripts/migrate-name.py apply --root /absolute/runtime --manifest /absolute/recovery/runtime.json
python3 scripts/migrate-name.py verify --manifest /absolute/recovery/runtime.json
```

On Windows, use `python` with native Windows paths. Repeat `--root` for separate
runtime roots. The tool renames the program-owned `.auto-company*` state in the
runtime and its immediate product directories, converts only `AUTO_COMPANY_`
configuration keys, and preserves their values, comments and line endings.
Identity ledgers and historical bodies are unchanged. Old/new conflicts, linked
paths and unresolved writer state are rejected without overwriting them.

4. Migrate the center directory. Convert any current runtime roots inside the
   center in separate manifests first, after upgrading their framework code.
   Do not reclassify an execution instance as read-only to avoid migrating it.

```sh
python3 scripts/migrate-name.py plan --data-dir /old/AutoCompany/center --new-data-dir /new/AutonomousCompany/center
python3 scripts/migrate-name.py apply --data-dir /old/AutoCompany/center --new-data-dir /new/AutonomousCompany/center --manifest /absolute/recovery/center.json
```

| Platform | Old default | New default |
|---|---|---|
| Windows | `%LOCALAPPDATA%/AutoCompany/center` | `%LOCALAPPDATA%/AutonomousCompany/center` |
| macOS | `~/Library/Application Support/AutoCompany/center` | `~/Library/Application Support/AutonomousCompany/center` |
| Linux/WSL | `$XDG_STATE_HOME/auto-company/center` | `$XDG_STATE_HOME/autonomous-company/center` |

If `XDG_STATE_HOME` is unset, use `~/.local/state`. Also move the stopped
execution-domain `center-runners` directory from `auto-company` to
`autonomous-company`, preserving owner records and locks. Confirm every old owner
is terminal and its cleanup is complete first; never substitute an empty owner
directory for unresolved ownership. Target directories must be absent.

The center ID, product IDs, request IDs, receipts, configuration fingerprints and
historical timestamps are retained. The migration pauses dispatch and removes
single-request start authorization. An old queued configuration fingerprint is
not silently refreshed: review its context and issue a fresh request when ready.

5. Rename the stopped service registration. `plan` saves its original definition
   and validates ownership; it does not start or replace the service. `apply`
   leaves the new registration disabled. Supply the original and final checkout
   paths explicitly, even when they are identical.

```sh
python3 scripts/migrate-service-name.py plan --kind systemd --old-root /old/runtime --root /new/runtime --manifest /absolute/recovery/service.json
python3 scripts/migrate-service-name.py apply --manifest /absolute/recovery/service.json
```

Use `--kind launchd` on macOS, or `--kind windows-task` with native `python` on
Windows for the default `AutoCompany-WSL-Start` task. New names are
`autonomous-company.service`, `com.autonomouscompany.loop` and
`AutonomousCompany-WSL-Start`. Custom systemd drop-ins and unknown environment
path fields require explicit migration and are rejected by the automatic tool.
macOS keeps the original service restart settings while using launchd's disabled
state. Custom scheduled-task names remain operator-owned and need explicit review.

6. Move any chosen checkout directories with the native platform's tools, then
   repair their existing Git worktree paths using the Git that owns them. Preserve
   locked/recycled registrations and their recovery mapping. Check current paths,
   IDs, language, budget, permissions, human constraints and service state before
   deliberately resuming. Migration never resumes queues or real models.

## Resume and rollback

After interruption, rerun `apply --manifest <same-file>`. The journal accepts only
the recorded original or expected migrated bytes. A partial backup stops before
any instance mutation and requires preserving that backup and creating a new
manifest. The in-progress marker blocks v3 entrypoints; old code does not understand
that marker, so all old writers must remain stopped throughout migration.

```sh
python3 scripts/migrate-name.py rollback --manifest /absolute/recovery/runtime.json
python3 scripts/migrate-service-name.py rollback --manifest /absolute/recovery/service.json
```

Stop the new owners first. New or changed records are preserved by refusing a
blind rollback. Restore code, directory mapping, configuration, database and
service definition as a complete instance; rollback does not restart it and does
not undo external side effects. Keep the original Git/code backup until recovery
is verified. SQLite backup includes its stopped database and sidecars, and the
prepared migrated database is integrity-checked and checkpointed.

Browser center preferences move once under the same origin. A different port or
origin has separate storage; do not assume its old preferences are accessible.
If both keys hold conflicting values, both are retained for explicit recovery.
Old process/user/machine environment names must also be removed after their values
have been saved under the new names; v3 refuses old names rather than choosing
silently between old and new settings.

## 中文操作要点

先停止并禁用旧实例，按旧版本治理要求完成恢复，保全源码、Git 与用户修改，
再升级新框架并转换状态。命令中的路径必须用实际绝对路径；Windows 使用
`python`，WSL/macOS/Linux 使用 `python3`。旧版源码不能读取改名后的配置。

`plan` 检查归属、占用、冲突和未恢复状态；状态 `apply` 先做字节备份，再按日志
逐项切换，中心仍暂停。服务 `plan` 另存原始注册，`apply` 更名后仍禁用。
中断后用同一 manifest 重试；回退时先停止新实例。有新记录或改动时拒绝覆盖。
旧名仅保留于历史、迁移读取/提示和第三方名称；备份只用于恢复，不长期双写。
不要删除或重建产品身份、中心身份、轮次、人工约束，也不要为了改名启动模型。
