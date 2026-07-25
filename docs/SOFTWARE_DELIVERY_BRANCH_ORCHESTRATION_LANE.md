# Software Delivery — Branch Orchestration (FIX 125B)

**First controlled workspace execution layer** for governed software delivery. Branch lifecycle only — no code modification, PR creation, or merge.

```text
software delivery lane  ≠  infrastructure mutation lane
one issue plan          →  one governed branch context
```

---

## Prerequisites (FIX 125A)

1. `analyze github issue owner/repo#N`
2. `create implementation plan`
3. `approve implementation planning` + planning phrase

---

## Commands (125B)

| Command | Purpose |
|---------|---------|
| `create implementation branch` + phrase | Reserve branch context + isolated workspace path |
| `show implementation branch status` | Lifecycle, job id, workspace, lock |
| `archive implementation branch` + phrase | Archive branch context (rollback semantics) |
| `restore implementation branch` + phrase | Restore archived context |
| `show software delivery timeline` | Plan events + branch events + receipts |

### Approval phrases

**Create**

```text
I authorize creating the governed implementation branch for this software delivery plan.
```

**Archive**

```text
I authorize archiving the governed implementation branch for this software delivery plan.
```

**Restore**

```text
I authorize restoring the governed implementation branch for this software delivery plan.
```

---

## Governance (Railway-aligned)

| Mechanism | 125B behavior |
|-----------|----------------|
| Receipts | `data/software_delivery_branch_receipts/` |
| Lifecycle persistence | `data/software_delivery_branch_contexts/` |
| Isolated workspace | `data/software_delivery_workspaces/{plan_id}/` |
| Idempotency | Active branch create is no-op |
| Execution mode | `software_delivery_branch_simulation` |
| Locks | `lock_holder` on active/restored context |
| Audit | `mutation_performed: false` on all events |

---

## Forbidden (125B)

- Code modification (125C proposes only; writes in 125D+)
- PR creation
- Merge to `main`
- Railway / infra mutation from this lane

---

## Environment

```bash
SOFTWARE_DELIVERY_BRANCH_ORCHESTRATION_ENABLED=true
SOFTWARE_DELIVERY_BRANCH_REQUIRE_PLANNING_APPROVED=true
```

---

## Route

`route_id: software_delivery_issue_plan` (same lane as 125A; stage in `software_delivery_stage` metadata)

---

## Related

- [SOFTWARE_DELIVERY_ISSUE_PLAN_LANE.md](./SOFTWARE_DELIVERY_ISSUE_PLAN_LANE.md) (125A)
- AETHOS_PHASE_2_READINESS_CONTRACT.md
