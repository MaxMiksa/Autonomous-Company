# graft — repo map

Small markdown nodes summarising this repo. `grep` any term, symbol, or
filename here, or run `graft ask "<task>"`. Each node carries prose plus exact
`file:line`; open a source file only to edit the named span.

The same graph is queryable as MCP tools (`graft_find_code`, `graft_find_all`,
`graft_trace_calls`, `graft_file_api`, `graft_repo_map`) where a host exposes them, and
as the `graft` CLI everywhere else. Edges — who calls what — live only in the
graph, not in these files: `graft callers <symbol>` is the only way to read them.

## Concepts

- [airtable-access-wrappers](airtable-access-wrappers.md) — Airtable Access Wrappers · tests/test_airtable_read.sh, tests/test_airtable_write.sh
- [airtable-linear-external-integrations](airtable-linear-external-integrations.md) — Airtable & Linear external integrations · scripts/ops/airtable-read.py, scripts/ops/airtable-write.py, scripts/ops/linear-track.py
- [analyst-engine-plumbing](analyst-engine-plumbing.md) — Analyst Engine Plumbing · tests/test_analyst_engine.sh
- [auto-company-container-entrypoint](auto-company-container-entrypoint.md) — Auto Company Container Entrypoint · docker-entrypoint.sh
- [auto-company-loop-orchestration](auto-company-loop-orchestration.md) — Auto Company loop orchestration · scripts/core/monitor.sh, scripts/core/stop-loop.sh, scripts/linux/noop-action.sh, scripts/linux/status-linux.sh, scripts/macos/install-daemon.sh, scripts/macos/status-mac.sh
- [auto-company-site-pages](auto-company-site-pages.md) — Auto Company Site Pages · projects/auto-company-site/functions/listeden-cik.js, projects/auto-company-site/functions/randevu.js
- [auto-loop-core-engine](auto-loop-core-engine.md) — auto-loop core engine · scripts/core/auto-loop.sh, tests/test_cycle_counter.sh, tests/test_cycle_metadata.sh, tests/test_discretionary_budget.sh, tests/test_escalation.sh, tests/test_idle_skip.sh, tests/test_mixed_harness.sh, tests/test_prompt_assembly.sh, tests/test_prompt_transport.sh, tests/test_seteshape_lint.py, tests/test_tier_ladder_daily.sh
- [autonomous-loop-orchestrator](autonomous-loop-orchestrator.md) — Autonomous Loop Orchestrator · scripts/core/auto-loop.sh
- [bridge-leak-scanner](bridge-leak-scanner.md) — Bridge Leak Scanner · scripts/core/bridge_leak_scan.py
- [browser-automation](browser-automation.md) — Browser Automation · scripts/ops/browse-extract.py, scripts/ops/site-contact-evidence.py, tests/test_browse_extract.sh
- [browser-web-extraction](browser-web-extraction.md) — Browser & web extraction · scripts/ops/browse-extract.py
- [cockpit-dashboard](cockpit-dashboard.md) — Cockpit Dashboard · dashboard/app.js, dashboard/sentry_client.py, dashboard/server.py
- [compact-ritual](compact-ritual.md) — Compact Ritual · scripts/compact_yol.py, tests/test_compact_anchor_sync.py, tests/test_compact_ritual_hardening.sh, tests/test_compact_yol.py
- [compact-ritual-tooling](compact-ritual-tooling.md) — Compact Ritual Tooling · scripts/compact_yol.py, scripts/compact-postcheck.py, scripts/compact-preflight.py, scripts/compact-report.py, scripts/compact-resume-lint.py
- [compliance-evidence-checks](compliance-evidence-checks.md) — Compliance & evidence checks · scripts/ops/context7-check.py, scripts/ops/extract-axis-evidence.py
- [consensus-ledger-pruning](consensus-ledger-pruning.md) — Consensus & Ledger Pruning · scripts/ops/consensus-prune.py, tests/test_auto_loop_consensus_prune.sh, tests/test_consensus_prune.py
- [consensus-registry-maintenance](consensus-registry-maintenance.md) — Consensus & registry maintenance · scripts/ops/consensus-prune.py, scripts/ops/idle-skip-note.py, scripts/ops/ledger-guard.py, scripts/ops/registry-archive.py
- [container-host-operations](container-host-operations.md) — Container & host operations · scripts/core/sentry-heartbeat.sh, scripts/ops/docker-prune-safe.sh, scripts/ops/operator-usage-report.sh, scripts/ops/opportunity-analyst-cron.sh
- [content-hash-provenance](content-hash-provenance.md) — Content-hash provenance · scripts/core/decision_text_hash.py, scripts/ops/kik-decision-read.py
- [context-watch-hook](context-watch-hook.md) — Context Watch Hook · scripts/context-watch.py
- [context7-docs-wrapper](context7-docs-wrapper.md) — Context7 Docs Wrapper · scripts/analyst/codex-skill/autocompany-opportunity-director/scripts/context7_docs.sh
- [context7-tool-surface-auditing](context7-tool-surface-auditing.md) — Context7 & Tool-Surface Auditing · scripts/ops/context7-check.py, scripts/ops/cost-audit.py, tests/test_context7_check.sh, tests/test_cost_audit_tool_surface.py
- [cost-budget-accounting](cost-budget-accounting.md) — Cost & budget accounting · scripts/core/engine-usage-cost.py, scripts/ops/bloat-trend.py, scripts/ops/budget-calibration-report.py, scripts/ops/cost-audit.py
- [cycle-cost-risk-auditing](cycle-cost-risk-auditing.md) — Cycle Cost & Risk Auditing · scripts/ops/tool-usage-audit.py, scripts/ops/turn-audit.py, scripts/ops/turn-bloat-brake.py, scripts/ops/web-research-cost.py
- [cycle-metadata-cost-attribution](cycle-metadata-cost-attribution.md) — cycle metadata & cost attribution · tests/test_cycle_counter.sh, tests/test_cycle_metadata.sh, tests/test_mixed_harness.sh
- [dashboard-server](dashboard-server.md) — dashboard server · dashboard/server.py, tests/test_dashboard_server.py
- [directive-governance-staleness](directive-governance-staleness.md) — Directive governance & staleness · scripts/core/directive_writer.py, scripts/ops/directive-rule-sweep.py, scripts/ops/directive-staleness-watch.py
- [directive-promotion-gate](directive-promotion-gate.md) — Directive Promotion Gate · scripts/analyst/promote_directive.py
- [directive-writer](directive-writer.md) — Directive Writer · scripts/core/directive_writer.py, tests/test_directive_section_refs.sh, tests/test_directive_writer.py
- [engine-usage-cost-model-hint](engine-usage-cost-model-hint.md) — engine-usage-cost model hint · tests/test_cost_model_hint.sh
- [escalation-directive-gating](escalation-directive-gating.md) — escalation & directive gating · tests/test_directive_section_refs.sh, tests/test_directive_writer.py, tests/test_escalation.sh
- [fail-closed-eligibility-gates](fail-closed-eligibility-gates.md) — Fail-Closed Eligibility Gates · scripts/ops/rfq-send.py, scripts/ops/send-gate.py
- [final-text-extraction](final-text-extraction.md) — Final-text extraction · scripts/core/codex-final-text.py, scripts/core/jcode-final-text.py
- [g4-address-matching](g4-address-matching.md) — G4 address matching · scripts/ops/g4-check.py, tests/test_g4_check.sh
- [g4-attribution-evidence](g4-attribution-evidence.md) — G4 Attribution Evidence · scripts/ops/site-contact-evidence.py
- [g4-identity-verification](g4-identity-verification.md) — G4 identity verification · scripts/ops/g4-check.py
- [graft-card-refresh](graft-card-refresh.md) — Graft card refresh · scripts/graft-auto-refresh.py
- [harness-loop-core](harness-loop-core.md) — Harness Loop Core · tests/test_active_window.sh, tests/test_auto_loop_consensus_prune.sh, tests/test_auto_loop_ledger_guard.sh, tests/test_auto_loop_work_window.sh, tests/test_budget_gates.sh, tests/test_ccusage_failclosed.sh, tests/test_codex_spend_sources.sh
- [headinspect-header-inspector](headinspect-header-inspector.md) — HeadInspect Header Inspector · projects/headinspect/migrations/0001_hits.sql, projects/headinspect/src/index.ts, projects/headinspect/src/inspect.ts, projects/headinspect/src/render.ts
- [headinspect-privacy-constraint](headinspect-privacy-constraint.md) — HeadInspect Privacy Constraint · projects/headinspect/migrations/0001_hits.sql
- [human-directive-write-path](human-directive-write-path.md) — Human directive write path · scripts/core/directive_writer.py
- [jcode-pilot-smoke-test](jcode-pilot-smoke-test.md) — jcode Pilot Smoke Test · scripts/analyst/jcode-pilot-smoke.sh
- [ki-k-decision-reading](ki-k-decision-reading.md) — KİK decision reading · scripts/ops/kik-decision-read.py
- [ledger-audit-guards](ledger-audit-guards.md) — ledger & audit guards · scripts/ops/ledger-guard.py, scripts/ops/tool-usage-audit.py, scripts/ops/turn-audit.py, scripts/ops/turn-bloat-brake.py, tests/test_ledger_guard.py, tests/test_tool_usage_audit.sh, tests/test_turn_audit.sh, tests/test_turn_bloat_brake.py
- [mcp-config-key-handling](mcp-config-key-handling.md) — MCP config & key handling · scripts/core/jcode-mcp-config.py, scripts/core/jcode-mcp-probe.py, tests/test_jcode_mcp_config.sh, tests/test_mcp_config_manifest_sync.sh, tests/test_mcp_key_fallback.sh, tests/test_mcp_probe.sh
- [mcp-configuration-boot-probe](mcp-configuration-boot-probe.md) — MCP configuration & boot probe · scripts/core/jcode-mcp-config.py, scripts/core/jcode-mcp-probe.py
- [mcp-key-server-verification](mcp-key-server-verification.md) — MCP Key & Server Verification · scripts/ops/verify-mcp-keys.py, tests/fixtures/mock_mcp_server.py
- [mcp-probe-invariants](mcp-probe-invariants.md) — MCP probe invariants · tests/test_mcp_probe.sh
- [operator-action-router](operator-action-router.md) — operator action router · scripts/ops/operator-action-router.py, tests/test_operator_action_router.py
- [operator-alerting-watchers](operator-alerting-watchers.md) — Operator Alerting Watchers · scripts/ops/registry-queue-watch.py, scripts/ops/reply-watch.py, scripts/ops/rfq-reply-watch.py
- [operator-notification-escalation](operator-notification-escalation.md) — Operator notification & escalation · scripts/core/operator_request_notify.py, scripts/core/telegram-notify.sh, scripts/ops/directive-staleness-watch.py, scripts/ops/operator-action-router.py
- [operator-request-resolution](operator-request-resolution.md) — operator request resolution · scripts/core/operator_request_notify.py, tests/test_operator_request_notify.py, tests/test_refusal_format.sh
- [opportunity-analyst](opportunity-analyst.md) — Opportunity Analyst · scripts/analyst/merge_registry.py, scripts/analyst/opportunity-analyst-jcode.sh, scripts/analyst/opportunity-analyst.sh, scripts/analyst/promote_directive.py
- [outcome-queue-watchers](outcome-queue-watchers.md) — outcome & queue watchers · scripts/ops/registry-archive.py, scripts/ops/registry-queue-watch.py, scripts/ops/reply-watch.py, scripts/ops/rfq-reply-watch.py, tests/test_registry_archive.sh, tests/test_registry_queue_watch.sh, tests/test_reply_watch.sh, tests/test_rfq_reply_watch.sh
- [prod-mechanism-guard](prod-mechanism-guard.md) — prod-mechanism guard · scripts/prod-mechanism-guard.py, tests/test_prod_mechanism_guard.sh
- [production-surface-guard](production-surface-guard.md) — Production Surface Guard · scripts/prod-mechanism-guard.py
- [prompt-md-guardrail-budget](prompt-md-guardrail-budget.md) — PROMPT.md guardrail budget · tests/test_prompt_guardrails.sh
- [prompt-transport-contract](prompt-transport-contract.md) — prompt transport contract · tests/test_prompt_assembly.sh, tests/test_prompt_guardrails.sh, tests/test_prompt_transport.sh
- [registry-merge-invariants](registry-merge-invariants.md) — Registry Merge Invariants · scripts/analyst/merge_registry.py
- [rfq-email-pipeline](rfq-email-pipeline.md) — RFQ Email Pipeline · scripts/ops/rfq_template.py, scripts/ops/rfq-reply-watch.py, scripts/ops/rfq-send.py
- [runtime-environment-secrets](runtime-environment-secrets.md) — Runtime environment & secrets · scripts/core/directive_writer.py, scripts/ops/airtable-read.py, scripts/ops/airtable-write.py, scripts/ops/docker-prune-safe.sh, scripts/ops/linear-track.py, scripts/ops/operator-action-router.py, scripts/ops/operator-usage-report.sh
- [send-gate-outreach-policy](send-gate-outreach-policy.md) — send-gate & outreach policy · scripts/ops/rfq-send.py, scripts/ops/send-gate.py, tests/test_rfq_send.sh, tests/test_send_gate.sh
- [session-brief-hook](session-brief-hook.md) — Session Brief Hook · scripts/session-brief.py
- [site-contact-evidence](site-contact-evidence.md) — Site contact evidence · scripts/ops/g4-check.py
- [snapog-cache-cap-abuse-prevention](snapog-cache-cap-abuse-prevention.md) — SnapOG Cache-Cap Abuse Prevention · projects/_archive/snapog/migrations/0003_cache_key_tracking.sql, projects/_archive/snapog/sample/cache-cap-test.sh, projects/_archive/snapog/src/index.ts, projects/_archive/snapog/src/og/render.ts, projects/_archive/snapog/src/types.ts
- [snapog-cost-alerting](snapog-cost-alerting.md) — SnapOG Cost Alerting · projects/_archive/snapog/src/alerts/check.ts, projects/_archive/snapog/src/alerts/graphql.ts, projects/_archive/snapog/src/alerts/index.ts, projects/_archive/snapog/src/alerts/thresholds.ts, projects/_archive/snapog/src/alerts/webhook.ts
- [snapog-d1-schema](snapog-d1-schema.md) — SnapOG D1 Schema · projects/_archive/snapog/migrations/0001_init.sql, projects/_archive/snapog/migrations/0002_waitlist.sql, projects/_archive/snapog/migrations/0003_cache_key_tracking.sql
- [snapog-landing-waitlist](snapog-landing-waitlist.md) — SnapOG Landing & Waitlist · projects/_archive/snapog/src/dashboard/pages.ts, projects/_archive/snapog/src/index.ts, projects/_archive/snapog/src/og/render.ts, projects/_archive/snapog/src/og/templates.ts, projects/_archive/snapog/src/types.ts
- [snapog-north-star-metric](snapog-north-star-metric.md) — SnapOG North-Star Metric · docs/operations/north-star-metric-query.sql
- [snapog-og-image-service](snapog-og-image-service.md) — SnapOG OG Image Service · projects/_archive/snapog/src/dashboard/pages.ts, projects/_archive/snapog/src/index.ts, projects/_archive/snapog/src/og/render.ts, projects/_archive/snapog/src/og/templates.ts, projects/_archive/snapog/src/types.ts
- [snapog-smoke-tests](snapog-smoke-tests.md) — SnapOG Smoke Tests · projects/_archive/snapog/sample/alerts-dry-run.sh, projects/_archive/snapog/sample/cache-cap-test.sh, projects/_archive/snapog/sample/smoke-test.sh
- [state-snapshot-staleness](state-snapshot-staleness.md) — state snapshot & staleness · scripts/ops/staleness-report.py, scripts/ops/state-snapshot.py, tests/test_staleness_report.py, tests/test_state_snapshot.sh
- [state-staleness-measurement](state-staleness-measurement.md) — State & Staleness Measurement · scripts/ops/staleness-report.py, scripts/ops/state-snapshot.py
- [telegram-notification-core](telegram-notification-core.md) — Telegram Notification Core · scripts/ops/registry-queue-watch.py, scripts/ops/reply-watch.py, scripts/ops/rfq-reply-watch.py, scripts/ops/turn-bloat-brake.py, scripts/ops/work-window-watchdog.py
- [work-window-brake](work-window-brake.md) — Work-Window Brake · scripts/ops/work-window-watchdog.py, scripts/ops/work-window.py
- [work-window-watchdog-brakes](work-window-watchdog-brakes.md) — work-window & watchdog brakes · scripts/ops/idle-skip-note.py, scripts/ops/work-window-watchdog.py, scripts/ops/work-window.py, tests/test_idle_skip.sh, tests/test_work_window_watchdog.py, tests/test_work_window.py
- [wowcar-revenue-relabel-acceptance](wowcar-revenue-relabel-acceptance.md) — Wowcar Revenue Relabel Acceptance · scripts/ops/wowcar-revenue-vocabulary-acceptance.py
- [wowcar-revenue-vocabulary](wowcar-revenue-vocabulary.md) — WowCar revenue vocabulary · scripts/ops/wowcar-revenue-vocabulary-acceptance.py, tests/test_wowcar_revenue_vocabulary_acceptance.sh
- [wsl-daemon-management](wsl-daemon-management.md) — WSL Daemon Management · scripts/wsl/install-wsl-daemon.sh, scripts/wsl/uninstall-wsl-daemon.sh, scripts/wsl/wsl-daemon-status.sh

## Files

89 per-file wiring cards mirror the source tree under `graft/` (87 carry extracted symbols). They are deliberately not enumerated here —
`grep` a symbol or `find`/`ls` a filename under `graft/` to land on the card for that file.
