# SPDX-License-Identifier: Apache-2.0
"""Structured provider E2E readiness and missing-configuration reports."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_e2e_readiness.blocker_mapping import (
    ReadinessBlocker,
    collect_safe_next_commands,
    format_blocker_entry,
)


def compose_structured_readiness_report(
    *,
    provider: str,
    checks: dict[str, Any],
    blockers: list[ReadinessBlocker],
    target_label: str = "",
    overall_ready: bool,
) -> str:
    provider_title = provider.title()
    lines = [
        f"**{provider_title} Deployment Readiness**",
        "",
        "### 1. Overall readiness",
        f"- Status: **{'ready for governed execution prep' if overall_ready else 'not ready'}**",
        "- Execution started: **false**",
        "- Mutation performed: **false**",
        "",
        "### 2. Provider connection",
    ]

    if provider == "railway":
        token_ok = bool(checks.get("railway_credential_ok"))
        conn_ok = bool(checks.get("railway_api_connection_ok"))
        lines.extend(
            [
                f"- Railway token: **{'pass' if token_ok else 'fail'}**",
                f"- API connection: **{'pass' if conn_ok else 'fail'}**",
                f"- Credential source: {checks.get('railway_credential_source_label') or checks.get('railway_credential_source') or 'unknown'}",
                f"- Validation probe: `{checks.get('railway_validation_probe') or 'ProjectsAndServices'}`",
                f"- Probe status: **{'pass' if conn_ok else 'fail'}**",
            ]
        )
        if checks.get("railway_credential_masked_identifier"):
            lines.append(f"- Token identifier: `{checks['railway_credential_masked_identifier']}`")
        if checks.get("railway_credential_id"):
            lines.append(f"- Credential id: `{checks['railway_credential_id']}`")
    else:
        lines.extend(
            [
                f"- Vercel credential: **{'pass' if checks.get('vercel_credential_ok') else 'fail'}**",
                f"- API connection: **{'pass' if checks.get('vercel_api_connection_ok') else 'fail'}**",
                f"- Projects visible: **{checks.get('vercel_project_count', 0)}**",
            ]
        )

    lines.extend(["", "### 3. Target project/service"])
    if target_label:
        lines.append(f"- Resolved target: `{target_label}`")
    elif provider == "railway":
        inv = checks.get("inventory") or {}
        inv_ok = bool(inv.get("ok"))
        lines.append(
            f"- Inventory: **{inv.get('project_count', 0)}** project(s), "
            f"**{inv.get('service_count', 0)}** service(s)"
        )
        lines.append(
            f"- Inventory probe: `{inv.get('inventory_probe') or 'ProjectsEnvironmentsServices'}` · "
            f"**{'pass' if inv_ok else 'fail'}**"
        )
        if not inv_ok and inv.get("error"):
            lines.append(f"- Inventory detail: {str(inv.get('error'))[:200]}")
    else:
        lines.append(f"- Project count: **{checks.get('vercel_project_count', 0)}**")

    lines.extend(["", "### 4. Environment variable readiness"])
    if provider == "railway":
        creation = checks.get("service_creation") or {}
        env_writes = bool(creation.get("env_var_writes_enabled"))
        for row in list(checks.get("required_env_vars") or [])[:6]:
            lines.append(f"- {row}")
        lines.append(f"- Governed env var writes: **{'enabled' if env_writes else 'disabled'}**")
    else:
        env_writes = bool(checks.get("env_var_mutations_enabled"))
        lines.append(f"- Governed env var writes: **{'enabled' if env_writes else 'disabled'}**")
        lines.append("- Env var keys are inspected at orchestration time — values are never shown in chat.")

    mutation_enabled = bool(checks.get("mutation_execution_enabled"))
    provider_env_writes = bool(checks.get("provider_env_var_mutations_enabled"))
    lines.extend(
        [
            "",
            "### 5. Mutation/approval readiness",
            f"- Mutation execution gate: **{'enabled' if mutation_enabled else 'disabled'}**",
            f"- Provider env var mutations: **{'enabled' if provider_env_writes else 'disabled'}**",
            "- Explicit Mission Control approval is required before any mutation step.",
            "",
            "### 6. Deployment verification readiness",
            "- Post-deploy polling and health verification are available via governed orchestration jobs.",
            "- No deployment verification has run in this turn.",
        ]
    )

    lines.extend(["", "### 7. Blockers"])
    if blockers:
        for idx, blocker in enumerate(blockers, start=1):
            lines.append(format_blocker_entry(blocker, index=idx))
            lines.append("")
    else:
        lines.append("- None — readonly readiness checks passed for connection and inventory.")

    safe_steps = collect_safe_next_commands(
        blockers,
        extra=[
            f"show {provider_title} deployment readiness",
            f"validate {provider_title} connection",
        ],
    )
    lines.extend(["### 8. Safe next steps"])
    for step in safe_steps:
        lines.append(f"- {step}")
    lines.append("")
    lines.append("No provider mutation has been performed.")
    return "\n".join(lines)


def compose_structured_missing_config_report(
    *,
    provider: str,
    requested_action: str,
    blockers: list[ReadinessBlocker],
    required_configuration: list[str] | None = None,
    safe_next_commands: list[str] | None = None,
) -> str:
    provider_title = provider.title()
    safe_steps = safe_next_commands or collect_safe_next_commands(
        blockers,
        extra=[
            f"show {provider_title} connection status",
            f"validate {provider_title} connection",
            f"show {provider_title} deployment readiness",
        ],
    )
    lines = [
        f"**{provider_title} E2E — missing configuration**",
        "",
        "Execution has **not** started.",
        "",
        f"**Provider:** {provider_title}",
        f"**Requested action:** {requested_action}",
        "**Mutation performed:** No",
        "",
        "**Blockers:**",
    ]
    if blockers:
        for idx, blocker in enumerate(blockers, start=1):
            lines.append(format_blocker_entry(blocker, index=idx))
            lines.append("")
    else:
        lines.append("- Unknown blocker — check Mission Control → Advanced settings → Credentials.")
    if required_configuration:
        lines.extend(["", "**Required configuration:**"])
        for item in required_configuration:
            lines.append(f"- {item}")
    lines.extend(["", "**Safe next steps:**"])
    for step in safe_steps:
        lines.append(f"- {step}")
    lines.append("")
    lines.append("No provider mutation has been performed.")
    return "\n".join(lines)
