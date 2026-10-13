# graft — repo map

Small markdown nodes summarising this repo. `grep` any term, symbol, or
filename here, or run `graft ask "<task>"`. Each node carries prose plus exact
`file:line`; open a source file only to edit the named span.

The same graph is queryable as MCP tools (`graft_find_code`, `graft_find_all`,
`graft_trace_calls`, `graft_file_api`, `graft_repo_map`) where a host exposes them, and
as the `graft` CLI everywhere else. Edges — who calls what — live only in the
graph, not in these files: `graft callers <symbol>` is the only way to read them.

## Concepts

- [airtable-access-wrappers](airtable-access-wrappers.md) — Airtable Access Wrappers · scripts/ops/send-gate.py, tests/test_airtable_read.sh, tests/test_airtable_write.sh
- [analyst-engine-plumbing](analyst-engine-plumbing.md) — Analyst Engine Plumbing · tests/test_analyst_engine.sh
- [auto-company-loop-orchestration](auto-company-loop-orchestration.md) — Auto Company Loop Orchestration · scripts/core/monitor.sh, scripts/core/sentry-heartbeat.sh, scripts/core/stop-loop.sh, scripts/linux/noop-action.sh, scripts/linux/status-linux.sh, scripts/macos/install-daemon.sh, scripts/macos/status-mac.sh
- [auto-loop-core-engine](auto-loop-core-engine.md) — auto-loop core engine · tests/test_cycle_counter.sh, tests/test_cycle_metadata.sh, tests/test_discretionary_budget.sh, tests/test_escalation.sh, tests/test_idle_skip.sh, tests/test_mixed_harness.sh, tests/test_prompt_assembly.sh, tests/test_prompt_guardrails.sh, tests/test_prompt_transport.sh, tests/test_seteshape_lint.py, tests/test_tier_ladder_daily.sh
- [business-hours-window-gating](business-hours-window-gating.md) — Business-Hours & Window Gating · tests/test_active_window.sh, tests/test_auto_loop_work_window.sh
- [consensus-memory-state-files](consensus-memory-state-files.md) — Consensus Memory & State Files · scripts/core/operator_request_notify.py, scripts/ops/consensus-prune.py, scripts/ops/idle-skip-note.py, scripts/ops/ledger-guard.py, scripts/ops/registry-archive.py
- [consensus-pruning-archival](consensus-pruning-archival.md) — Consensus Pruning & Archival · scripts/ops/consensus-prune.py, scripts/ops/registry-archive.py
- [consensus-pruning-ledger-guard](consensus-pruning-ledger-guard.md) — Consensus Pruning & Ledger Guard · tests/test_auto_loop_consensus_prune.sh, tests/test_auto_loop_ledger_guard.sh, tests/test_consensus_prune.py
- [cost-budget-accounting](cost-budget-accounting.md) — Cost & Budget Accounting · scripts/core/engine-usage-cost.py, scripts/ops/budget-calibration-report.py, scripts/ops/cost-audit.py, scripts/ops/operator-usage-report.sh
- [cycle-cost-usage-auditing](cycle-cost-usage-auditing.md) — Cycle Cost & Usage Auditing · scripts/ops/tool-usage-audit.py, scripts/ops/turn-audit.py, scripts/ops/web-research-cost.py, tests/test_context7_check.sh, tests/test_cost_audit_tool_surface.py
- [cycle-metadata-extraction](cycle-metadata-extraction.md) — cycle metadata extraction · tests/test_cycle_metadata.sh, tests/test_mixed_harness.sh
- [dashboard-server](dashboard-server.md) — dashboard server · tests/test_dashboard_server.py, tests/test_refusal_format.sh
- [directive-staleness-coverage-watchers](directive-staleness-coverage-watchers.md) — Directive Staleness & Coverage Watchers · scripts/ops/directive-rule-sweep.py, scripts/ops/directive-staleness-watch.py
- [directive-writer-section-refs](directive-writer-section-refs.md) — directive writer & section refs · tests/test_directive_section_refs.sh, tests/test_directive_writer.py
- [docker-disk-guard](docker-disk-guard.md) — Docker Disk Guard · scripts/ops/docker-prune-safe.sh
- [engine-usage-cost-model-hint](engine-usage-cost-model-hint.md) — engine usage cost & model hint · tests/test_cost_model_hint.sh
- [evidence-extraction-axis-screening](evidence-extraction-axis-screening.md) — Evidence Extraction & Axis Screening · scripts/ops/extract-axis-evidence.py
- [external-data-access-airtable-browser-ki-k](external-data-access-airtable-browser-ki-k.md) — External Data Access (Airtable/Browser/KİK) · scripts/ops/airtable-read.py, scripts/ops/airtable-write.py, scripts/ops/browse-extract.py, scripts/ops/kik-decision-read.py
- [fail-closed-harness-brakes](fail-closed-harness-brakes.md) — Fail-Closed Harness Brakes · scripts/ops/rfq-send.py, scripts/ops/send-gate.py, scripts/ops/turn-bloat-brake.py, scripts/ops/work-window.py
- [final-text-extraction-jcode-codex](final-text-extraction-jcode-codex.md) — Final-Text Extraction (jcode/codex) · scripts/core/codex-final-text.py, scripts/core/jcode-final-text.py
- [g4-attribution-evidence](g4-attribution-evidence.md) — G4 Attribution Evidence · scripts/ops/send-gate.py, scripts/ops/site-contact-evidence.py
- [g4-identity-attribution-verdict](g4-identity-attribution-verdict.md) — G4 Identity-Attribution Verdict · scripts/ops/g4-check.py
- [g4-identity-matching](g4-identity-matching.md) — g4 identity matching · tests/test_g4_check.sh
- [graft-card-refresh](graft-card-refresh.md) — Graft Card Refresh · scripts/graft-auto-refresh.py
- [harness-budget-spend-accounting](harness-budget-spend-accounting.md) — Harness Budget & Spend Accounting · tests/test_budget_gates.sh, tests/test_ccusage_failclosed.sh, tests/test_codex_spend_sources.sh
- [human-directive-write-path](human-directive-write-path.md) — Human Directive Write Path · scripts/core/directive_writer.py
- [idle-skip-mechanism](idle-skip-mechanism.md) — idle-skip mechanism · tests/test_discretionary_budget.sh, tests/test_idle_skip.sh
- [ki-k-decision-content-hash-canon](ki-k-decision-content-hash-canon.md) — KİK Decision Content-Hash Canon · scripts/core/decision_text_hash.py, scripts/ops/kik-decision-read.py
- [ki-k-decision-reader](ki-k-decision-reader.md) — KİK Decision Reader · scripts/ops/kik-decision-read.py
- [ledger-guard](ledger-guard.md) — ledger guard · tests/test_ledger_guard.py
- [ledger-integrity-guard](ledger-integrity-guard.md) — Ledger Integrity Guard · scripts/ops/ledger-guard.py
- [linear-workstream-tracking](linear-workstream-tracking.md) — Linear Workstream Tracking · scripts/ops/linear-track.py
- [mcp-configuration-boot-probe](mcp-configuration-boot-probe.md) — MCP Configuration & Boot Probe · scripts/core/jcode-mcp-config.py, scripts/core/jcode-mcp-probe.py
- [mcp-configuration-key-handling](mcp-configuration-key-handling.md) — MCP configuration & key handling · tests/test_jcode_mcp_config.sh, tests/test_mcp_config_manifest_sync.sh, tests/test_mcp_key_fallback.sh, tests/test_mcp_probe.sh
- [mcp-probe-contract](mcp-probe-contract.md) — MCP probe contract · tests/test_mcp_probe.sh
- [mcp-probe-mock-server](mcp-probe-mock-server.md) — MCP Probe & Mock Server · tests/fixtures/mock_mcp_server.py, tests/test_browse_extract.sh
- [one-shot-escalation](one-shot-escalation.md) — one-shot escalation · tests/test_escalation.sh
- [operator-action-router](operator-action-router.md) — Operator Action Router · scripts/ops/operator-action-router.py, tests/test_operator_action_router.py
- [operator-alerting-watchers](operator-alerting-watchers.md) — Operator Alerting Watchers · scripts/ops/registry-queue-watch.py, scripts/ops/reply-watch.py, scripts/ops/rfq-reply-watch.py, scripts/ops/turn-bloat-brake.py, scripts/ops/work-window-watchdog.py
- [operator-escalation-gate](operator-escalation-gate.md) — Operator Escalation Gate · scripts/core/operator_request_notify.py
- [operator-request-resolution](operator-request-resolution.md) — operator request resolution · tests/test_operator_request_notify.py, tests/test_refusal_format.sh
- [opportunity-analyst-pipeline](opportunity-analyst-pipeline.md) — Opportunity Analyst Pipeline · scripts/ops/opportunity-analyst-cron.sh
- [outreach-send-gating](outreach-send-gating.md) — outreach & send gating · tests/test_g4_check.sh, tests/test_reply_watch.sh, tests/test_rfq_reply_watch.sh, tests/test_rfq_send.sh, tests/test_send_gate.sh
- [platform-lifecycle-management](platform-lifecycle-management.md) — Platform Lifecycle Management · scripts/core/stop-loop.sh, scripts/linux/noop-action.sh, scripts/linux/status-linux.sh, scripts/macos/install-daemon.sh, scripts/macos/status-mac.sh
- [prod-mechanism-guard](prod-mechanism-guard.md) — Prod-Mechanism Guard · scripts/prod-mechanism-guard.py, tests/test_prod_mechanism_guard.sh, tests/test_rfq_send.sh
- [prompt-assembly-guardrails](prompt-assembly-guardrails.md) — prompt assembly & guardrails · tests/test_prompt_assembly.sh, tests/test_prompt_guardrails.sh
- [prompt-transport-contract](prompt-transport-contract.md) — prompt transport contract · tests/test_prompt_transport.sh
- [registry-operations](registry-operations.md) — registry operations · tests/test_registry_archive.sh, tests/test_registry_queue_watch.sh
- [rfq-email-content-templates](rfq-email-content-templates.md) — RFQ Email Content Templates · scripts/ops/rfq_template.py
- [secret-management-runtime-env-keychain](secret-management-runtime-env-keychain.md) — Secret Management (runtime.env/Keychain) · scripts/core/jcode-mcp-config.py, scripts/core/telegram-notify.sh, scripts/ops/airtable-read.py, scripts/ops/airtable-write.py, scripts/ops/docker-prune-safe.sh, scripts/ops/linear-track.py
- [sentry-liveness-heartbeat](sentry-liveness-heartbeat.md) — Sentry Liveness Heartbeat · scripts/core/sentry-heartbeat.sh
- [session-brief-compact-ritual](session-brief-compact-ritual.md) — Session Brief & Compact Ritual · scripts/session-brief.py, tests/test_compact_anchor_sync.py, tests/test_compact_ritual_hardening.sh, tests/test_compact_yol.py
- [set-e-shape-lint](set-e-shape-lint.md) — set -e shape lint · tests/test_seteshape_lint.py
- [spending-controls-ledger](spending-controls-ledger.md) — spending controls & ledger · tests/test_discretionary_budget.sh
- [state-snapshot-delta-probing](state-snapshot-delta-probing.md) — State Snapshot & Delta Probing · scripts/ops/staleness-report.py, scripts/ops/state-snapshot.py, scripts/ops/work-window.py
- [state-snapshot-staleness](state-snapshot-staleness.md) — state snapshot & staleness · tests/test_staleness_report.py, tests/test_state_snapshot.sh
- [telegram-notification-channel](telegram-notification-channel.md) — Telegram Notification Channel · scripts/core/telegram-notify.sh, scripts/ops/bloat-trend.py, scripts/ops/directive-staleness-watch.py, scripts/ops/docker-prune-safe.sh, scripts/ops/operator-action-router.py
- [telegram-notification-core](telegram-notification-core.md) — Telegram Notification Core · scripts/ops/registry-queue-watch.py, scripts/ops/reply-watch.py, scripts/ops/rfq-reply-watch.py, scripts/ops/verify-mcp-keys.py
- [tier-ladder-budgeting](tier-ladder-budgeting.md) — tier ladder budgeting · tests/test_tier_ladder_daily.sh
- [tool-usage-audit](tool-usage-audit.md) — tool usage audit · tests/test_tool_usage_audit.sh
- [turn-economy-bloat-control](turn-economy-bloat-control.md) — turn economy & bloat control · tests/test_turn_audit.sh, tests/test_turn_bloat_brake.py
- [turn-economy-bloat-monitoring](turn-economy-bloat-monitoring.md) — Turn-Economy & Bloat Monitoring · scripts/ops/bloat-trend.py, scripts/ops/context7-check.py
- [work-window-watchdog](work-window-watchdog.md) — work window & watchdog · tests/test_work_window_watchdog.py, tests/test_work_window.py
- [wowcar-revenue-relabel-acceptance](wowcar-revenue-relabel-acceptance.md) — Wowcar Revenue Relabel Acceptance · scripts/ops/wowcar-revenue-vocabulary-acceptance.py
- [wowcar-revenue-vocabulary](wowcar-revenue-vocabulary.md) — wowcar revenue vocabulary · tests/test_wowcar_revenue_vocabulary_acceptance.sh
- [wsl-systemd-daemon](wsl-systemd-daemon.md) — WSL Systemd Daemon · scripts/wsl/install-wsl-daemon.sh, scripts/wsl/uninstall-wsl-daemon.sh, scripts/wsl/wsl-daemon-status.sh

## Files

89 per-file wiring cards mirror the source tree under `graft/` (87 carry extracted symbols). They are deliberately not enumerated here —
`grep` a symbol or `find`/`ls` a filename under `graft/` to land on the card for that file.
