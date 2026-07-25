# Software Delivery — Workspace Code Application (FIX 125D)

**First governed code-write phase** — applies an approved patch proposal **only** inside the isolated workspace tree. Repository, git, PR, merge, deploy, and infrastructure remain untouched.

```text
plan → branch → patch proposal → approval → workspace apply (125D)
```

---

## Prerequisites

1. FIX 125A–125C complete through **patch proposal approved**
2. Active or restored implementation branch context

---

## Commands (125D)

| Command | Purpose |
|---------|---------|
| `apply approved patch to workspace` + phrase | Snapshot → apply staged patches → receipts |
| `show workspace apply status` | Application id, snapshot, files applied |
| `show governed workspace diff` | Unified diff: repo vs workspace tree |
| `rollback workspace changes` + phrase | Restore pre-apply snapshot |

### Apply phrase

```text
I authorize applying the approved patch proposal to the governed software delivery workspace.
```

### Rollback phrase

```text
I authorize rolling back the governed software delivery workspace to the pre-apply snapshot.
```

---

## Critical rules

| Rule | Enforcement |
|------|-------------|
| Writes only in governed workspace | `data/software_delivery_workspaces/{plan_id}/tree/` |
| Only approved files | `proposed_files` scope validation |
| Only approved proposal | `patch_proposal_approved` gate |
| Deterministic apply | `staged_patches` from proposal (not re-generated) |
| Rollback snapshot before write | `rollback/{snapshot_id}/` |
| Workspace diff receipts | `workspace_diff_recorded` phase |
| Write audit trail | events + `software_delivery_workspace_applications/` |
| No out-of-scope files | path normalization + blocklist |
| No shell / deps / discovery mutation | contract flags false |

---

## Still forbidden (125D)

- Git commit
- PR creation
- Merge
- Deploy
- Infrastructure mutation
- Repository writes

---

## Environment

```bash
SOFTWARE_DELIVERY_WORKSPACE_APPLY_ENABLED=true
SOFTWARE_DELIVERY_WORKSPACE_REQUIRE_PATCH_APPROVED=true
```

---

## Related

- [SOFTWARE_DELIVERY_PATCH_PROPOSAL_LANE.md](./SOFTWARE_DELIVERY_PATCH_PROPOSAL_LANE.md)
- [SOFTWARE_DELIVERY_BRANCH_ORCHESTRATION_LANE.md](./SOFTWARE_DELIVERY_BRANCH_ORCHESTRATION_LANE.md)
