# 高完成度产品筛选与分级清单 / Curated Product Inventory

本清单按“只保留高完成度成品用于主推展示、同时无损保护既有资产”原则，对仓库内 **19 个保留 `examples/`**、**`projects/snapog`**、**6 个暂停中的 `oil-ui` 产品**以及 **3 个已按用户确认移除的 Tier 3 轻量示例**记录如下。

> **状态说明**：经用户明确批准，原 22 个 `examples/` 中的 3 个 Tier 3 轻量/CLI 项（`payment-recovery-audit`、`scope-sheet`、`text-meter`）已从工作树 `examples/` 移除，并同步更新 `scripts/ci/examples.py`、`tests/test_ci_policy.py`、`tests/browser/showcase.spec.js`、`examples/README.md`、`README.md` 与 `README-ZH.md`（历史快照仍可在标签 `mechanism/harness-v2.2-c` @ `e3cd209` 完整回溯）；当前共保留 19 个公开产品（15 Tier 1 + 4 Tier 2）。

## Tier 1：高完成度独立 Web 产品（15 个，推荐保留与主推）

筛选标准：具备独立 `index.html` 可交互前端、本地优先零外部账号/API 依赖、完成核心业务流程且在本次实测中自动化核心套件全量通过（`0` 失败）。

| 产品目录 | 实测通过情况 | 规模（文件 / 体积） | 核心用户任务 |
|---|---|---|---|
| `examples/chart-proof` | Node `15/15` PASS | 20 / 112.2 KB | 制作带数据缺测/近似标记与人工复核证据的图表资料 |
| `examples/coi-chase-desk` | Node `6/6` PASS | 11 / 52.0 KB | 本地保单/收件跟进记录与会话导出工作台 |
| `examples/crm-migration-proof` | Node `64/64` PASS | 21 / 146.4 KB | CRM CSV 迁移身份/字段映射验收与证据导出 |
| `examples/crossed-island-experiment` | Node `26/26` PASS | 22 / 126.7 KB | 同设备双人轮流叙事、分支保留与 JSON 备份恢复 |
| `examples/cuecheck` | Node `24/24` PASS | 17 / 263.7 KB | 本地 SRT 字幕时码/重叠/阅读负担检查与报告导出 |
| `examples/dual-flavor-table` | Node `12/12` PASS | 18 / 117.8 KB | 双口味整餐采购/备料手册（支持禁忌筛选与恢复） |
| `examples/family-memory` | Node `17/17` PASS | 23 / 169.3 KB | 自愿署名与分歧保留的本地家庭故事共创手册 |
| `examples/field-return-audit` | WSL Python `65/65` PASS | 31 / 313.2 KB | SQLite/GeoPackage 离线采集往返核对与审计导出 |
| `examples/participation-recovery` | Node `24/24` PASS | 20 / 159.7 KB | 混合活动参与路径演练、变更恢复与中文交接导出 |
| `examples/rest-rhythm` | Node `19/19` PASS | 16 / 117.1 KB | 按个人恢复节奏编排一日城市探索手账 |
| `examples/reversible-room` | Node `28/28` PASS | 19 / 124.1 KB | 租客可逆房间改善筛选、费用比较与搬迁适配 |
| `examples/scopefence` | Node `8/8` PASS | 11 / 44.6 KB | 自由职业范围/价格/工期变更确认单链接 |
| `examples/spec-evidence` | Node `25/25` PASS | 22 / 119.1 KB | 工程采购规格变更原文定位、复核与证据包生成 |
| `examples/tabledelta` | Node `85/85` PASS | 17 / 191.7 KB | 唯一键关联 CSV 增删改对比与保值 JSON 导出 |
| `examples/tujiandan` | Node `6/6` PASS | 15 / 56.8 KB | 本地批量图片尺寸/体积/格式/命名检查与双语清单导出 |

## Tier 2：专项依赖、纯浏览器验收或用户暂停保留（按需/保护保留）

| 对象 | 状态与实测说明 | 规模 | 处理建议 |
|---|---|---|---|
| `examples/disclosure-qa-spike` | Python `pymupdf` 外部依赖项（基础 Python 环境 `ModuleNotFoundError`） | 20 / 139.2 KB | 需专有 Python 环境；保留完整源码 |
| `examples/ifc-source-preflight` | Python `ifcopenshell` 外部依赖项（基础 Python 环境 `ModuleNotFoundError`） | 45 / 185.9 KB | 需专有 Python 环境；保留完整源码 |
| `examples/family-art-show` | `scripts/ci/examples.py` 标记为 `BROWSER_ONLY`（无独立单元测试） | 18 / 97.7 KB | 交互完整但缺核心单测；建议后续补充核心单测或归入演示位 |
| `examples/tactile-preflight` | `scripts/ci/examples.py` 标记为 `BROWSER_ONLY`（含 `serve.py`，无单测） | 21 / 192.9 KB | 同上，保留源码 |
| `projects/snapog` | 人类本地修改保留资产（原库 `Autonomous-Company/projects/snapog` 与开发工作树同步保护） | 独立子项目 | 永久受保护资产，不动 |
| 6 个 `oil-ui` 暂停产品 | `场序`、`折间`、`执行单`、`时间航道`、`尺价`、`声巷`（2026-10-22 用户要求暂停） | `runs/oil-ui-*` 与运行态 | 保留原状与身份记录；仅随用户明确指令恢复 |

## Tier 3：轻量 / 非 WebUI 项（3 个，已按批准移除；可从历史标签回溯）

| 产品目录 | 移除前实测情况 | 规模 | 移除原因与回溯入口 |
|---|---|---|---|
| `examples/payment-recovery-audit` | Node `5/5` PASS | 12 / 50.6 KB | 仅 CLI/fixture 审计脚本，无 `index.html` 可视界面；可从 `mechanism/harness-v2.2-c` 回溯 |
| `examples/scope-sheet` | `node --check app.js` PASS | 8 / 24.7 KB | 仅单文件静态表单，无自动化单测覆盖（`tests=0`）；可从 `mechanism/harness-v2.2-c` 回溯 |
| `examples/text-meter` | Node `5/5` PASS | 10 / 12.6 KB | 极简字数/行数统计器，产品体量与复杂度偏小；可从 `mechanism/harness-v2.2-c` 回溯 |

上述 3 项的 CI 注册、浏览器目录用例及 README 条目均已同步更新，当前 `scripts/ci/examples.py` 与 `tests/browser/showcase.spec.js` 保持 19 项一比一对齐。
