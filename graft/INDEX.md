# graft — repo map

Small markdown nodes summarising this repo. `grep` any term, symbol, or
filename here, or run `graft ask "<task>"`. Each node carries prose plus exact
`file:line`; open a source file only to edit the named span.

The same graph is queryable as MCP tools (`graft_find_code`, `graft_find_all`,
`graft_trace_calls`, `graft_file_api`, `graft_repo_map`) where a host exposes them, and
as the `graft` CLI everywhere else. Edges — who calls what — live only in the
graph, not in these files: `graft callers <symbol>` is the only way to read them.

## Concepts

- [airtable-access-wrappers](airtable-access-wrappers.md) — Airtable access wrappers · tests/test_airtable_read.sh, tests/test_airtable_write.sh
- [analyst-engine-plumbing](analyst-engine-plumbing.md) — Analyst engine plumbing · tests/test_analyst_engine.sh
- [auto-company-loop-orchestration](auto-company-loop-orchestration.md) — Auto Company Loop Orchestration · scripts/core/monitor.sh, scripts/core/sentry-heartbeat.sh, scripts/core/stop-loop.sh, scripts/linux/noop-action.sh, scripts/linux/status-linux.sh, scripts/macos/install-daemon.sh, scripts/macos/status-mac.sh
- [auto-company-site-pages-functions](auto-company-site-pages-functions.md) — Auto-Company Site Pages Functions · projects/auto-company-site/functions/listeden-cik.js, projects/auto-company-site/functions/randevu.js
- [auto-loop-core-engine](auto-loop-core-engine.md) — auto-loop core engine · scripts/core/auto-loop.sh, tests/test_cycle_counter.sh, tests/test_cycle_metadata.sh, tests/test_discretionary_budget.sh, tests/test_escalation.sh, tests/test_idle_skip.sh, tests/test_mixed_harness.sh, tests/test_prompt_assembly.sh, tests/test_prompt_transport.sh, tests/test_seteshape_lint.py, tests/test_tier_ladder_daily.sh
- [auto-loop-harness](auto-loop-harness.md) — Auto-loop harness · tests/test_active_window.sh, tests/test_auto_loop_consensus_prune.sh, tests/test_auto_loop_ledger_guard.sh, tests/test_auto_loop_work_window.sh, tests/test_budget_gates.sh, tests/test_ccusage_failclosed.sh, tests/test_codex_spend_sources.sh
- [autonomous-loop](autonomous-loop.md) — Autonomous Loop · scripts/core/auto-loop.sh
- [bridge-leak-scanner](bridge-leak-scanner.md) — Bridge Leak Scanner · scripts/core/bridge_leak_scan.py
- [browse-extract-mcp-gateway-client](browse-extract-mcp-gateway-client.md) — browse-extract MCP gateway client · tests/test_browse_extract.sh
- [cockpit-dashboard](cockpit-dashboard.md) — Cockpit Dashboard · dashboard/app.js, dashboard/sentry_client.py, dashboard/server.py
- [compact-ritual-path-resolution](compact-ritual-path-resolution.md) — Compact ritual path resolution · scripts/compact_yol.py, tests/test_compact_anchor_sync.py, tests/test_compact_ritual_hardening.sh, tests/test_compact_yol.py
- [compact-ritual-tooling](compact-ritual-tooling.md) — Compact Ritual Tooling · scripts/compact_yol.py, scripts/compact-postcheck.py, scripts/compact-preflight.py, scripts/compact-report.py, scripts/compact-resume-lint.py
- [consensus-document-pruning](consensus-document-pruning.md) — Consensus document pruning · tests/test_auto_loop_consensus_prune.sh, tests/test_consensus_prune.py
- [consensus-memory-state-files](consensus-memory-state-files.md) — Consensus Memory & State Files · scripts/core/operator_request_notify.py, scripts/ops/consensus-prune.py, scripts/ops/idle-skip-note.py, scripts/ops/ledger-guard.py, scripts/ops/registry-archive.py
- [consensus-pruning-archival](consensus-pruning-archival.md) — Consensus Pruning & Archival · scripts/ops/consensus-prune.py, scripts/ops/registry-archive.py
- [container-entrypoint-state-persistence](container-entrypoint-state-persistence.md) — Container Entrypoint & State Persistence · docker-entrypoint.sh
- [context-watch-hook](context-watch-hook.md) — Context Watch Hook · scripts/context-watch.py
- [context7-import-audit](context7-import-audit.md) — Context7 import audit · tests/test_context7_check.sh
- [cost-audit-tool-surface](cost-audit-tool-surface.md) — Cost-audit tool surface · tests/test_cost_audit_tool_surface.py
- [cost-budget-accounting](cost-budget-accounting.md) — Cost & Budget Accounting · scripts/core/engine-usage-cost.py, scripts/ops/budget-calibration-report.py, scripts/ops/cost-audit.py, scripts/ops/operator-usage-report.sh
- [cycle-cost-risk-audit](cycle-cost-risk-audit.md) — Cycle cost & risk audit · scripts/ops/tool-usage-audit.py, scripts/ops/turn-audit.py, scripts/ops/web-research-cost.py
- [cycle-metadata-extraction](cycle-metadata-extraction.md) — cycle metadata extraction · scripts/core/auto-loop.sh, scripts/core/codex-final-text.py, tests/test_cycle_metadata.sh, tests/test_mixed_harness.sh
- [dashboard-server](dashboard-server.md) — dashboard server · dashboard/server.py, tests/test_dashboard_server.py, tests/test_refusal_format.sh
- [directive-staleness-coverage-watchers](directive-staleness-coverage-watchers.md) — Directive Staleness & Coverage Watchers · scripts/ops/directive-rule-sweep.py, scripts/ops/directive-staleness-watch.py
- [directive-write-gate](directive-write-gate.md) — Directive Write Gate · dashboard/server.py, scripts/analyst/opportunity-analyst-jcode.sh, scripts/analyst/opportunity-analyst.sh, scripts/analyst/promote_directive.py
- [directive-writer](directive-writer.md) — directive writer · scripts/core/directive_writer.py, tests/test_directive_section_refs.sh, tests/test_directive_writer.py
- [docker-disk-guard](docker-disk-guard.md) — Docker Disk Guard · scripts/ops/docker-prune-safe.sh
- [engine-usage-cost-adapter](engine-usage-cost-adapter.md) — Engine usage cost adapter · tests/test_cost_model_hint.sh
- [evidence-extraction-axis-screening](evidence-extraction-axis-screening.md) — Evidence Extraction & Axis Screening · scripts/ops/extract-axis-evidence.py
- [external-data-access-airtable-browser-ki-k](external-data-access-airtable-browser-ki-k.md) — External Data Access (Airtable/Browser/KİK) · scripts/ops/airtable-read.py, scripts/ops/airtable-write.py, scripts/ops/browse-extract.py, scripts/ops/kik-decision-read.py
- [final-text-extraction-jcode-codex](final-text-extraction-jcode-codex.md) — Final-Text Extraction (jcode/codex) · scripts/core/codex-final-text.py, scripts/core/jcode-final-text.py
- [g4-attribution-evidence](g4-attribution-evidence.md) — G4 attribution evidence · scripts/ops/site-contact-evidence.py
- [g4-identity-attribution-verdict](g4-identity-attribution-verdict.md) — G4 Identity-Attribution Verdict · scripts/ops/g4-check.py
- [graft-card-refresh](graft-card-refresh.md) — Graft Card Refresh · scripts/graft-auto-refresh.py
- [headinspect-header-inspector](headinspect-header-inspector.md) — HeadInspect Header Inspector · projects/headinspect/migrations/0001_hits.sql, projects/headinspect/src/index.ts, projects/headinspect/src/inspect.ts, projects/headinspect/src/render.ts
- [human-directive-write-path](human-directive-write-path.md) — Human Directive Write Path · scripts/core/directive_writer.py
- [jcode-pilot-smoke-test](jcode-pilot-smoke-test.md) — jcode Pilot Smoke Test · scripts/analyst/jcode-pilot-smoke.sh
- [ki-k-decision-content-hash-canon](ki-k-decision-content-hash-canon.md) — KİK Decision Content-Hash Canon · scripts/core/decision_text_hash.py, scripts/ops/kik-decision-read.py
- [ki-k-decision-reader](ki-k-decision-reader.md) — KİK Decision Reader · scripts/ops/kik-decision-read.py
- [ledger-guard](ledger-guard.md) — ledger guard · scripts/ops/ledger-guard.py, tests/test_ledger_guard.py
- [ledger-integrity-guard](ledger-integrity-guard.md) — Ledger Integrity Guard · scripts/ops/ledger-guard.py
- [linear-workstream-tracking](linear-workstream-tracking.md) — Linear Workstream Tracking · scripts/ops/linear-track.py
- [mcp-configuration-boot-probe](mcp-configuration-boot-probe.md) — MCP Configuration & Boot Probe · scripts/core/jcode-mcp-config.py, scripts/core/jcode-mcp-probe.py
- [mcp-configuration-system](mcp-configuration-system.md) — MCP configuration system · scripts/core/jcode-mcp-config.py, scripts/core/jcode-mcp-probe.py, tests/fixtures/mock_mcp_server.py, tests/test_jcode_mcp_config.sh, tests/test_mcp_config_manifest_sync.sh, tests/test_mcp_key_fallback.sh, tests/test_mcp_probe.sh
- [mcp-key-fallback](mcp-key-fallback.md) — MCP key fallback · scripts/core/jcode-mcp-config.py, tests/test_mcp_key_fallback.sh
- [mcp-key-verification](mcp-key-verification.md) — MCP key verification · scripts/ops/verify-mcp-keys.py
- [mock-mcp-server-fixture](mock-mcp-server-fixture.md) — Mock MCP server fixture · tests/fixtures/mock_mcp_server.py
- [operator-action-router](operator-action-router.md) — Operator Action Router · scripts/ops/operator-action-router.py, tests/test_operator_action_router.py
- [operator-alerting-watchers](operator-alerting-watchers.md) — Operator alerting watchers · scripts/ops/registry-queue-watch.py, scripts/ops/reply-watch.py, scripts/ops/rfq-reply-watch.py
- [operator-escalation-gate](operator-escalation-gate.md) — Operator Escalation Gate · scripts/core/operator_request_notify.py
- [operator-request-notification](operator-request-notification.md) — operator request notification · scripts/core/operator_request_notify.py, tests/test_operator_request_notify.py, tests/test_refusal_format.sh
- [opportunity-analyst](opportunity-analyst.md) — Opportunity Analyst · scripts/analyst/codex-skill/autocompany-opportunity-director/scripts/context7_docs.sh, scripts/analyst/merge_registry.py, scripts/analyst/opportunity-analyst-jcode.sh, scripts/analyst/opportunity-analyst.sh, scripts/analyst/promote_directive.py
- [opportunity-analyst-pipeline](opportunity-analyst-pipeline.md) — Opportunity Analyst Pipeline · scripts/ops/opportunity-analyst-cron.sh
- [outreach-and-send-gating](outreach-and-send-gating.md) — outreach and send gating · scripts/ops/g4-check.py, scripts/ops/reply-watch.py, scripts/ops/rfq-reply-watch.py, scripts/ops/rfq-send.py, scripts/ops/send-gate.py, tests/test_g4_check.sh, tests/test_reply_watch.sh, tests/test_rfq_reply_watch.sh, tests/test_rfq_send.sh, tests/test_send_gate.sh
- [platform-lifecycle-management](platform-lifecycle-management.md) — Platform Lifecycle Management · scripts/core/stop-loop.sh, scripts/linux/noop-action.sh, scripts/linux/status-linux.sh, scripts/macos/install-daemon.sh, scripts/macos/status-mac.sh
- [prod-mechanism-guard](prod-mechanism-guard.md) — Prod-mechanism guard · scripts/prod-mechanism-guard.py
- [production-mechanism-guard](production-mechanism-guard.md) — production mechanism guard · scripts/prod-mechanism-guard.py, tests/test_prod_mechanism_guard.sh
- [prompt-transport-contract](prompt-transport-contract.md) — prompt transport contract · scripts/core/auto-loop.sh, tests/test_prompt_transport.sh
- [registry-merge-invariants](registry-merge-invariants.md) — Registry Merge Invariants · scripts/analyst/merge_registry.py
- [registry-queue-watch](registry-queue-watch.md) — registry queue watch · scripts/ops/registry-archive.py, scripts/ops/registry-queue-watch.py, tests/test_registry_archive.sh, tests/test_registry_queue_watch.sh
- [rfq-send-pipeline](rfq-send-pipeline.md) — RFQ send pipeline · scripts/ops/rfq_template.py, scripts/ops/rfq-send.py
- [secret-management-runtime-env-keychain](secret-management-runtime-env-keychain.md) — Secret Management (runtime.env/Keychain) · scripts/core/jcode-mcp-config.py, scripts/core/telegram-notify.sh, scripts/ops/airtable-read.py, scripts/ops/airtable-write.py, scripts/ops/docker-prune-safe.sh, scripts/ops/linear-track.py
- [send-gate-py-eligibility-brake](send-gate-py-eligibility-brake.md) — send-gate.py eligibility brake · scripts/ops/send-gate.py
- [sentry-error-reporting](sentry-error-reporting.md) — Sentry Error Reporting · dashboard/sentry_client.py
- [sentry-liveness-heartbeat](sentry-liveness-heartbeat.md) — Sentry Liveness Heartbeat · scripts/core/sentry-heartbeat.sh
- [session-brief-hook](session-brief-hook.md) — Session brief hook · scripts/session-brief.py
- [set-e-shape-lint](set-e-shape-lint.md) — set -e shape lint · docker-entrypoint.sh, scripts/core/auto-loop.sh, tests/test_seteshape_lint.py
- [snapog-cost-alerting](snapog-cost-alerting.md) — SnapOG Cost Alerting · projects/_archive/snapog/sample/alerts-dry-run.sh, projects/_archive/snapog/src/alerts/check.ts, projects/_archive/snapog/src/alerts/graphql.ts, projects/_archive/snapog/src/alerts/index.ts, projects/_archive/snapog/src/alerts/thresholds.ts, projects/_archive/snapog/src/alerts/webhook.ts
- [snapog-landing-dashboard-pages](snapog-landing-dashboard-pages.md) — SnapOG Landing & Dashboard Pages · projects/_archive/snapog/src/dashboard/pages.ts
- [snapog-north-star-metric-sql](snapog-north-star-metric-sql.md) — SnapOG North-Star Metric SQL · docs/operations/north-star-metric-query.sql
- [snapog-og-image-service](snapog-og-image-service.md) — SnapOG OG Image Service · projects/_archive/snapog/migrations/0001_init.sql, projects/_archive/snapog/migrations/0002_waitlist.sql, projects/_archive/snapog/migrations/0003_cache_key_tracking.sql, projects/_archive/snapog/src/index.ts, projects/_archive/snapog/src/og/render.ts, projects/_archive/snapog/src/og/templates.ts, projects/_archive/snapog/src/types.ts
- [snapog-smoke-tests](snapog-smoke-tests.md) — SnapOG Smoke Tests · projects/_archive/snapog/sample/alerts-dry-run.sh, projects/_archive/snapog/sample/cache-cap-test.sh, projects/_archive/snapog/sample/smoke-test.sh
- [spending-control-and-budget-gates](spending-control-and-budget-gates.md) — spending control and budget gates · scripts/core/auto-loop.sh, scripts/ops/turn-audit.py, tests/test_dashboard_server.py, tests/test_discretionary_budget.sh, tests/test_tier_ladder_daily.sh
- [state-snapshot-and-delta](state-snapshot-and-delta.md) — state snapshot and DELTA · scripts/ops/state-snapshot.py, tests/test_state_snapshot.sh
- [state-snapshot-py-probe](state-snapshot-py-probe.md) — state-snapshot.py probe · scripts/ops/state-snapshot.py
- [telegram-notification-channel](telegram-notification-channel.md) — Telegram Notification Channel · scripts/core/telegram-notify.sh, scripts/ops/bloat-trend.py, scripts/ops/directive-staleness-watch.py, scripts/ops/docker-prune-safe.sh, scripts/ops/operator-action-router.py
- [tool-usage-audit](tool-usage-audit.md) — tool usage audit · scripts/ops/tool-usage-audit.py, tests/test_tool_usage_audit.sh
- [turn-bloat-brake-py-escalation](turn-bloat-brake-py-escalation.md) — turn-bloat-brake.py escalation · scripts/ops/turn-bloat-brake.py
- [turn-economy-and-bloat-control](turn-economy-and-bloat-control.md) — turn economy and bloat control · scripts/ops/turn-audit.py, scripts/ops/turn-bloat-brake.py, tests/test_turn_audit.sh, tests/test_turn_bloat_brake.py
- [turn-economy-bloat-monitoring](turn-economy-bloat-monitoring.md) — Turn-Economy & Bloat Monitoring · scripts/ops/bloat-trend.py, scripts/ops/context7-check.py
- [waitlist-capture](waitlist-capture.md) — Waitlist Capture · projects/_archive/snapog-landing/functions/api/waitlist.ts
- [work-window-brake](work-window-brake.md) — work window brake · scripts/ops/work-window-watchdog.py, scripts/ops/work-window.py, tests/test_work_window_watchdog.py, tests/test_work_window.py
- [work-window-brake-watchdog](work-window-brake-watchdog.md) — Work-window brake & watchdog · scripts/ops/work-window-watchdog.py, scripts/ops/work-window.py
- [wowcar-revenue-relabel-acceptance](wowcar-revenue-relabel-acceptance.md) — Wowcar revenue relabel acceptance · scripts/ops/wowcar-revenue-vocabulary-acceptance.py
- [wowcar-revenue-vocabulary](wowcar-revenue-vocabulary.md) — WowCar revenue vocabulary · scripts/ops/wowcar-revenue-vocabulary-acceptance.py, tests/test_wowcar_revenue_vocabulary_acceptance.sh
- [wsl-daemon-management](wsl-daemon-management.md) — WSL daemon management · scripts/wsl/install-wsl-daemon.sh, scripts/wsl/uninstall-wsl-daemon.sh, scripts/wsl/wsl-daemon-status.sh

## Files

87 per-file wiring cards mirror the source tree under `graft/` (85 carry extracted symbols). They are deliberately not enumerated here —
`grep` a symbol or `find`/`ls` a filename under `graft/` to land on the card for that file.
