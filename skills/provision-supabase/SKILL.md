---
name: provision-supabase
description: Provision or connect a Supabase project/database and wire it to a service.
---

## When to use

The operator asks to create a Supabase project, add a database, or connect
Supabase to a service ("provision a Supabase db for aethos-api").

## Steps

1. Confirm the Supabase credential is present in the vault (management token /
   access token). If missing, ask the operator to add it in Connections — never
   request it in chat.
2. Read existing Supabase projects to avoid duplicates.
3. Create a governed **provision/connect preflight**: project/region for new
   projects, or the connection string wiring for existing ones (values masked).
4. Operator approves; on execution, store the connection secret in the vault and
   wire it to the target service as an env var via the set-env governed flow.
5. Verify connectivity (read-only) and report.

## Mutation tools

- create supabase provision/connect preflight (governed)
- set-env preflight (to wire the connection string)

## Governance

Mutation. Vault-only credentials, masked values, preflight → approve → execute →
verify.
