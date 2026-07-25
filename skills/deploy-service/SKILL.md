---
name: deploy-service
description: Deploy or redeploy a service to a provider through the governed preflight flow.
---

## When to use

The operator asks to deploy, redeploy, ship, or push a service live (e.g.
"redeploy aethos-api on Railway with latest changes").

## Steps

1. Resolve the target: provider, project, environment, service. If more than one
   service matches (e.g. both aethos-api and aethos-ui), confirm which to deploy.
2. Validate the provider credential and connection (read-only preflight).
3. Create a governed deploy/redeploy **preflight** — describe blast radius and the
   rollback path. Do NOT execute.
4. Surface the preflight in the approvals surface; the operator reviews and
   approves before anything runs.
5. After approval, watch the deployment and verify health from real evidence
   (status + post-deploy logs/timestamps), then report verified or unconfirmed.

## Mutation tools

- create deploy/redeploy preflight (governed)
- verify_deployment (post-approval)

## Governance

Mutation. Always preflight → approve → execute → verify. Never report success
without post-approval evidence.
