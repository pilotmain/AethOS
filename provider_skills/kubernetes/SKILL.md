# Kubernetes Provider Operations Skill

Cluster operations — stub until implemented.

## Supported operations

- deployments (stub)
- pods (stub)
- events (stub)
- logs (stub)
- rollout restart (stub)
- rollout status (stub)
- configmaps/secrets metadata (stub)

## Required credentials

- kubeconfig with namespace-scoped RBAC

## Readonly tools

- get_pods
- get_events
- pod_logs

## Mutation tools

- rollout_restart (not implemented)

## Evidence rules

- Pod restart timestamps and ready conditions after approval.

## Verification rules

- Rollout status must reach Available with new pod logs.

## Rollback rules

- Not implemented.

## Common failure patterns

- kubeconfig missing or namespace mismatch

## Repair recipes

- Fix kube context, rerun readonly rollout status
