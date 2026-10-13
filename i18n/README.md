# 语言设置

[English](en/README.md) · [项目说明](../README-ZH.md)

一个语言偏好统一控制 Dashboard、文档入口、AI 的新输出和新产品的目标语言。首次默认读取电脑显示语言：中文使用 `zh-CN`，其他语言使用 `en`；WSL 优先读取 Windows 显示语言，无法读取时使用 Linux 区域设置。

## 选择语言

在 Dashboard 选择语言，或在仓库根目录执行：

```bash
make language LANGUAGE=zh-CN
make language LANGUAGE=en
```

Windows 不使用 make 时：

```powershell
python scripts/core/localization.py set --language en
```

Windows 的 `start-win.ps1 -Language en` 也保存同一个偏好。已保存设置优先于旧服务中的 `AUTONOMOUS_COMPANY_LANGUAGE` 环境变量；环境值只在没有保存设置时提供初始选择。Dashboard 不再保留独立浏览器语言偏好，无需同步修改多处配置。

## 一个产品周期内保持固定

“产品周期”是同一个产品从启动到交付的过程，可以包含多轮 AI 执行。首次开始时固定当前语言；暂停、重启和恢复都沿用它。

| 操作 | 结果 |
|---|---|
| 首次启动前选择英文 | 当前界面和新产品工作使用英文 |
| 中文产品运行中选择英文 | 保存下个周期为英文，当前产品及其界面继续中文 |
| 暂停或重新启动同一产品 | 继续原语言 |
| 明确开始下一个产品周期 | 使用最新保存的偏好 |

Dashboard 会显示当前周期和下个周期的语言。修改偏好无需停止产品，也不会中途改变提示词或生成内容的语言。

准备开始下个产品时，先正常停止前台循环（`make stop`）或暂停后台服务（`make pause`），再执行：

```bash
make next-product CONFIRM=NEXT
```

Windows 可先使用 `./scripts/windows/stop-win.ps1`，再执行：

```powershell
python scripts/core/localization.py next-product --confirm NEXT
```

这一步明确切换产品周期的语言记录，不会启动模型，也不会清空历史、预算、人工规则或现有产品文件。若上一轮异常中断，先按原有恢复流程处理，再切换周期。新产品的项目选择和任务需求仍按正常流程设置。

## 哪些内容跟随语言

| 内容 | 行为 |
|---|---|
| Dashboard、文档入口、常见操作提示 | 使用当前周期语言；尚未开始时使用已选偏好 |
| 新的说明、决策、交付报告与共识正文 | 提示 AI 使用当前周期语言 |
| 新产品界面、帮助、说明文档 | 将当前周期语言作为交付要求，并要求验收检查 |
| 全部附带 skill 源文件 | 统一英文；面向用户的结果仍跟随产品语言 |
| 命令、路径、标识符、协议标题、底层原始错误 | 保留原样 |
| 既有产品、历史日志、自定义源文件、人工规则 | 保留原内容，不追溯翻译 |

AI 生成内容的语言由任务指令约束，仍需在产品验收时检查。GitHub 托管页面、第三方工具和用户提供的原文不受本地设置控制；GitHub 上可使用 README 顶部的中英文入口。

## 资源与维护

角色与文档通过 `source-hashes.json` 选择已审核的译文。仅当源文件未被定制时使用配套译文；源文件已修改或译文缺失时保留源文件，CRLF/LF 换行差异不视为定制。所有技能直接使用 `.claude/skills/` 下的英文版本。

修改受覆盖的源文件时，同步审核两种语言的指令强度、术语、命令和链接，再更新对应哈希。运行语言、Dashboard 和受影响流程的检查；不要仅为消除测试失败刷新哈希。

更多操作见[常见操作与排错](../docs/troubleshooting.md)。

### 写入进程异常退出后的恢复

如果出现配置忙碌或交互会话标记残留的提示，先停止前台循环或暂停后台服务，关闭全部 `make team` 会话及其子进程、Dashboard 和正在修改配置的命令。确认这些进程都已退出后，在仓库根目录执行：

```bash
python3 scripts/core/localization.py recover-lock --confirm RECOVER
```

Windows 使用 `python` 代替 `python3`。`RECOVER` 表示你已确认所有相关进程停止；不要对仍在写入的进程执行。恢复会完成尚未结束的语言偏好保存，并清理残留的操作标记，不改变当前产品语言、不清空历史。若提示循环仍在运行或锁目录内容异常，先处理该原因，不要直接删除配置或治理备份。
