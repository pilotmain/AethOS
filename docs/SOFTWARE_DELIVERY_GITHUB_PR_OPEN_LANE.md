# Software Delivery — Governed GitHub PR Open (FIX 125I)

**Opens a GitHub pull request** after governed branch push (125H). Title and body come from the 125F PR draft. No merge, deploy, Railway mutation, or auto-review approval. **Human review required.**

## Pipeline position

```text
… → branch push (125H) → open PR (125I) → human review → merge/deploy (out of band)
```

Completes the Phase 2 software-delivery loop through human-review PR:

`issue → plan → branch → patch → apply → verify → PR draft → branch push → PR open`

## Commands

| Command | Effect |
|---------|--------|
| `open governed github pull request` + approval phrase | Create PR on GitHub |
| `show governed github pr status` | Short status |
| `show governed github pr report` | Full record + URL |

## Approval phrase

```text
I authorize opening the governed GitHub pull request for human review.
```

## Required gates

1. **125H** branch push `status == pushed`
2. **125G** preflight approved
3. **125F** PR draft exists (`drafted`)
4. Exact approval phrase in user message
5. Idempotent replay when same `idempotency_key` and PR already opened

## Boundaries (125I)

| Capability | Enabled |
|------------|---------|
| GitHub PR create | Yes |
| Merge | **No** |
| Deploy | **No** |
| Railway mutation | **No** |
| Auto-review approval | **No** |
| Human review | **Required** |

## Artifacts

- Durable record: `data/software_delivery_github_pr_opens/`
- Receipts: `data/software_delivery_github_pr_open_receipts/`
- PR URL and number persisted; draft updated with `github_pr_created`

## Configuration

- `SOFTWARE_DELIVERY_GITHUB_PR_OPEN_ENABLED`
