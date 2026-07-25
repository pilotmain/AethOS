# Railway Provider Operations Skill

Governed Railway operations for AethOS — discover, mutate, observe, verify.

## Supported operations

- list projects/environments/services
- restart service
- redeploy service
- deploy latest
- env vars (readonly)
- runtime/build/deploy logs
- source binding reconciliation
- health verification

## Required credentials

- Railway API token or authenticated CLI session

## Readonly tools

- list_services
- list_deployments
- fetch_runtime_logs
- fetch_deployment_logs
- service_health

## Mutation tools

- service_instance_redeploy
- deployment_restart
- deploy_latest

## Evidence rules

- Compare all returned log lines against approval time — not only the latest line.
- Prefer fresh runtime CLI logs over cached deployment excerpts.
- Record command_submitted and command_name from execution results.

## Verification rules

- Restart verified when startup/runtime logs appear after approval.
- Mark unconfirmed when only pre-approval logs are available.

## Rollback rules

- Capture deployment snapshot before mutation.
- Compare deployment IDs and log timestamps after execution.

## Common failure patterns

- Missing environment_id for serviceInstanceRedeploy
- Token scope insufficient for GraphQL mutation
- Service name ambiguous across projects

## Repair recipes

- Reconcile source binding, then retry restart
- Fetch fresh runtime logs, then redeploy if no post-approval evidence
