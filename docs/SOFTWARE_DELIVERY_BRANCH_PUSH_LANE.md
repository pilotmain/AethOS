# Software Delivery — Governed Branch Push + Commit (FIX 125H)

**First bounded GitHub mutation** in the software delivery lane: create/update a remote **feature branch** and commit governed workspace files via the GitHub Contents API. No PR open, merge, deploy, or direct `main`/`master` push. PR creation is FIX **125I** (separate step).

## Pipeline position

```text
… → PR draft (125F) → GitHub preflight (125G) → approve preflight
  → push feature branch (125H) → open PR (125I)
```

## Commands

| Command | Effect |
|---------|--------|
| `push governed branch to github` + approval phrases | Push workspace files to feature branch |
| `show governed branch push status` | Short status |
| `show governed branch push report` | Full push record + rollback plan |

## Required gates (all must pass)

1. **125G** preflight `preflight_passed` and `preflight_approved`
2. Workspace verification passed (125E)
3. PR draft exists (125F)
4. Branch context `active` or `restored` (125B)
5. Workspace patch applied (125D)
6. **Exact phrases** (in user message):
   - `I authorize pushing the governed workspace changes to the GitHub feature branch.`
   - `I acknowledge the governed branch push mutation preview from FIX 125G.`
7. Protected branch guard — not `main`, `master`, or configured default branch
8. GitHub token scope re-check (same as 125G)
9. Idempotent replay when same `idempotency_key` from 125G

## Boundaries (125H)

| Capability | Enabled |
|------------|---------|
| Feature branch create/update | Yes |
| Workspace file commit to branch | Yes |
| GitHub PR create | **No** (125I) |
| Merge | **No** |
| Deploy | **No** |
| Direct default-branch push | **No** |

## Rollback / cleanup

Push record inherits 125G `rollback_cleanup_plan` and adds `branch_push_rollback` steps (delete remote branch, workspace rollback, idempotency reference).

## Configuration

- `SOFTWARE_DELIVERY_GITHUB_BRANCH_PUSH_ENABLED`
- `SOFTWARE_DELIVERY_GITHUB_DEFAULT_BRANCH` (default `main`)

## Next step

FIX **125I** — [`open governed github pull request`](./SOFTWARE_DELIVERY_GITHUB_PR_OPEN_LANE.md) after push succeeds.

## Lane separation

`software_delivery_issue_plan` route with `mutation_scope: feature_branch_push_only`. Infrastructure/Railway mutation lanes remain separate.
