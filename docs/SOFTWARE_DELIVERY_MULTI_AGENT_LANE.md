# Software Delivery — Bounded Multi-Agent Roles (FIX 127)

**Advisory collaboration only** on top of the frozen FIX 126 loop. Agents analyze and recommend; they do **not** mutate, merge, deploy, or bypass approvals.

```text
software_delivery_lane != infrastructure_mutation_lane
```

---

## Bounded agents (FIX 127)

| Agent | Scope |
|-------|--------|
| **PlannerAgent** | Loop position, next governed stages |
| **ReviewerAgent** | Human review readiness, checklist |
| **VerificationAgent** | Workspace verification status |
| **RiskAgent** | Plan risk / blast radius |
| **DiffAuditAgent** | Patch proposal / diff audit |

**No ExecutorAgent** in FIX 127.

---

## Allowed

- planning, analysis, verification, review, risk assessment, patch proposal review

## Forbidden

- merge, deploy, Railway mutation, bypass approvals, rollout promotion, workspace/repo mutation, self-authorizing execution

---

## Commands

```text
run software delivery agent collaboration
run software delivery planner agent
run software delivery reviewer agent
run software delivery verification agent
run software delivery risk agent
run software delivery diff audit agent
show software delivery agent collaboration report
show software delivery agent collaboration status
```

Requires an active issue plan (125A).

---

## Machine-readable

`aethos_core/software_delivery/multi_agent/multi_agent_contract.py`
