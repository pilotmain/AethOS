# Vercel Provider Operations Skill

Read-only inspection first; mutations require explicit approval and verified auth.

## Supported operations

- list projects
- list deployments
- inspect build/function logs
- redeploy (stub)
- rollback (stub)
- env vars (stub)
- domain health

## Required credentials

- Vercel API token or saved browser session

## Readonly tools

- list_projects
- deployment_status
- service_health_summary

## Mutation tools

- redeploy (not implemented)
- rollback (not implemented)

## Evidence rules

- Use deployment/build logs with UTC timestamps.
- Do not claim mutation success without provider confirmation.

## Verification rules

- Health summaries are readonly until mutation skills are implemented.

## Rollback rules

- Not available until mutation path is implemented.

## Common failure patterns

- Missing API token
- Expired browser session

## Repair recipes

- Reconnect Vercel auth, rerun readonly inspection
