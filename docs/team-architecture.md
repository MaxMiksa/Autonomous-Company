# Team Architecture — departments, gate map, role-file standard

Role files in `.claude/agents/` are authoritative; this file is the human-readable map.
Rewritten 2026-10-16 for plan v4.1 B5 (sponsor S2 + S3, operator K-2).

## How roles reach a loop cycle (Path B)

The jcode loop does not load `.claude/agents/*` as sub-agents, its skill tool does not see
`.claude/skills/`, and `swarm` spawns no workers headless (measured, A0.2, 2026-10-16).
One model plays every role. A role therefore acts only as a **checklist the harness
injects**: for a work card's gate, `scripts/ops/role-checklist.py render --card <card>`
prints the `## Gate Checklist` of each active role mapped to that gate (≤1 KB, priority
order), and the independent reviewer scores the same items against the card's evidence.
Interactive Claude Code sessions can still use the files as sub-agents.

## Departments and gate map

Gates: G0 document integrity · G1 legal feasibility · G2 commercial/financial validation ·
G3 operations/system design · G4 build+UAT · G5 funding readiness · G6 controlled pilot ·
G7 scale.

| Department | Role file | Gates | Priority | Output dir |
|---|---|---|---|---|
| Management | `ceo-bezos` | G2, G5, G7 | 3 | `docs/ceo/` |
| Management | `chief-of-staff` (new) | none — weekly brief | 9 | `docs/chief-of-staff/` |
| Finance | `cfo-campbell` | G0, G2, G5 | 2 | `docs/cfo/` |
| Finance | `reconciliation-controller` (new) | G0, G2 | 2 | `docs/reconciliation/` |
| Legal & Compliance | `compliance-officer` (new) | G1, G5, G6 | 2 | `docs/compliance/` |
| Legal & Compliance | `kvkk-dpo` (new) | G1, G3, G6 | 3 | `docs/kvkk/` |
| Operations | `operations-pg` | G3, G6, G7 | 2 | `docs/operations/` |
| Operations | `interaction-cooper` | G3 | 4 | `docs/interaction/` |
| Quality | `critic-munger` | G0–G7 | 1 | `docs/critic/` |
| Quality | `qa-bach` | G4, G6 | 2 | `docs/qa/` |
| Technology | `cto-vogels` | G3, G7 | 3 | `docs/cto/` |
| Technology | `fullstack-dhh` | G4 | 3 | `docs/fullstack/` |
| Technology | `devops-hightower` | G4, G7 | 4 | `docs/devops/` |
| Technology | `security-architect` (new) | G3, G4 | 3 | `docs/security/` |
| Research | `research-thompson` | G0, G1 | 2 | `docs/research/` |
| Dormant | `marketing-godin`, `sales-ross`, `ui-duarte`, `product-norman` | none | — | unchanged |

19 role files: 15 active, 4 dormant (S2: dormant files stay, they leave cycle selection).
`critic-munger` maps to every gate: its review is mandatory before any gate-pass claim.
A card may name its roles explicitly (`roles` field); otherwise the gate map applies.

Shadow organization (the human owner of each department in the real company): sponsor —
CEO approval and every directive §15 act; Yasin (puratu1) — CRM and technology; SMMM —
accounting and tax; law office — new legal questions; bank(s) — funding.

## Role-file standard

Adapted from msitarzewski/agency-agents (MIT, © 2025 AgentLand Contributors), nine-section
agent structure, plus two loop sections. Enforced by
`python3 scripts/ops/role-checklist.py check` and `tests/test_role_files.py`.

- Frontmatter: `name` (= file stem), `description` (one line: when to use), `model: inherit`.
  A dormant role's description starts with `DORMANT`.
- H2 sections, exactly in this order: Identity & Memory · Core Mission · Critical Rules ·
  Deliverables · Workflow · Communication Style · Learning & Memory · Success Metrics ·
  Advanced Capabilities · Gate Checklist · Loop Metadata.
- **English only** (operator K-2): instructions to the company are English; no CJK, no
  Turkish letters (Turkish terms are transliterated and glossed, e.g. `temlik (assignment)`).
  What the company PRODUCES follows the OUTPUT LANGUAGE section of `PROMPT.md`.
- **Gate Checklist:** 2–4 bullets, ≤280 bytes together; each bullet is checkable against an
  evidence entry (a file + sha, a record id, a quoted clause) — never an attitude.
- **Success Metrics:** ≥2 measurable bullets bound to VADEA work, not generic startup KPIs.
- **Loop Metadata:** bullets `status` (active|dormant), `department`, `gates` (comma list or
  `none`), `checklist_priority` (1 = injected first), `docs_dir`.
- No numbers restated from sponsor rules or source documents: cite the source file and
  location instead (numbers drift; the source does not).
- Keep each file ≤7 KB; persona flavour stays one paragraph.

## Historical — Tender/discovery-era workflows (moved from CLAUDE.md 2026-08-24)

Retired by the Wowcar 2.0 re-charter; kept for the record:

1. New Product Evaluation: research-thompson → ceo-bezos → critic-munger → product-norman → cto-vogels → cfo-campbell
2. Feature Development: interaction-cooper → ui-duarte → fullstack-dhh → qa-bach → devops-hightower
3. Product Launch: qa-bach → devops-hightower → marketing-godin → sales-ross → operations-pg → ceo-bezos
4. Pricing and Monetization: research-thompson → cfo-campbell → sales-ross → critic-munger → ceo-bezos
5. Weekly Review: operations-pg → sales-ross → cfo-campbell → qa-bach → ceo-bezos
6. Opportunity Discovery: research-thompson → ceo-bezos → critic-munger → cfo-campbell

Workflows 1 and 6 ran through `PROJECT_EVALUATION_FRAMEWORK.md` (dormant archive).
