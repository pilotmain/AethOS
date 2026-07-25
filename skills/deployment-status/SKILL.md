---
name: deployment-status
description: Read a service's current deployment status and health across providers.
---

## When to use

The operator asks "is it deployed?", "what's the status?", "is the latest live?",
or wants a governed deployment/health summary for a service.

## Steps

1. Identify the provider + target (Railway/Vercel, project/service, environment).
   If ambiguous, ask which provider and target.
2. Read the latest deployment (status, commit, created time) and current health.
3. Summarize: deployment status, commit/source, health, and whether the latest
   commit is the one running.
4. If unhealthy or stale, offer the next governed step (check logs, redeploy).

## Readonly tools

- provider_status / provider_inventory
- recall_last_deployment_thread

## Governance

Read-only. Any redeploy/restart is a separate governed action (preflight →
approve). Never claim success without evidence.
