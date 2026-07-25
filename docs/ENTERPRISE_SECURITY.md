# Enterprise Security

## Mandatory invariants (always blocked)

- Unrestricted shell (`HOST_EXECUTOR_ENABLED=false` in production)
- Silent mutation
- Auto-merge
- Hidden retries
- Stealth execution
- Secret leakage in API responses
- Autonomous deployments
- Privilege escalation via plugins

## RBAC

Role-based access enforced via `aethos_core/orgs/rbac.py`. See [ORGS_AND_RBAC.md](ORGS_AND_RBAC.md).

## Production requirements

When `APP_ENV=production`:
- `WEB_API_TOKEN` required
- Safe defaults audit must pass
- Host executor disabled

## Audit integrity

- Approval attributions: append-only JSONL (`data/orgs/audit_attribution.jsonl`)
- Engineering audit: governed mutation trail
- Immutable attribution records

## Credential vault

Encrypted storage under `data/credentials`. Doctor check: `aethos doctor --category vault`.

## Plugin sandbox

All plugins validated against forbidden capability list before enable.

## Verification

```bash
GET /api/v1/enterprise/safe-defaults
aethos doctor
```

Mission Control → Production Infrastructure → Enterprise Security
