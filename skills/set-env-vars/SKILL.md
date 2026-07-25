---
name: set-env-vars
description: Set or update environment variables on a provider service, governed and redacted.
---

## When to use

The operator asks to add, change, or remove environment variables / config on a
service ("set WORKSPACE_SUITE_ENABLED=true on aethos-api").

## Steps

1. Resolve provider + project + environment + service. Confirm if ambiguous.
2. Read the current variables so the change is additive and non-conflicting.
3. Create a governed **set-env preflight** listing exactly which keys change (mask
   values). Secrets are read from the vault, never echoed into chat or logs.
4. Operator approves; a service restart/redeploy may be required for the new value
   to take effect — call that out and offer it as the next governed step.
5. Verify the variable is applied and the service is healthy afterward.

## Mutation tools

- create set-env preflight (governed)
- provider_status (post-approval verification)

## Governance

Mutation. Preflight → approve → execute → verify. Never print secret values;
keys only.
