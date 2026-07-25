# Organizations & RBAC

## Model

- **Organizations** — tenant boundary
- **Workspaces** — scoped operational areas within an org
- **Roles** — admin, operator, reviewer, viewer
- **Audit attribution** — immutable who-approved/executed log

## Roles

| Role | Capabilities |
|------|-------------|
| Viewer | Readonly, audit read |
| Operator | Create preflights, watch mode |
| Reviewer | Approve E2 tier |
| Admin | Approve E3+, org/credential management |

## API

```bash
GET  /api/v1/orgs/current
POST /api/v1/orgs/members/role
POST /api/v1/orgs/rbac/check
GET  /api/v1/orgs/audit
```

## Example RBAC check

```json
POST /api/v1/orgs/rbac/check
{"user_id": "alice", "action": "approve_e3", "engineering_tier": "E3_pr_creation"}
```

## Governance

RBAC never bypasses engineering preflight approval. Autonomous execution remains blocked for all roles.

See [ENTERPRISE_SECURITY.md](ENTERPRISE_SECURITY.md).
