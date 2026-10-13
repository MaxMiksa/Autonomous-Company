# graft — repo map

Small markdown nodes summarising this repo. `grep` any term, symbol, or
filename here, or run `graft ask "<task>"`. Each node carries prose plus exact
`file:line`; open a source file only to edit the named span.

The same graph is queryable as MCP tools (`graft_find_code`, `graft_find_all`,
`graft_trace_calls`, `graft_file_api`, `graft_repo_map`) where a host exposes them, and
as the `graft` CLI everywhere else. Edges — who calls what — live only in the
graph, not in these files: `graft callers <symbol>` is the only way to read them.

## Concepts

- [airtable-read-write-wrappers](airtable-read-write-wrappers.md) — Airtable Read/Write Wrappers · tests/test_airtable_read.sh, tests/test_airtable_write.sh
- [analyst-engine-plumbing](analyst-engine-plumbing.md) — Analyst Engine Plumbing · tests/test_analyst_engine.sh
- [auto-company-loop-orchestration](auto-company-loop-orchestration.md) — Auto Company Loop Orchestration · scripts/core/monitor.sh, scripts/core/sentry-heartbeat.sh, scripts/core/stop-loop.sh, scripts/linux/noop-action.sh, scripts/linux/status-linux.sh, scripts/macos/install-daemon.sh, scripts/macos/status-mac.sh
- [auto-company-site-functions](auto-company-site-functions.md) — Auto-Company Site Functions · projects/auto-company-site/functions/listeden-cik.js, projects/auto-company-site/functions/randevu.js
- [auto-loop](auto-loop.md) — Auto Loop · scripts/core/auto-loop.sh
- [auto-loop-core-engine](auto-loop-core-engine.md) — auto-loop core engine · scripts/core/auto-loop.sh, tests/test_cycle_counter.sh, tests/test_cycle_metadata.sh, tests/test_discretionary_budget.sh, tests/test_escalation.sh, tests/test_idle_skip.sh, tests/test_mcp_config_manifest_sync.sh, tests/test_mixed_harness.sh, tests/test_prompt_assembly.sh, tests/test_prompt_transport.sh, tests/test_seteshape_lint.py, tests/test_tier_ladder_daily.sh
- [auto-loop-harness](auto-loop-harness.md) — Auto-Loop Harness · tests/test_active_window.sh, tests/test_auto_loop_consensus_prune.sh, tests/test_auto_loop_ledger_guard.sh, tests/test_auto_loop_work_window.sh, tests/test_budget_gates.sh, tests/test_ccusage_failclosed.sh, tests/test_codex_spend_sources.sh
- [bridge-leak-scanner](bridge-leak-scanner.md) — Bridge Leak Scanner · scripts/core/bridge_leak_scan.py
- [cockpit-dashboard](cockpit-dashboard.md) — Cockpit Dashboard · dashboard/app.js
- [cockpit-dashboard-server](cockpit-dashboard-server.md) — Cockpit Dashboard Server · dashboard/server.py
- [compact-ritual-tooling](compact-ritual-tooling.md) — Compact Ritual Tooling · scripts/compact_yol.py, scripts/compact-postcheck.py, scripts/compact-preflight.py, scripts/compact-report.py, scripts/compact-resume-lint.py
- [consensus-ledger-pruning](consensus-ledger-pruning.md) — Consensus & Ledger Pruning · tests/test_auto_loop_consensus_prune.sh, tests/test_auto_loop_ledger_guard.sh, tests/test_consensus_prune.py
- [consensus-memory-state-files](consensus-memory-state-files.md) — Consensus Memory & State Files · scripts/core/operator_request_notify.py, scripts/ops/consensus-prune.py, scripts/ops/idle-skip-note.py, scripts/ops/ledger-guard.py, scripts/ops/registry-archive.py
- [consensus-pruning-archival](consensus-pruning-archival.md) — Consensus Pruning & Archival · scripts/ops/consensus-prune.py, scripts/ops/registry-archive.py
- [container-entrypoint-state-persistence](container-entrypoint-state-persistence.md) — Container Entrypoint & State Persistence · docker-entrypoint.sh
- [context-watch-hook](context-watch-hook.md) — Context Watch Hook · scripts/context-watch.py
- [context7-docs-cli](context7-docs-cli.md) — Context7 Docs CLI · scripts/analyst/codex-skill/autocompany-opportunity-director/scripts/context7_docs.sh
- [context7-tool-surface-auditing](context7-tool-surface-auditing.md) — Context7 & Tool-Surface Auditing · tests/test_context7_check.sh, tests/test_cost_audit_tool_surface.py
- [cost-budget-accounting](cost-budget-accounting.md) — Cost & Budget Accounting · scripts/core/engine-usage-cost.py, scripts/ops/budget-calibration-report.py, scripts/ops/cost-audit.py, scripts/ops/operator-usage-report.sh
- [cycle-cost-turn-auditing](cycle-cost-turn-auditing.md) — Cycle Cost & Turn Auditing · scripts/ops/tool-usage-audit.py, scripts/ops/turn-audit.py, scripts/ops/web-research-cost.py
- [cycle-escalation-brakes](cycle-escalation-brakes.md) — Cycle Escalation Brakes · scripts/ops/turn-bloat-brake.py, scripts/ops/work-window-watchdog.py, scripts/ops/work-window.py
- [cycle-metadata-prompt-transport-contract](cycle-metadata-prompt-transport-contract.md) — cycle metadata & prompt transport contract · scripts/core/auto-loop.sh, scripts/core/codex-final-text.py, tests/test_cycle_metadata.sh, tests/test_prompt_transport.sh
- [dashboard-server](dashboard-server.md) — dashboard server · dashboard/server.py, tests/test_dashboard_server.py
- [directive-promotion-gate](directive-promotion-gate.md) — Directive Promotion Gate · scripts/analyst/promote_directive.py
- [directive-staleness-coverage-watchers](directive-staleness-coverage-watchers.md) — Directive Staleness & Coverage Watchers · scripts/ops/directive-rule-sweep.py, scripts/ops/directive-staleness-watch.py
- [directive-writer](directive-writer.md) — Directive Writer · dashboard/server.py, scripts/analyst/opportunity-analyst-jcode.sh, scripts/analyst/opportunity-analyst.sh, scripts/analyst/promote_directive.py
- [directive-writer-lifecycle](directive-writer-lifecycle.md) — directive writer & lifecycle · scripts/core/directive_writer.py, tests/test_directive_section_refs.sh, tests/test_directive_writer.py
- [docker-disk-guard](docker-disk-guard.md) — Docker Disk Guard · scripts/ops/docker-prune-safe.sh
- [engine-usage-cost-adapter](engine-usage-cost-adapter.md) — engine-usage-cost adapter · scripts/core/engine-usage-cost.py, tests/test_cost_model_hint.sh
- [evidence-extraction-axis-screening](evidence-extraction-axis-screening.md) — Evidence Extraction & Axis Screening · scripts/ops/extract-axis-evidence.py
- [external-data-access-airtable-browser-ki-k](external-data-access-airtable-browser-ki-k.md) — External Data Access (Airtable/Browser/KİK) · scripts/ops/airtable-read.py, scripts/ops/airtable-write.py, scripts/ops/browse-extract.py, scripts/ops/kik-decision-read.py
- [final-text-extraction-jcode-codex](final-text-extraction-jcode-codex.md) — Final-Text Extraction (jcode/codex) · scripts/core/codex-final-text.py, scripts/core/jcode-final-text.py
- [g4-compliance-checks](g4-compliance-checks.md) — G4 compliance checks · scripts/ops/g4-check.py, tests/test_g4_check.sh
- [g4-identity-attribution-verdict](g4-identity-attribution-verdict.md) — G4 Identity-Attribution Verdict · scripts/ops/g4-check.py
- [graft-card-refresh](graft-card-refresh.md) — Graft Card Refresh · scripts/graft-auto-refresh.py
- [headinspect-inspection-logic](headinspect-inspection-logic.md) — HeadInspect Inspection Logic · projects/headinspect/src/inspect.ts
- [headinspect-renderer](headinspect-renderer.md) — HeadInspect Renderer · projects/headinspect/src/render.ts
- [headinspect-schema](headinspect-schema.md) — HeadInspect Schema · projects/headinspect/migrations/0001_hits.sql
- [headinspect-worker](headinspect-worker.md) — HeadInspect Worker · projects/headinspect/src/index.ts
- [human-directive-write-path](human-directive-write-path.md) — Human Directive Write Path · scripts/core/directive_writer.py
- [idle-skip-work-window-brakes](idle-skip-work-window-brakes.md) — idle-skip & work-window brakes · scripts/core/auto-loop.sh, scripts/ops/idle-skip-note.py, scripts/ops/work-window-watchdog.py, scripts/ops/work-window.py, tests/test_idle_skip.sh, tests/test_work_window_watchdog.py, tests/test_work_window.py
- [jcode-pilot-smoke-test](jcode-pilot-smoke-test.md) — jcode Pilot Smoke Test · scripts/analyst/jcode-pilot-smoke.sh
- [ki-k-decision-content-hash-canon](ki-k-decision-content-hash-canon.md) — KİK Decision Content-Hash Canon · scripts/core/decision_text_hash.py, scripts/ops/kik-decision-read.py
- [ki-k-decision-reader](ki-k-decision-reader.md) — KİK Decision Reader · scripts/ops/kik-decision-read.py
- [ledger-guard-audit](ledger-guard-audit.md) — ledger guard & audit · scripts/ops/ledger-guard.py, scripts/ops/tool-usage-audit.py, tests/test_ledger_guard.py, tests/test_tool_usage_audit.sh
- [ledger-integrity-guard](ledger-integrity-guard.md) — Ledger Integrity Guard · scripts/ops/ledger-guard.py
- [linear-workstream-tracking](linear-workstream-tracking.md) — Linear Workstream Tracking · scripts/ops/linear-track.py
- [mcp-config-manifest-sync](mcp-config-manifest-sync.md) — MCP config & manifest sync · scripts/core/jcode-mcp-config.py, scripts/core/jcode-mcp-probe.py, tests/test_jcode_mcp_config.sh, tests/test_mcp_config_manifest_sync.sh, tests/test_mcp_key_fallback.sh, tests/test_mcp_probe.sh
- [mcp-configuration-boot-probe](mcp-configuration-boot-probe.md) — MCP Configuration & Boot Probe · scripts/core/jcode-mcp-config.py, scripts/core/jcode-mcp-probe.py
- [mcp-key-server-verification](mcp-key-server-verification.md) — MCP Key & Server Verification · scripts/ops/verify-mcp-keys.py, tests/fixtures/mock_mcp_server.py
- [one-shot-operator-escalation](one-shot-operator-escalation.md) — one-shot operator escalation · scripts/core/auto-loop.sh, tests/test_escalation.sh
- [operator-action-router](operator-action-router.md) — Operator Action Router · scripts/ops/operator-action-router.py, tests/test_operator_action_router.py
- [operator-alerting-watchers](operator-alerting-watchers.md) — Operator Alerting Watchers · scripts/ops/registry-queue-watch.py, scripts/ops/reply-watch.py, scripts/ops/rfq-reply-watch.py
- [operator-escalation-gate](operator-escalation-gate.md) — Operator Escalation Gate · scripts/core/operator_request_notify.py
- [operator-request-resolution](operator-request-resolution.md) — operator request resolution · scripts/core/operator_request_notify.py, tests/test_operator_request_notify.py, tests/test_refusal_format.sh
- [opportunity-analyst-codex](opportunity-analyst-codex.md) — Opportunity Analyst (Codex) · scripts/analyst/opportunity-analyst.sh
- [opportunity-analyst-jcode](opportunity-analyst-jcode.md) — Opportunity Analyst (jcode) · scripts/analyst/opportunity-analyst-jcode.sh
- [opportunity-analyst-pipeline](opportunity-analyst-pipeline.md) — Opportunity Analyst Pipeline · scripts/ops/opportunity-analyst-cron.sh
- [outreach-eligibility-gate](outreach-eligibility-gate.md) — Outreach Eligibility Gate · scripts/ops/send-gate.py, scripts/ops/site-contact-evidence.py
- [outreach-outcome-watchers](outreach-outcome-watchers.md) — outreach outcome watchers · scripts/ops/reply-watch.py, tests/test_reply_watch.sh
- [platform-lifecycle-management](platform-lifecycle-management.md) — Platform Lifecycle Management · scripts/core/stop-loop.sh, scripts/linux/noop-action.sh, scripts/linux/status-linux.sh, scripts/macos/install-daemon.sh, scripts/macos/status-mac.sh
- [production-mechanism-guard](production-mechanism-guard.md) — production mechanism guard · scripts/prod-mechanism-guard.py, tests/test_prod_mechanism_guard.sh
- [production-surface-guard](production-surface-guard.md) — Production Surface Guard · scripts/prod-mechanism-guard.py
- [registry-merge-tool](registry-merge-tool.md) — Registry Merge Tool · scripts/analyst/merge_registry.py
- [registry-tooling](registry-tooling.md) — registry tooling · scripts/ops/registry-archive.py, scripts/ops/registry-queue-watch.py, tests/test_registry_archive.sh, tests/test_registry_queue_watch.sh
- [rfq-send-pipeline](rfq-send-pipeline.md) — RFQ Send Pipeline · scripts/ops/rfq_template.py, scripts/ops/rfq-send.py
- [rfq-sender-watchers](rfq-sender-watchers.md) — RFQ sender & watchers · scripts/ops/rfq-reply-watch.py, scripts/ops/rfq-send.py, tests/test_rfq_reply_watch.sh, tests/test_rfq_send.sh
- [secret-management-runtime-env-keychain](secret-management-runtime-env-keychain.md) — Secret Management (runtime.env/Keychain) · scripts/core/jcode-mcp-config.py, scripts/core/telegram-notify.sh, scripts/ops/airtable-read.py, scripts/ops/airtable-write.py, scripts/ops/docker-prune-safe.sh, scripts/ops/linear-track.py
- [send-gate](send-gate.md) — send gate · scripts/ops/send-gate.py, tests/test_send_gate.sh
- [sentry-client](sentry-client.md) — Sentry Client · dashboard/sentry_client.py
- [sentry-liveness-heartbeat](sentry-liveness-heartbeat.md) — Sentry Liveness Heartbeat · scripts/core/sentry-heartbeat.sh
- [session-brief-compact-ritual](session-brief-compact-ritual.md) — Session Brief & Compact Ritual · scripts/compact_yol.py, scripts/session-brief.py, tests/test_compact_anchor_sync.py, tests/test_compact_ritual_hardening.sh, tests/test_compact_yol.py
- [snapog-cost-alerts](snapog-cost-alerts.md) — SnapOG Cost Alerts · projects/_archive/snapog/src/alerts/check.ts, projects/_archive/snapog/src/alerts/graphql.ts, projects/_archive/snapog/src/alerts/index.ts, projects/_archive/snapog/src/alerts/thresholds.ts, projects/_archive/snapog/src/alerts/webhook.ts
- [snapog-d1-schema](snapog-d1-schema.md) — SnapOG D1 Schema · projects/_archive/snapog/migrations/0001_init.sql, projects/_archive/snapog/migrations/0002_waitlist.sql, projects/_archive/snapog/migrations/0003_cache_key_tracking.sql
- [snapog-landing-dashboard-pages](snapog-landing-dashboard-pages.md) — SnapOG Landing & Dashboard Pages · projects/_archive/snapog/src/dashboard/pages.ts
- [snapog-north-star-metric](snapog-north-star-metric.md) — SnapOG North-Star Metric · docs/operations/north-star-metric-query.sql
- [snapog-og-rendering](snapog-og-rendering.md) — SnapOG OG Rendering · projects/_archive/snapog/src/og/render.ts, projects/_archive/snapog/src/og/templates.ts
- [snapog-test-scripts](snapog-test-scripts.md) — SnapOG Test Scripts · projects/_archive/snapog/sample/alerts-dry-run.sh, projects/_archive/snapog/sample/cache-cap-test.sh, projects/_archive/snapog/sample/smoke-test.sh
- [snapog-waitlist-function](snapog-waitlist-function.md) — SnapOG Waitlist Function · projects/_archive/snapog-landing/functions/api/waitlist.ts
- [snapog-worker](snapog-worker.md) — SnapOG Worker · projects/_archive/snapog/src/index.ts, projects/_archive/snapog/src/types.ts
- [spending-budget-controls](spending-budget-controls.md) — spending & budget controls · scripts/core/auto-loop.sh, tests/test_discretionary_budget.sh, tests/test_tier_ladder_daily.sh
- [staleness-reporting](staleness-reporting.md) — staleness reporting · scripts/ops/staleness-report.py, tests/test_staleness_report.py
- [state-snapshot-delta](state-snapshot-delta.md) — state snapshot & DELTA · scripts/ops/state-snapshot.py, tests/test_state_snapshot.sh
- [state-snapshot-staleness](state-snapshot-staleness.md) — State Snapshot & Staleness · scripts/ops/staleness-report.py, scripts/ops/state-snapshot.py
- [telegram-notification-channel](telegram-notification-channel.md) — Telegram Notification Channel · scripts/core/telegram-notify.sh, scripts/ops/bloat-trend.py, scripts/ops/directive-staleness-watch.py, scripts/ops/docker-prune-safe.sh, scripts/ops/operator-action-router.py
- [turn-economy-bloat-brakes](turn-economy-bloat-brakes.md) — turn economy & bloat brakes · scripts/ops/turn-audit.py, scripts/ops/turn-bloat-brake.py, tests/test_turn_audit.sh, tests/test_turn_bloat_brake.py
- [turn-economy-bloat-monitoring](turn-economy-bloat-monitoring.md) — Turn-Economy & Bloat Monitoring · scripts/ops/bloat-trend.py, scripts/ops/context7-check.py
- [wowcar-revenue-relabel-acceptance](wowcar-revenue-relabel-acceptance.md) — Wowcar Revenue Relabel Acceptance · scripts/ops/wowcar-revenue-vocabulary-acceptance.py
- [wowcar-revenue-vocabulary](wowcar-revenue-vocabulary.md) — WowCar revenue vocabulary · scripts/ops/wowcar-revenue-vocabulary-acceptance.py, tests/test_wowcar_revenue_vocabulary_acceptance.sh
- [wsl-daemon-management](wsl-daemon-management.md) — WSL Daemon Management · scripts/wsl/install-wsl-daemon.sh, scripts/wsl/uninstall-wsl-daemon.sh, scripts/wsl/wsl-daemon-status.sh

## Files

89 per-file wiring cards mirror the source tree under `graft/` (87 carry extracted symbols). They are deliberately not enumerated here —
`grep` a symbol or `find`/`ls` a filename under `graft/` to land on the card for that file.
