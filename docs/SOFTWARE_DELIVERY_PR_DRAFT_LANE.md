# Software Delivery — PR Draft Artifact (FIX 125F)

**Governed PR draft artifact** after workspace verification passes. No GitHub PR creation, git push, merge, deploy, or repo mutation (125G+).

```text
… → verify workspace (125E) → create PR draft (125F) → GitHub PR (125G, future)
```

---

## Prerequisites

1. Full stack through **125E** with `workspace verification` status **passed**

---

## Commands

| Command | Purpose |
|---------|---------|
| `create software delivery pr draft` | Compose + persist draft artifact |
| `create governed pr draft` | Alias |
| `show software delivery pr draft` | Full title, body, checklist |
| `show pr draft status` | Summary metadata |

---

## Draft contents

- Title + markdown body
- Verification summary (125E checks)
- Risk + rollback notes from plan
- Human review requirements
- Review checklist
- Linked issue + governed branch name

Artifacts: `data/software_delivery_pr_drafts/{draft_id}.json` + `{draft_id}.md`

---

## Forbidden (125F)

- GitHub PR creation
- Git push / commit
- Merge
- Deploy
- Repository writes

---

## Environment

```bash
SOFTWARE_DELIVERY_PR_DRAFT_ENABLED=true
SOFTWARE_DELIVERY_PR_DRAFT_REQUIRE_VERIFICATION=true
```

---

## Related

- [SOFTWARE_DELIVERY_WORKSPACE_VERIFICATION_LANE.md](./SOFTWARE_DELIVERY_WORKSPACE_VERIFICATION_LANE.md)
- FIX **125G** — [GitHub PR creation preflight](./SOFTWARE_DELIVERY_GITHUB_PR_PREFLIGHT_LANE.md)
- FIX **125H** — [branch push + commit](./SOFTWARE_DELIVERY_BRANCH_PUSH_LANE.md)
- FIX **125I** — [open GitHub PR](./SOFTWARE_DELIVERY_GITHUB_PR_OPEN_LANE.md)
