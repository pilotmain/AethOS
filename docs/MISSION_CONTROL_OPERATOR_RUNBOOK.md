# Mission Control operator runbook

## Prerequisites

- The API and web UI are running.
- The operator is using the intended account, organization, workspace, and
  session.
- Required provider credentials have been configured and validated.

## Start an operator session

1. Open Mission Control.
2. Check runtime health and the active organization/workspace.
3. Review provider connection status before requesting live operations.
4. Use read-only inventory or diagnostics to confirm the target.

## Review operational state

Use Runtime, Jobs, Providers, and Engineering views to inspect current evidence.
A status shown without fresh provider evidence should be treated as stale or
unknown. Refresh before making a consequential decision.

## Approve a governed action

Before approval, confirm:

- the provider, project, environment, service, repository, and branch;
- the exact requested operation;
- risk tier and blast radius;
- required prerequisites and current evidence;
- rollback or recovery path;
- whether production access is enabled;
- whether the approval is still current and has not been superseded.

An approval applies only to its associated preflight. After approval, wait for
execution and verification receipts. Do not infer success from acceptance of the
request.

## Evidence and audit

For consequential actions, retain:

- preflight and execution identifiers;
- approver identity and decision time;
- provider response or workspace result;
- verification evidence;
- failure details and recovery actions.

Exports may contain operational metadata. Review them before sharing outside the
deployment's trust boundary.

## Stop conditions

Stop and investigate when:

- the displayed target differs from the operator's request;
- credentials or tenant scope are uncertain;
- evidence is stale, missing, or contradictory;
- an approval appears replayed or already consumed;
- a direct provider action bypasses the governed route;
- rollback prerequisites are unavailable.

See [MISSION_CONTROL_TROUBLESHOOTING.md](MISSION_CONTROL_TROUBLESHOOTING.md) for
recovery steps and [SOFTWARE_DELIVERY_OPERATOR_RUNBOOK.md](SOFTWARE_DELIVERY_OPERATOR_RUNBOOK.md)
for repository delivery workflows.
