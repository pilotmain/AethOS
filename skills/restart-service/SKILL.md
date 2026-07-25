---
name: restart-service
description: Restart a running service safely with governed approval and verification.
---

## When to use

The operator asks to restart, bounce, or cycle a service ("restart aethos-api").

## Steps

1. Resolve provider + project + environment + service. Confirm if ambiguous.
2. Read current health so you can compare before/after.
3. Create a governed **restart preflight** (blast radius, rollback). Do NOT execute.
4. Operator approves in the approvals surface.
5. After approval, confirm the restart from post-approval evidence: a startup log
   timestamp AFTER the approval time. If logs are older than approval, the restart
   is unverified — say so honestly.

## Mutation tools

- create restart preflight (governed)
- verify_operation / fetch_logs (post-approval)

## Governance

Mutation. Preflight → approve → execute → verify. Logs older than the approval
time never prove a restart.
