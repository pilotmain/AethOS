# Software Delivery — Issue Plan Lane (FIX 125A)

**First human-governed autonomous software delivery lane** — planning only. Isolated from infrastructure orchestration.

```text
software delivery lane  ≠  infrastructure mutation lane
```

---

## FIX 125 roadmap

| Sub-fix | Scope |
|---------|--------|
| **125A** | Issue intake + governed planning (this doc) |
| **125B** | [Branch orchestration](./SOFTWARE_DELIVERY_BRANCH_ORCHESTRATION_LANE.md) |
| **125C** | [Patch proposal + diff preview](./SOFTWARE_DELIVERY_PATCH_PROPOSAL_LANE.md) |
| **125D** | [Workspace code application](./SOFTWARE_DELIVERY_WORKSPACE_APPLICATION_LANE.md) |
| **125E** | [Workspace verification](./SOFTWARE_DELIVERY_WORKSPACE_VERIFICATION_LANE.md) |
| **125F** | [PR draft artifact](./SOFTWARE_DELIVERY_PR_DRAFT_LANE.md) |
| **125G** | [GitHub PR creation preflight](./SOFTWARE_DELIVERY_GITHUB_PR_PREFLIGHT_LANE.md) |
| **125H** | [Governed branch push + commit](./SOFTWARE_DELIVERY_BRANCH_PUSH_LANE.md) |
| **125I** | [Governed GitHub PR open](./SOFTWARE_DELIVERY_GITHUB_PR_OPEN_LANE.md) |
| **126** | [Freeze](./SOFTWARE_DELIVERY_PHASE_2_CERTIFICATION_FREEZE.md) · [Runbook](./SOFTWARE_DELIVERY_PHASE_2_OPERATOR_RUNBOOK.md) · [Index](./SOFTWARE_DELIVERY_PHASE_2_INDEX.md) |
| **127** | [Bounded multi-agent advisory roles](./SOFTWARE_DELIVERY_MULTI_AGENT_LANE.md) |

---

## Commands (125A)

| Command | Purpose |
|---------|---------|
| `analyze github issue owner/repo#N` | Intake + analysis |
| `create implementation plan` | Draft governed plan |
| `show implementation scope` | Affected files, blast radius, tests |
| `show risk assessment` | Risk tier + rollback notes |
| `approve implementation planning` + phrase | Human approve planning only |

### Planning approval phrase

```text
I approve this governed software delivery implementation plan for human review.
```

---

## Outputs

- Bounded implementation plan
- Estimated affected files
- Blast radius (`local` / `service` / `platform`)
- Test expectations
- Rollback notes (branch revert — not prod deploy)
- Audit events (`mutation_performed: false`)

---

## Forbidden (125A and beyond until explicit sub-fix)

- Auto-merge to `main`
- Deploy to production
- Mutate Railway / infra from this lane
- Bypass approvals
- Code generation (125A — disabled)
- Self-expand scope

---

## Storage

`aethos_core/data/software_delivery_issue_plans/{plan_id}.json`

---

## Route

`route_id: software_delivery_issue_plan`

Routed before production incident / Railway governance routers. Does not hijack `github_workflow_lane` or `railway_execution_contract`.

---

## Environment

```bash
SOFTWARE_DELIVERY_ISSUE_PLAN_ENABLED=true
SOFTWARE_DELIVERY_REQUIRE_PLANNING_APPROVAL=true
```

---

## Related

- AETHOS_PHASE_2_READINESS_CONTRACT.md
- PHASE_9_7_SELF_IMPROVEMENT_SYSTEM.md
