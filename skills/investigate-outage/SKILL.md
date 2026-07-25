---
name: investigate-outage
description: Diagnose why a service is down or erroring, with evidence before any fix.
---

## When to use

The operator reports something is down, failing, throwing errors, or "not working"
("why is aethos-api unhealthy?", "check why we see this issue").

## Steps

1. Resolve the affected provider + target. Stay on the provider the operator named
   or the one in active context — do not switch providers.
2. Gather evidence (read-only): current health/status, recent logs, latest
   deployment + commit, and recent changes.
3. Form a hypothesis grounded in the evidence (bad deploy, crash loop, missing env
   var, dependency/credential failure, upstream provider issue).
4. Propose the smallest governed fix (set env var, rollback, redeploy, restart) as
   a preflight — do NOT execute.
5. After approval and execution, verify recovery from fresh evidence.

## Readonly tools

- provider_status / provider_logs / provider_inventory
- recall_last_deployment_thread

## Governance

Investigation is read-only. Any remediation is a separate governed action
(preflight → approve). Never guess a cause without evidence.
