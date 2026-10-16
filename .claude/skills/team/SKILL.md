---
name: team
description: "Assemble a temporary team of role agents from .claude/agents/ for one task (interactive sessions only; the jcode loop uses injected role checklists instead)."
argument-hint: "[task description]"
disable-model-invocation: true
---

# Assemble a temporary team

Pick the smallest set of roles that covers the task below and run them as a temporary team.

## Task

$ARGUMENTS

## Active roles

Authoritative map: `docs/team-architecture.md` (departments, gates, output directories).

| Department | Role file | Use for |
|---|---|---|
| Management | `ceo-bezos` | final internal decision, priorities, decision records |
| Management | `chief-of-staff` | weekly sponsor brief, decision log, document dependency sync |
| Finance | `cfo-campbell` | financial model, unit economics, funding readiness, collateral structure |
| Finance | `reconciliation-controller` | source/model/CRM reconciliation, variance, instalment formula check |
| Legal & Compliance | `compliance-officer` | obligation matrix (TKHK, BDDK, MASAK), counsel-or-not decision |
| Legal & Compliance | `kvkk-dpo` | KVKK data map, lawful basis, retention, breach plan |
| Operations | `operations-pg` | SOPs, runbooks, RACI, weekly report |
| Operations | `interaction-cooper` | CRM staff and customer flows, flow-based CRM requirements |
| Quality | `critic-munger` | contrarian review — REQUIRED before any gate-pass claim |
| Quality | `qa-bach` | test strategy, acceptance tests, CRM UAT |
| Technology | `cto-vogels` | system architecture, CRM requirement packages |
| Technology | `fullstack-dhh` | internal tools, checkers, scripts with tests |
| Technology | `devops-hightower` | product deploys (Cloudflare), verification, infrastructure hygiene |
| Technology | `security-architect` | threat model, permissions/audit trail, tool allowlist, secrets |
| Research | `research-thompson` | primary-source legal, regulatory and market research |

Dormant (sponsor S2 — do not select unless the sponsor wakes them): `marketing-godin`,
`sales-ross`, `ui-duarte`, `product-norman`.

## Steps

1. **Select 2–5 roles.** Only the necessary ones; cover the hand-off chain; no overlapping
   roles. Add `critic-munger` whenever the result feeds a gate claim or a sponsor decision.
   Tell the operator in one line who you picked and why, then start.
2. **Run them.** Spawn each member with the Agent tool using its role file as `subagent_type`
   (or `general-purpose` with the full role file injected). Give each member the task, the
   context it needs, and its output directory from the role's Loop Metadata `docs_dir`.
3. **Merge.** Collect the outputs into one result; list disagreements side by side with the
   evidence for each; the operator (or `ceo-bezos` inside the loop) decides.

## Notes

- Instructions to role agents are English (operator K-2). The language of what they produce
  follows the OUTPUT LANGUAGE section of `PROMPT.md`.
- The team is temporary; dissolve it when the task is done.
- Every directive §15 act stays sponsor-gated; a team never authorizes one.
