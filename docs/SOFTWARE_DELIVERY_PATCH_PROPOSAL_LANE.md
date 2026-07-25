# Software Delivery — Patch Proposal (FIX 125C)

**Bounded patch contract** — propose files, generate patch intent, preview diffs, approve proposal. **No file writes, commits, PRs, merges, or deploys.**

```text
plan (125A) → branch (125B) → patch proposal (125C) → approval → code write (future)
```

---

## Prerequisites

1. FIX 125A: analyze → plan → approve planning
2. FIX 125B: create implementation branch (active or restored)

---

## Commands (125C)

| Command | Purpose |
|---------|---------|
| `propose patch files` / `propose files to change` | Inspect plan + branch; bound file list |
| `generate patch intent` / `generate patch proposal` | Structured intent + unified diffs (read-only) |
| `show patch diff preview` | Render diff preview; record preview receipt |
| `approve patch proposal` + phrase | Human approve proposal (writes still disabled) |
| `show patch proposal status` | Proposal lifecycle summary |

### Approval phrase

```text
I approve this governed software delivery patch proposal for bounded application.
```

Approval authorizes FIX **125D** workspace apply — it does **not** write files in 125C.

---

## Governance

| Mechanism | 125C behavior |
|-----------|----------------|
| Plan + branch inspection | Required before file proposal |
| Receipts | `data/software_delivery_patch_receipts/` |
| Proposals | `data/software_delivery_patch_proposals/` |
| Diff generation | Read-only (`generate_patch_proposal` / cert fixture) |
| `file_write_enabled` | **false** |
| `git_commit_enabled` | **false** |
| PR / merge / deploy | **false** |

---

## Environment

```bash
SOFTWARE_DELIVERY_PATCH_PROPOSAL_ENABLED=true
SOFTWARE_DELIVERY_PATCH_REQUIRE_PLANNING_APPROVED=true
SOFTWARE_DELIVERY_PATCH_REQUIRE_ACTIVE_BRANCH=true
```

---

## Route

`route_id: software_delivery_issue_plan` — `software_delivery_stage` distinguishes patch steps.

---

## Related

- [SOFTWARE_DELIVERY_ISSUE_PLAN_LANE.md](./SOFTWARE_DELIVERY_ISSUE_PLAN_LANE.md)
- [SOFTWARE_DELIVERY_BRANCH_ORCHESTRATION_LANE.md](./SOFTWARE_DELIVERY_BRANCH_ORCHESTRATION_LANE.md)
