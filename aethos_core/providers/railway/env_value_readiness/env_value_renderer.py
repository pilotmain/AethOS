# SPDX-License-Identifier: Apache-2.0
"""Render Railway env value readiness reports — no secret values."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.env_value_readiness.env_classification import (
    EnvCriticality,
    classify_env_var,
)
from aethos_core.providers.railway.env_value_readiness.env_readiness_summary_renderer import (
    render_compact_env_readiness_report,
)
from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
    credential_center_path,
)


def _source_label(source: str | None) -> str:
    labels = {
        "deployment_default": "deployment default",
        "credential_center": "credential center",
        "local_env_dev_only": "local env (dev only)",
        "plan_default": "plan default",
    }
    return labels.get(str(source or ""), str(source or "unknown"))


def render_env_value_readiness_report(state: dict[str, Any]) -> str:
    project = str(state.get("project") or "—")
    environment = str(state.get("environment") or "—")
    service = str(state.get("service_name") or "—")
    repo = str(state.get("repo") or "—")
    ready = bool(state.get("ready"))
    ready_mode = str(state.get("ready_mode") or ("ready" if ready else "blocked"))
    profile = str(state.get("env_profile") or state.get("deployment_profile") or "railway_production")

    lines = [
        "# Railway Env Value Readiness",
        "",
        "Target:",
        f"- Repo: `{repo}`",
        f"- Project/environment: `{project}` / `{environment}`",
        f"- Service: `{service}`",
        "",
        "Env readiness:",
        f"- ready: **{'true' if ready else 'false'}**",
        f"- mode: {ready_mode}",
        f"- env_profile: {profile}",
        "",
    ]

    critical_missing = list(state.get("critical_missing") or state.get("missing") or [])
    if critical_missing:
        lines.append("Critical secrets/config missing:")
        for name in critical_missing:
            crit = classify_env_var(name, profile=profile)
            kind = "required secret" if crit == EnvCriticality.CRITICAL_SECRET else "critical runtime"
            lines.append(f"- `{name}` — {kind}, not configured")
        lines.append("")

    configured_secrets = list(state.get("critical_secrets_configured") or [])
    if configured_secrets:
        lines.append("Critical secrets configured:")
        for name in configured_secrets:
            lines.append(f"- `{name}`")
        lines.append("")

    configured: list[str] = []
    for name in list(state.get("required_env_names") or []):
        entry = dict((state.get("values") or {}).get(name) or {})
        if entry.get("present") and not entry.get("using_default") and name not in configured_secrets:
            configured.append(name)
    if configured:
        lines.append("Configured:")
        for name in configured:
            entry = dict((state.get("values") or {}).get(name) or {})
            lines.append(f"- `{name}` — present via {_source_label(entry.get('source'))}")
        lines.append("")

    defaults = list(state.get("using_defaults") or [])
    if defaults:
        lines.append("Using deployment defaults:")
        for row in defaults:
            lines.append(f"- `{row.get('name')}`={row.get('value')}")
        lines.append("")

    optional_missing = list(state.get("optional_missing") or [])
    if optional_missing:
        lines.append("Optional feature config not configured:")
        for name in optional_missing:
            lines.append(f"- `{name}`")
        lines.append("")

    ignored = list(state.get("ignored_dev_only") or [])
    if ignored:
        lines.append("Ignored development-only config:")
        for name in ignored[:12]:
            lines.append(f"- `{name}`")
        if len(ignored) > 12:
            lines.append(f"- …and {len(ignored) - 12} more")
        lines.append("")

    lines.extend(
        [
            "How to configure:",
            credential_center_path(project=project, environment=environment, service_name=service),
            "",
            "No secret values should be pasted into chat.",
            "No Railway env vars have been written.",
            "No service has been created.",
        ]
    )
    return "\n".join(lines)


def render_configure_securely_guide(*, state: dict[str, Any]) -> str:
    project = str(state.get("project") or "—")
    environment = str(state.get("environment") or "—")
    service = str(state.get("service_name") or "—")
    profile = str(state.get("deployment_profile") or "railway_production")
    secrets = [
        n
        for n in state.get("required_env_names") or []
        if classify_env_var(str(n), profile=profile) == EnvCriticality.CRITICAL_SECRET
    ]
    runtime = [
        n
        for n in state.get("required_env_names") or []
        if classify_env_var(str(n), profile=profile) == EnvCriticality.CRITICAL_RUNTIME
    ]
    lines = [
        "Configure env values through a secure path, not chat.",
        "",
        "Recommended:",
        credential_center_path(project=project, environment=environment, service_name=service),
        "",
    ]
    if secrets:
        lines.append("Required secret values:")
        for name in secrets:
            lines.append(f"- `{name}`")
        lines.append("")
    if runtime:
        lines.append("Required non-secret values:")
        for name in runtime:
            lines.append(f"- `{name}`")
        lines.append("")
    lines.extend(
        [
            "After configuring, run:",
            "`refresh railway env readiness`",
            "",
            "No secret values will be displayed.",
            "No Railway env vars have been written yet.",
        ]
    )
    return "\n".join(lines)


def render_mark_configured_reply() -> str:
    return "\n".join(
        [
            "I can record that you attempted to configure env values, but I still need to verify secure presence.",
            "",
            "Run:",
            "`refresh railway env readiness`",
            "",
            "If secure store lookup succeeds you will see `ready: true`. No secret values will be displayed.",
            "No Railway env vars have been written yet.",
        ]
    )


def render_refresh_reply(state: dict[str, Any]) -> str:
    ready = bool(state.get("ready"))
    body = render_compact_env_readiness_report(state)
    if ready:
        return "\n".join(
            [
                "Env value readiness refreshed.",
                "",
                body.split("Env readiness:", 1)[-1].strip() if "Env readiness:" in body else body,
                "",
                "No secret values were displayed.",
                "No Railway env vars have been written yet.",
            ]
        )
    return "\n".join(
        [
            "Env value readiness refreshed.",
            "",
            body,
        ]
    )
