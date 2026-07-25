# AethOS architecture

AethOS separates intent, policy, execution, and evidence so an agent cannot
silently turn a request into an unreviewed infrastructure change.

```text
Web / API / Telegram / Slack
            |
            v
Conversation and intent routing
            |
            v
Planning + policy + approval gates
            |
            v
Provider and workspace runtimes
            |
            v
Evidence + verification + audit
            |
            v
Mission Control observability
```

## Major components

| Component | Responsibility | Primary location |
| --- | --- | --- |
| API | Authentication, request boundaries, route composition | `aethos_core/api/` |
| Conversation runtime | Intent classification, continuity, response shaping | `aethos_core/chat/`, `aethos_core/conversation/` |
| Execution brain | Plans tool use and coordinates bounded agent work | `aethos_core/execution_brain/`, `aethos_core/agents/` |
| Governance | Preflight, risk, approval, and mutation controls | `aethos_core/operations/`, `aethos_core/governance/` |
| Providers | Read-only discovery and governed provider actions | `aethos_core/providers/` |
| Evidence | Captures and correlates observable outcomes | `aethos_core/evidence_correlation/`, `aethos_core/observability/` |
| Mission Control | Operator views, approvals, runtime state, and audit access | `aethos_core/mission_control/`, `web/` |

## Request lifecycle

1. A channel adapter normalizes the request and identity context.
2. Intent routing distinguishes informational, read-only, and mutating work.
3. Read-only work can execute within configured provider permissions.
4. Mutating work creates a preflight with target, risk, blast radius, rollback,
   and required approval.
5. Approval is validated against the current operation state; it is not a generic
   permission to run arbitrary commands.
6. Execution uses the selected provider or workspace adapter.
7. Verification captures evidence and the audit trail records the outcome.

## Trust boundaries

- Provider credentials remain in the credential subsystem and are not returned
  through normal API responses.
- Tenant, organization, workspace, and session identifiers define data and
  approval scope.
- Browser and host execution are separate capabilities with independent policy.
- Plugins use the governed SDK contract and do not receive an implicit bypass.
- Mission Control presents state and submits governed actions; it is not a direct
  provider backdoor.

## State and persistence

Local deployments write runtime state under the configured data directories.
Those directories may contain credentials, audit records, browser profiles, or
operator data and must not be committed. Production deployments should use
durable storage, backups, encryption, access controls, and retention settings
appropriate to their environment.

For endpoint and runtime detail, see [RUNTIME.md](RUNTIME.md). For deployment
controls, see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md).
