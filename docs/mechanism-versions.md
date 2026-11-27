# 机制版本谱系与回溯对比指南 / Mechanism Versions & Comparison Guide

本文档整理了 `Autonomous-Company` 历代运行/Harness 机制的本地标注标签（均保存于 `runtime/autonomous-company` 的 `refs/tags/mechanism/*`），用于版本回溯、规则对比与隔离对照基准测试。所有标签均为本地只读基准，未推送远端、未自动切换线上运行。

## 版本对比总表

| 标签 (`mechanism/*`) | Commit | 机制定位 | 核心改动与特性 | 适用对比 / 已知边界 |
|---|---|---|---|---|
| `mechanism/legacy-loop-v3` | `2481b1e` | Legacy Loop v3（Harness 前夜） | 基于 `auto-loop.sh` + `consensus.md` 接力的连续自治循环与基础隔离/产品中心基线 | 无细粒度协议状态机、无提交原子契约与不可变输入包；用于对照旧架构基准 |
| `mechanism/harness-v2.1-base` | `d7b132a` | Harness v2.1 + Dashboard v2 基线 | 引入 Company Harness（Unix Socket 桥接、原子提交/回执、`REQUIRED` 质量门禁、`company_harness_runner.py`）与 Dashboard v2 | 初版缺少阶段成果快速收敛、部分交接防死锁与防空转守卫；用于评估纯协议引入效果 |
| `mechanism/harness-v2.1-stage-1023` | `3e81aea` | 阶段成果规则试验版（2026-10-23） | 明确阶段成果/未完成项边界与持续精修规则，保留人工治理红线 | 未解决 `company_harness_client.py` 源码探查、`inputRefs` 冗余与首轮机械停滞；用于单独剥离 prompt 影响 |
| `mechanism/harness-v2.1-eff-1024` | `5fbcc37` | 效率方案实施版（2026-10-24，卡死修复前） | 新增 `company_harness_handoff.py` 确定性交接编译器与短决策段合同，降低哈希手抄成本 | `partial` 产物未建立完成主版本时仍存在下游提案死锁风险，且提交前缺少同步 `prepare_contract` 校验 |
| `mechanism/harness-v2.2-a1` | `06a16e7` | Phase A1：卡死与死锁修复版 | Bridge `submit` 同步预览校验（`_LiveOverlayStore`）、可读 `REVIEW_REQUIRED` / `PROTOCOL_SCOPE` 细节、`MAX_SAME_ERROR` 同错熔断、`artifact_state()` 与 `partial` 死锁修复 | 解决协议提交卡死与无休止原地重试，但尚未治理 `research/review` 循环空转 |
| `mechanism/harness-v2.2-b2` | `e9d4891` | Phase B2：B1 + A1 + Dashboard 稳定性基线 | `pnpm@12.16.1` + Node `24.11.1` 统一、Dashboard 运行时/前端稳定性修复、精选移植 F10 / F11-ext / F13 / F32 | `_cached_capabilities` 缓存空结果/恢复态问题于下一版修复；适合评测纯前端/中心增强 |
| `mechanism/harness-v2.2-a2` | `322dc62` | Phase A2：防空转治理与轻量选题收敛版 | `progression_state()` 停滞追踪、`SPIN_GUARD` / `REDUNDANT_REVIEW`、`reviewTargets` 解耦、首轮智能入口、CLI 速查、`LOOP_INTERVAL=5` 默认、暂缓商业验证的 2–3 候选收敛漏斗，顺带修复 `_cached_capabilities` fail-closed | 待经独立真实模型（`terra high`）端到端长跑对比历史空转数据 |
| `mechanism/harness-v2.2-c` | `feat/c-integration-catalog` HEAD | Phase C：全量交付整合候选 | 汇总机制对比谱系、22 个公开示例实测分级清单与整合收口文档（整合 B1+A1+B2+A2+C） | 仅文档与清单整合；未改动核心 Harness 代码 |

## 回溯与对照操作命令

以下操作均以 `runtime/autonomous-company` 为只读 Git 基准仓（Windows 原生 `git`）：

1. **查看全部机制标签及说明**：
   ```powershell
   git -C runtime\autonomous-company tag -l "mechanism/*" -n1
   ```
2. **对比任意两代核心引擎与 Prompt 差异**（示例：A1 vs A2）：
   ```powershell
   git -C runtime\autonomous-company diff mechanism/harness-v2.2-a1..mechanism/harness-v2.2-a2 -- scripts/core PROMPT.md
   ```
3. **检出独立只读工作树进行对照基准测试**（使用完毕后显式 `git worktree remove`）：
   ```powershell
   git -C runtime\autonomous-company worktree add worktrees\bench-v2.1-base mechanism/harness-v2.1-base
   ```
4. **查看单版本新增变更与提交详情**：
   ```powershell
   git -C runtime\autonomous-company show --stat mechanism/harness-v2.2-a2
   ```
