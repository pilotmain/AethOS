# Software Delivery — GitHub PR Creation Preflight (FIX 125G)

**Readiness gate before any GitHub mutation.** Separates preflight (125G) from branch push (125H) and PR open (125I), mirroring Railway’s mutation separation.

```text
… → PR draft (125F) → GitHub preflight (125G) → approve → push (125H) → open PR (125I)
```

---

## Commands

| Command | Purpose |
|---------|---------|
| `run github pr creation preflight` | Auth, scope, branch readiness, package size, protection, preview |
| `show github pr creation preflight status` | Summary |
| `show github pr creation preflight report` | Full report |
| `approve github pr creation preflight` + phrase | Unblock 125H/125I (still no mutation in 125G) |

### Approval phrase

```text
I authorize proceeding with governed GitHub PR creation after this preflight.
```

---

## Preflight checks

| Check | Description |
|-------|-------------|
| Readiness gate | PR draft + verification passed |
| GitHub auth/scope | Token + repository access (read-only API) |
| Branch push readiness | Workspace tree + branch name ready for 125H |
| Diff/package size | Bounded file count and bytes |
| Protected branch policy | Feature branch ≠ default; protection awareness |
| PR title/body review | Final review metadata from 125F draft |
| Mutation preview | What 125H and 125I will do (disabled here) |
| Idempotency key | `sdgpr-{hash}` for future mutations |
| Rollback/cleanup plan | Branch/workspace/PR rollback steps |

---

## Next step

After approve, run FIX **125H** (`push governed branch to github` with push approval phrases), then FIX **125I** ([open PR](./SOFTWARE_DELIVERY_GITHUB_PR_OPEN_LANE.md)).

## Forbidden (125G)

- Git push
- GitHub PR creation
- Repo writes
- Merge / deploy

---

## Environment

```bash
SOFTWARE_DELIVERY_GITHUB_PR_PREFLIGHT_ENABLED=true
SOFTWARE_DELIVERY_GITHUB_PR_PREFLIGHT_REQUIRE_DRAFT=true
```

---

## Related

- [SOFTWARE_DELIVERY_PR_DRAFT_LANE.md](./SOFTWARE_DELIVERY_PR_DRAFT_LANE.md)
