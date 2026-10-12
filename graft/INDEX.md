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
- [airtable-scoped-access](airtable-scoped-access.md) — Airtable Scoped Access · scripts/ops/airtable-read.py, scripts/ops/airtable-write.py
- [analyst-engine-plumbing](analyst-engine-plumbing.md) — Analyst engine plumbing · tests/test_analyst_engine.sh
- [assistant-final-text-extraction](assistant-final-text-extraction.md) — Assistant Final-Text Extraction · scripts/core/codex-final-text.py, scripts/core/jcode-final-text.py
- [auto-company-loop-orchestration](auto-company-loop-orchestration.md) — Auto Company Loop Orchestration · scripts/core/monitor.sh, scripts/core/stop-loop.sh, scripts/linux/noop-action.sh, scripts/linux/status-linux.sh, scripts/macos/install-daemon.sh, scripts/macos/status-mac.sh
- [auto-company-site-pages-functions](auto-company-site-pages-functions.md) — Auto-Company Site Pages Functions · projects/auto-company-site/functions/listeden-cik.js, projects/auto-company-site/functions/randevu.js
- [auto-loop-core-engine](auto-loop-core-engine.md) — auto-loop core engine · scripts/core/auto-loop.sh
- [auto-loop-harness](auto-loop-harness.md) — Auto-loop harness · tests/test_active_window.sh, tests/test_auto_loop_consensus_prune.sh, tests/test_auto_loop_ledger_guard.sh, tests/test_auto_loop_work_window.sh, tests/test_budget_gates.sh, tests/test_ccusage_failclosed.sh, tests/test_codex_spend_sources.sh
- [auto-loop-orchestration](auto-loop-orchestration.md) — Auto Loop Orchestration · scripts/core/auto-loop.sh
- [bridge-leak-scanner](bridge-leak-scanner.md) — Bridge Leak Scanner · scripts/core/bridge_leak_scan.py
- [browse-extract-mcp-gateway-client](browse-extract-mcp-gateway-client.md) — browse-extract MCP gateway client · tests/test_browse_extract.sh
- [browser-extraction-harness](browser-extraction-harness.md) — Browser Extraction Harness · scripts/ops/browse-extract.py
- [cockpit-dashboard](cockpit-dashboard.md) — Cockpit Dashboard · dashboard/app.js, dashboard/sentry_client.py, dashboard/server.py
- [compact-ritual-path-resolution](compact-ritual-path-resolution.md) — Compact ritual path resolution · scripts/compact_yol.py, tests/test_compact_anchor_sync.py, tests/test_compact_ritual_hardening.sh, tests/test_compact_yol.py
- [compact-ritual-tooling](compact-ritual-tooling.md) — Compact Ritual Tooling · scripts/compact_yol.py, scripts/compact-postcheck.py, scripts/compact-preflight.py, scripts/compact-report.py, scripts/compact-resume-lint.py
- [consensus-document-pruning](consensus-document-pruning.md) — Consensus document pruning · tests/test_auto_loop_consensus_prune.sh, tests/test_consensus_prune.py
- [consensus-memory-management](consensus-memory-management.md) — Consensus Memory Management · scripts/ops/consensus-prune.py, scripts/ops/idle-skip-note.py, scripts/ops/ledger-guard.py, scripts/ops/registry-archive.py
- [container-entrypoint-boot](container-entrypoint-boot.md) — Container Entrypoint & Boot · docker-entrypoint.sh
- [content-hash-provenance](content-hash-provenance.md) — Content-Hash Provenance · scripts/core/decision_text_hash.py, scripts/ops/kik-decision-read.py
- [context-watch-hook](context-watch-hook.md) — Context Watch Hook · scripts/context-watch.py
- [context7-compliance-check](context7-compliance-check.md) — Context7 Compliance Check · scripts/ops/context7-check.py
- [context7-import-audit](context7-import-audit.md) — Context7 import audit · tests/test_context7_check.sh
- [cost-audit-tool-surface](cost-audit-tool-surface.md) — Cost-audit tool surface · tests/test_cost_audit_tool_surface.py
- [cost-budget-accounting](cost-budget-accounting.md) — Cost & Budget Accounting · scripts/core/engine-usage-cost.py, scripts/ops/budget-calibration-report.py, scripts/ops/cost-audit.py
- [cycle-cost-risk-audit](cycle-cost-risk-audit.md) — Cycle cost & risk audit · scripts/ops/tool-usage-audit.py, scripts/ops/turn-audit.py, scripts/ops/web-research-cost.py
- [cycle-metadata-extraction](cycle-metadata-extraction.md) — cycle metadata extraction · scripts/core/auto-loop.sh, scripts/core/codex-final-text.py, tests/test_cycle_metadata.sh
- [dashboard-server](dashboard-server.md) — dashboard server · dashboard/server.py, tests/test_dashboard_server.py
- [directive-promotion-gate](directive-promotion-gate.md) — Directive Promotion Gate · scripts/analyst/promote_directive.py
- [directive-writer-gate](directive-writer-gate.md) — Directive Writer Gate · dashboard/server.py, scripts/analyst/opportunity-analyst-jcode.sh, scripts/analyst/opportunity-analyst.sh
- [docker-disk-guard](docker-disk-guard.md) — Docker Disk Guard · scripts/ops/docker-prune-safe.sh
- [docker-entrypoint](docker-entrypoint.md) — docker-entrypoint · docker-entrypoint.sh
- [engine-usage-cost-adapter](engine-usage-cost-adapter.md) — Engine usage cost adapter · tests/test_cost_model_hint.sh
- [escalation-directive-system](escalation-directive-system.md) — escalation & directive system · scripts/core/auto-loop.sh, scripts/core/directive_writer.py, tests/test_directive_section_refs.sh, tests/test_escalation.sh
- [evidence-extraction-validation](evidence-extraction-validation.md) — Evidence Extraction & Validation · scripts/ops/directive-rule-sweep.py, scripts/ops/extract-axis-evidence.py
- [g4-attribution-evidence](g4-attribution-evidence.md) — G4 attribution evidence · scripts/ops/site-contact-evidence.py
- [g4-compliance-checks](g4-compliance-checks.md) — G4 compliance checks · scripts/ops/g4-check.py, tests/test_g4_check.sh
- [g4-identity-verification](g4-identity-verification.md) — G4 Identity Verification · scripts/ops/g4-check.py
- [graft-card-refresh](graft-card-refresh.md) — Graft Card Refresh · scripts/graft-auto-refresh.py
- [headinspect-header-inspector](headinspect-header-inspector.md) — HeadInspect Header Inspector · projects/headinspect/migrations/0001_hits.sql, projects/headinspect/src/index.ts, projects/headinspect/src/inspect.ts, projects/headinspect/src/render.ts
- [human-directive-lifecycle](human-directive-lifecycle.md) — Human Directive Lifecycle · scripts/core/directive_writer.py, scripts/ops/directive-rule-sweep.py, scripts/ops/directive-staleness-watch.py
- [idle-skip-mechanism](idle-skip-mechanism.md) — idle-skip mechanism · scripts/core/auto-loop.sh, scripts/ops/idle-skip-note.py, tests/test_idle_skip.sh
- [jcode-pilot-smoke-test](jcode-pilot-smoke-test.md) — jcode Pilot Smoke Test · scripts/analyst/jcode-pilot-smoke.sh
- [ki-k-decision-evidence-pipeline](ki-k-decision-evidence-pipeline.md) — KİK Decision Evidence Pipeline · scripts/core/decision_text_hash.py, scripts/ops/kik-decision-read.py
- [ledger-guard-state-integrity](ledger-guard-state-integrity.md) — ledger guard & state integrity · scripts/ops/ledger-guard.py, scripts/ops/state-snapshot.py, tests/test_ledger_guard.py, tests/test_state_snapshot.sh
- [linear-workstream-discipline](linear-workstream-discipline.md) — Linear Workstream Discipline · scripts/ops/linear-track.py
- [mcp-boot-probe-config](mcp-boot-probe-config.md) — MCP Boot Probe & Config · scripts/core/jcode-mcp-config.py, scripts/core/jcode-mcp-probe.py
- [mcp-config-probe-system](mcp-config-probe-system.md) — MCP config & probe system · scripts/core/jcode-mcp-config.py, scripts/core/jcode-mcp-probe.py, tests/test_jcode_mcp_config.sh, tests/test_mcp_config_manifest_sync.sh, tests/test_mcp_key_fallback.sh, tests/test_mcp_probe.sh
- [mcp-key-fallback](mcp-key-fallback.md) — MCP key fallback · tests/test_mcp_key_fallback.sh
- [mcp-key-verification](mcp-key-verification.md) — MCP key verification · scripts/ops/verify-mcp-keys.py
- [mock-mcp-server-fixture](mock-mcp-server-fixture.md) — Mock MCP server fixture · tests/fixtures/mock_mcp_server.py
- [operator-alerting-watchers](operator-alerting-watchers.md) — Operator alerting watchers · scripts/ops/registry-queue-watch.py, scripts/ops/reply-watch.py, scripts/ops/rfq-reply-watch.py
- [operator-escalation-gate](operator-escalation-gate.md) — Operator Escalation Gate · scripts/core/operator_request_notify.py, scripts/ops/operator-action-router.py
- [operator-notification-channel](operator-notification-channel.md) — Operator Notification Channel · scripts/core/sentry-heartbeat.sh, scripts/core/telegram-notify.sh
- [operator-request-notification-system](operator-request-notification-system.md) — operator request & notification system · scripts/core/operator_request_notify.py, scripts/ops/operator-action-router.py, tests/test_operator_action_router.py, tests/test_operator_request_notify.py, tests/test_refusal_format.sh
- [operator-usage-reporting](operator-usage-reporting.md) — Operator Usage Reporting · scripts/ops/operator-usage-report.sh
- [opportunity-analyst](opportunity-analyst.md) — Opportunity Analyst · scripts/analyst/codex-skill/autocompany-opportunity-director/scripts/context7_docs.sh, scripts/analyst/merge_registry.py, scripts/analyst/opportunity-analyst-jcode.sh, scripts/analyst/opportunity-analyst.sh, scripts/analyst/promote_directive.py
- [opportunity-analyst-cron](opportunity-analyst-cron.md) — Opportunity Analyst Cron · scripts/ops/opportunity-analyst-cron.sh
- [outreach-send-gate](outreach-send-gate.md) — outreach send gate · scripts/ops/send-gate.py, tests/test_send_gate.sh
- [prod-mechanism-guard](prod-mechanism-guard.md) — Prod-mechanism guard · scripts/prod-mechanism-guard.py, tests/test_prod_mechanism_guard.sh
- [prompt-assembly-guardrails](prompt-assembly-guardrails.md) — prompt assembly guardrails · scripts/core/auto-loop.sh, tests/test_prompt_assembly.sh
- [prompt-transport-contract](prompt-transport-contract.md) — prompt transport contract · scripts/core/auto-loop.sh, tests/test_prompt_transport.sh
- [registry-merge-invariants](registry-merge-invariants.md) — Registry Merge Invariants · scripts/analyst/merge_registry.py
- [registry-outreach-watchers](registry-outreach-watchers.md) — registry & outreach watchers · scripts/ops/registry-archive.py, scripts/ops/registry-queue-watch.py, scripts/ops/reply-watch.py, scripts/ops/rfq-reply-watch.py, tests/test_registry_archive.sh, tests/test_registry_queue_watch.sh, tests/test_reply_watch.sh, tests/test_rfq_reply_watch.sh
- [rfq-send-pipeline](rfq-send-pipeline.md) — RFQ send pipeline · scripts/ops/rfq_template.py, scripts/ops/rfq-send.py
- [rfq-sender](rfq-sender.md) — RFQ sender · scripts/ops/rfq-send.py, tests/test_rfq_send.sh
- [send-gate-py-eligibility-brake](send-gate-py-eligibility-brake.md) — send-gate.py eligibility brake · scripts/ops/send-gate.py
- [sentry-reporter](sentry-reporter.md) — Sentry Reporter · dashboard/sentry_client.py
- [session-brief-hook](session-brief-hook.md) — Session brief hook · scripts/session-brief.py
- [set-e-lint-invariant](set-e-lint-invariant.md) — set -e lint invariant · docker-entrypoint.sh, scripts/core/auto-loop.sh, tests/test_seteshape_lint.py
- [site-contact-evidence](site-contact-evidence.md) — Site Contact Evidence · scripts/ops/g4-check.py
- [snapog-cost-alerting](snapog-cost-alerting.md) — SnapOG Cost Alerting · projects/_archive/snapog/src/alerts/check.ts, projects/_archive/snapog/src/alerts/graphql.ts, projects/_archive/snapog/src/alerts/index.ts, projects/_archive/snapog/src/alerts/thresholds.ts, projects/_archive/snapog/src/alerts/webhook.ts
- [snapog-d1-schema](snapog-d1-schema.md) — SnapOG D1 Schema · projects/_archive/snapog/migrations/0001_init.sql, projects/_archive/snapog/migrations/0002_waitlist.sql, projects/_archive/snapog/migrations/0003_cache_key_tracking.sql
- [snapog-north-star-metric](snapog-north-star-metric.md) — SnapOG North-Star Metric · docs/operations/north-star-metric-query.sql
- [snapog-og-image-service](snapog-og-image-service.md) — SnapOG OG Image Service · projects/_archive/snapog/src/dashboard/pages.ts, projects/_archive/snapog/src/index.ts, projects/_archive/snapog/src/og/render.ts, projects/_archive/snapog/src/og/templates.ts, projects/_archive/snapog/src/types.ts
- [snapog-validation-scripts](snapog-validation-scripts.md) — SnapOG Validation Scripts · projects/_archive/snapog/sample/alerts-dry-run.sh, projects/_archive/snapog/sample/cache-cap-test.sh, projects/_archive/snapog/sample/smoke-test.sh
- [spending-control-budget-gates](spending-control-budget-gates.md) — spending control & budget gates · scripts/core/auto-loop.sh, scripts/ops/send-gate.py, tests/test_discretionary_budget.sh, tests/test_send_gate.sh, tests/test_tier_ladder_daily.sh
- [state-snapshot-py-probe](state-snapshot-py-probe.md) — state-snapshot.py probe · scripts/ops/state-snapshot.py
- [tool-surface-compliance](tool-surface-compliance.md) — Tool Surface Compliance · scripts/core/jcode-mcp-probe.py, scripts/ops/cost-audit.py
- [turn-bloat-brake-py-escalation](turn-bloat-brake-py-escalation.md) — turn-bloat-brake.py escalation · scripts/ops/turn-bloat-brake.py
- [turn-economy-audit](turn-economy-audit.md) — turn economy & audit · scripts/ops/tool-usage-audit.py, scripts/ops/turn-audit.py, scripts/ops/turn-bloat-brake.py, tests/test_tool_usage_audit.sh, tests/test_turn_audit.sh, tests/test_turn_bloat_brake.py
- [turn-economy-trend-watch](turn-economy-trend-watch.md) — Turn Economy Trend Watch · scripts/ops/bloat-trend.py
- [work-window-brake-watchdog](work-window-brake-watchdog.md) — Work-window brake & watchdog · scripts/ops/work-window-watchdog.py, scripts/ops/work-window.py
- [work-window-watchdog](work-window-watchdog.md) — work window & watchdog · scripts/ops/work-window-watchdog.py, scripts/ops/work-window.py, tests/test_work_window_watchdog.py, tests/test_work_window.py
- [wowcar-revenue-relabel-acceptance](wowcar-revenue-relabel-acceptance.md) — Wowcar revenue relabel acceptance · scripts/ops/wowcar-revenue-vocabulary-acceptance.py
- [wowcar-revenue-vocabulary](wowcar-revenue-vocabulary.md) — wowcar revenue vocabulary · scripts/ops/wowcar-revenue-vocabulary-acceptance.py, tests/test_wowcar_revenue_vocabulary_acceptance.sh
- [wsl-daemon-management](wsl-daemon-management.md) — WSL daemon management · scripts/wsl/install-wsl-daemon.sh, scripts/wsl/uninstall-wsl-daemon.sh, scripts/wsl/wsl-daemon-status.sh

## Files

86 per-file wiring cards mirror the source tree under `graft/` (84 carry extracted symbols). They are deliberately not enumerated here —
`grep` a symbol or `find`/`ls` a filename under `graft/` to land on the card for that file.
