# Mission Control

Mission Control is the operator interface for observing AethOS, reviewing
evidence, managing provider connections, and handling governed approvals.

## Operating model

```text
operator request
      |
      v
governed route -> policy/preflight -> approval when required
      |
      v
provider/workspace execution -> verification -> audit receipt
```

Mission Control does not grant a blanket mutation capability. Buttons and API
actions submit work to the same policy and approval paths used by chat and other
channels.

## Primary areas

| Area | Purpose |
| --- | --- |
| Runtime | Health, configuration state, jobs, and execution status |
| Providers | Connection status, capabilities, and credential guidance |
| Browser | Sessions, profiles, capture policy, and evidence |
| Engineering | Workspaces, repository analysis, delivery plans, and checks |
| Approvals | Pending preflights, risk context, decisions, and audit history |
| System | Identity, tenancy, observability, reliability, and diagnostics |

## Operator documentation

- [Operator runbook](MISSION_CONTROL_OPERATOR_RUNBOOK.md)
- [Troubleshooting](MISSION_CONTROL_TROUBLESHOOTING.md)
- [Runtime reference](RUNTIME.md)
- [Organizations and RBAC](ORGS_AND_RBAC.md)
- [Provider credentials](PROVIDER_CREDENTIALS.md)
- [Enterprise security](ENTERPRISE_SECURITY.md)

Detailed implementation specifications remain in this directory where runtime
contracts and certification tests depend on them. They supplement, but do not
replace, the supported guides above.
