# Software Delivery Phase 2 — Documentation Index (FIX 126)

Single entry point for the **frozen** governed software delivery loop (FIX 125A–125I).

---

## Warnings (read first)

```text
Do not skip workflow stages.
Do not bypass governed verification.
Do not couple software delivery lanes to infrastructure mutation lanes.
```

**Architectural invariant (certified):**

```text
software_delivery_lane != infrastructure_mutation_lane
```

---

## Certified workflow

```text
issue
→ implementation plan
→ governed branch
→ bounded patch proposal
→ governed workspace apply
→ workspace verification
→ PR draft
→ GitHub preflight
→ governed branch push
→ governed PR open
→ human review
```

---

## Core documents

| Document | Purpose |
|----------|---------|
| [SOFTWARE_DELIVERY_PHASE_2_CERTIFICATION_FREEZE.md](./SOFTWARE_DELIVERY_PHASE_2_CERTIFICATION_FREEZE.md) | Freeze scope, invariants, forbidden behavior |
| [SOFTWARE_DELIVERY_PHASE_2_OPERATOR_RUNBOOK.md](./SOFTWARE_DELIVERY_PHASE_2_OPERATOR_RUNBOOK.md) | Exact commands, phrases, troubleshooting |
| AETHOS_PHASE_2_READINESS_CONTRACT.md | Master Phase 2 boundaries |

---

## Lane docs (125A–125I)

| Fix | Lane |
|-----|------|
| 125A | [Issue plan](./SOFTWARE_DELIVERY_ISSUE_PLAN_LANE.md) |
| 125B | [Branch orchestration](./SOFTWARE_DELIVERY_BRANCH_ORCHESTRATION_LANE.md) |
| 125C | [Patch proposal](./SOFTWARE_DELIVERY_PATCH_PROPOSAL_LANE.md) |
| 125D | [Workspace apply](./SOFTWARE_DELIVERY_WORKSPACE_APPLICATION_LANE.md) |
| 125E | [Workspace verification](./SOFTWARE_DELIVERY_WORKSPACE_VERIFICATION_LANE.md) |
| 125F | [PR draft](./SOFTWARE_DELIVERY_PR_DRAFT_LANE.md) |
| 125G | [GitHub preflight](./SOFTWARE_DELIVERY_GITHUB_PR_PREFLIGHT_LANE.md) |
| 125H | [Branch push](./SOFTWARE_DELIVERY_BRANCH_PUSH_LANE.md) |
| 125I | [PR open](./SOFTWARE_DELIVERY_GITHUB_PR_OPEN_LANE.md) |

---

## Governance rules

- **Governed workspace only** until 125H (`data/software_delivery_workspaces/`)
- **No merge** from software delivery lane
- **No deploy** from software delivery lane
- **No Railway mutation** from software delivery lane
- **Exact approval phrases** at each gated step
- **Receipts + timeline** required for audit
- **Idempotent replay** on completed stages
- **Workspace rollback snapshots** (125D)

---

## Certification

```bash
make certify
```

Baselines (FIX 126): **≥ 19** certification modules, **≥ 61** passing tests.

Machine-readable contract:

`aethos_core/software_delivery/software_delivery_phase_2_contract.py`

---

## Troubleshooting (quick)

| Issue | Doc section |
|-------|-------------|
| Verification blocked | [Runbook — Verification](./SOFTWARE_DELIVERY_PHASE_2_OPERATOR_RUNBOOK.md) |
| Workspace rollback | [Runbook — Workspace](./SOFTWARE_DELIVERY_PHASE_2_OPERATOR_RUNBOOK.md) |
| Preflight rejection | [Runbook — Preflight](./SOFTWARE_DELIVERY_PHASE_2_OPERATOR_RUNBOOK.md) |
| Protected branch / push | [Branch push lane](./SOFTWARE_DELIVERY_BRANCH_PUSH_LANE.md) |
| GitHub auth | [Preflight lane](./SOFTWARE_DELIVERY_GITHUB_PR_PREFLIGHT_LANE.md) |
| Idempotent replay | [Freeze doc](./SOFTWARE_DELIVERY_PHASE_2_CERTIFICATION_FREEZE.md) |

---

## Mission Control operator console (FIX 128–135)

| Doc | Purpose |
|-----|---------|
| [MISSION_CONTROL_INDEX.md](./MISSION_CONTROL_INDEX.md) | **Index** — frozen operator console (129–135) |
| [MISSION_CONTROL_PHASE_2_UI_FREEZE.md](./MISSION_CONTROL_PHASE_2_UI_FREEZE.md) | UI freeze, API surface, forbidden controls |
| [MISSION_CONTROL_OPERATOR_RUNBOOK.md](./MISSION_CONTROL_OPERATOR_RUNBOOK.md) | Operator workflows |
| [MISSION_CONTROL_TROUBLESHOOTING.md](./MISSION_CONTROL_TROUBLESHOOTING.md) | Common failures |
| [MISSION_CONTROL_CROSS_LANE_OBSERVABILITY.md](./MISSION_CONTROL_CROSS_LANE_OBSERVABILITY.md) | Cross-lane snapshot, timeline, attention queue |

## Multi-agent advisory (FIX 127)

| Doc | Purpose |
|-----|---------|
| [SOFTWARE_DELIVERY_MULTI_AGENT_LANE.md](./SOFTWARE_DELIVERY_MULTI_AGENT_LANE.md) | Bounded Planner/Reviewer/Verification/Risk/DiffAudit agents |

Advisory only — no ExecutorAgent, no mutations.

## Roadmap (deferred)

| Item | Status |
|------|--------|
| ExecutorAgent / autonomous mutation | Deferred |
| Parallel agent orchestration at scale | Future |
| Governed merge flows | Future |
| Governed deployment promotion | Future (infra lane) |
