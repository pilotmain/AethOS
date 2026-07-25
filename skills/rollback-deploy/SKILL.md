---
name: rollback-deploy
description: Roll a service back to a previous known-good deployment, governed.
---

## When to use

A deploy made things worse and the operator wants to revert ("rollback aethos-api
to the last working deploy").

## Steps

1. Resolve provider + project + environment + service.
2. List recent deployments and identify the last known-good one (status SUCCESS,
   healthy, prior commit). Show the operator the candidate before acting.
3. Create a governed **rollback preflight** targeting that deployment/commit
   (blast radius + that this replaces the current running version). Do NOT execute.
4. Operator approves.
5. After execution, verify the rolled-back version is live and healthy from fresh
   evidence (commit + post-rollback health/logs).

## Mutation tools

- create rollback preflight (governed)
- verify_deployment (post-approval)

## Governance

Mutation. Preflight → approve → execute → verify. Confirm the rollback target
with the operator before creating the preflight.
