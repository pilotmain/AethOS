# SPDX-License-Identifier: Apache-2.0
"""Secure env readiness summaries — no secret values, hashes, or lengths."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.env_value_readiness.env_minimum_secret_sets import (
    OPTIONAL_INTEGRATION_EXAMPLES,
    minimum_secrets_for_profile,
    production_only_secrets_for_profile,
)
from aethos_core.providers.railway.env_value_readiness.env_presence_confidence import (
    EnvPresenceConfidence,
)
from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
    credential_center_path,
)


def secure_source_label(source: str | None) -> str:
    mapping = {
        "credential_center": "credential_center",
        "secure_store_reference": "secure_store_reference",
        "deployment_default": "deployment_defaults",
        "deployment_defaults": "deployment_defaults",
        "plan_default": "deployment_defaults",
        "local_env_dev_only": "local_process_env",
    }
    return mapping.get(str(source or ""), "secure_store_reference" if source else "unknown")


def _format_blocker(name: str, entry: dict[str, Any]) -> list[str]:
    tier = entry.get("operational_tier", "—")
    confidence = entry.get("confidence", EnvPresenceConfidence.MISSING.value)
    lines = [
        f"- {name}",
        f"  - tier: {tier}",
        f"  - confidence: {confidence}",
    ]
    if entry.get("rotation_state") and entry.get("rotation_state") != "unknown":
        lines.append(f"  - rotation_state: {entry.get('rotation_state')}")
    return lines


def _format_configured_securely(name: str, entry: dict[str, Any]) -> list[str]:
    lines = [
        f"- {name}",
        f"  - confidence: {entry.get('confidence', EnvPresenceConfidence.CONFIRMED_PRESENT.value)}",
        f"  - source: {secure_source_label(entry.get('source'))}",
    ]
    rotation = str(entry.get("rotation_state") or "")
    if rotation and rotation != "unknown":
        lines.append(f"  - rotation_state: {rotation}")
    return lines


def render_secure_env_readiness_summary(state: dict[str, Any]) -> str:
    project = str(state.get("project") or "—")
    environment = str(state.get("environment") or "—")
    service = str(state.get("service_name") or "—")
    profile = str(state.get("env_profile") or state.get("deployment_profile") or "railway_production")
    ready = bool(state.get("ready"))
    minimum = state.get("minimum_secret_set") or {}
    minimum_required = list(minimum.get("required") or minimum_secrets_for_profile(profile))

    lines = [
        "# Secure Railway Env Readiness",
        "",
        "Target:",
        f"- {project} / {environment} / {service}",
        "",
        "Deployment profile:",
        f"- {profile}",
        "",
        "Overall readiness:",
        f"- {'ready' if ready else 'blocked'}",
        "",
    ]

    blockers = list(state.get("critical_blockers") or [])
    if blockers:
        lines.append("Critical blockers:")
        for name in blockers:
            entry = dict((state.get("values") or {}).get(name) or {})
            lines.extend(_format_blocker(name, entry))
        lines.append("")

    configured = list(state.get("configured_securely") or [])
    if configured:
        lines.append("Configured securely:")
        for name in configured:
            entry = dict((state.get("values") or {}).get(name) or {})
            lines.extend(_format_configured_securely(name, entry))
        lines.append("")

    defaults = list(state.get("using_default_names") or [])
    if defaults:
        lines.append("Using defaults:")
        for name in defaults:
            lines.append(f"- {name}")
        lines.append("")

    optional = list(state.get("optional_missing") or [])
    if optional:
        lines.append("Optional integrations not configured:")
        for name in optional[:16]:
            lines.append(f"- {name}")
        if len(optional) > 16:
            lines.append(f"- …and {len(optional) - 16} more")
        lines.append("")

    ignored = list(state.get("ignored_dev_only") or [])
    if ignored:
        lines.append("Ignored local-dev config:")
        for name in ignored[:12]:
            lines.append(f"- {name}")
        if len(ignored) > 12:
            lines.append(f"- …and {len(ignored) - 12} more")
        lines.append("")

    stale = list(state.get("stale_secrets") or [])
    if stale:
        lines.append("Stale secret metadata (rotation review recommended):")
        for name in stale:
            entry = dict((state.get("values") or {}).get(name) or {})
            lines.append(f"- {name} — rotation_state: {entry.get('rotation_state', 'stale')}")
        lines.append("")

    lines.append(f"Minimum required secrets for {profile.replace('railway_', '')}:")
    for name in minimum_required:
        lines.append(f"- {name}")
    lines.append("")

    score = state.get("env_readiness_score")
    confidence = state.get("env_readiness_confidence")
    if score is not None:
        lines.append(f"Env readiness score: {score}/100 (informational)")
    if confidence:
        lines.append(f"Env readiness confidence: {confidence}")
    lines.extend(
        [
            "",
            "No secret values displayed.",
            "No Railway env vars written.",
            "No mutation performed.",
        ]
    )
    return "\n".join(lines)


def render_minimum_required_secrets(state: dict[str, Any]) -> str:
    project = str(state.get("project") or "—")
    environment = str(state.get("environment") or "—")
    service = str(state.get("service_name") or "—")
    profile = str(state.get("env_profile") or state.get("deployment_profile") or "railway_production")
    staging_minimum = list(minimum_secrets_for_profile("railway_staging"))
    production_minimum = list(minimum_secrets_for_profile("railway_production"))
    production_only = list(production_only_secrets_for_profile("railway_staging")) or list(
        production_only_secrets_for_profile("railway_production")
    )

    lines = [
        "# Minimum Required Secrets",
        "",
        "Target:",
        f"- {project} / {environment} / {service}",
        "",
        "Required for dry-run staging:",
    ]
    lines.extend(f"- {name}" for name in staging_minimum)
    lines.extend(
        [
            "",
            "Required only for production:",
        ]
    )
    lines.extend(f"- {name}" for name in production_only)
    lines.extend(
        [
            "",
            "Optional integrations:",
        ]
    )
    optional = list(state.get("optional_missing") or [])[:8]
    if optional:
        lines.extend(f"- {name}" for name in optional)
    else:
        lines.extend(f"- {name}" for name in OPTIONAL_INTEGRATION_EXAMPLES)
    lines.extend(
        [
            "",
            "No secret values displayed.",
            "No Railway env vars written.",
            "No mutation performed.",
        ]
    )
    return "\n".join(lines)


def render_compact_env_readiness_report(state: dict[str, Any]) -> str:
    """Enhanced check railway env value readiness — grouped operational summary."""
    project = str(state.get("project") or "—")
    environment = str(state.get("environment") or "—")
    service = str(state.get("service_name") or "—")
    repo = str(state.get("repo") or "—")
    ready = bool(state.get("ready"))
    ready_mode = str(state.get("ready_mode") or ("ready" if ready else "blocked"))
    profile = str(state.get("env_profile") or state.get("deployment_profile") or "railway_production")
    execution_mode = str(state.get("execution_mode") or "disabled")

    lines = [
        "# Railway Env Value Readiness",
        "",
        "Target:",
        f"- Repo: `{repo}`",
        f"- Project/environment: `{project}` / `{environment}`",
        f"- Service: `{service}`",
        "",
        "Summary:",
        f"- Critical blockers: {state.get('critical_missing_count', 0)}",
        f"- Configured securely: {state.get('configured_securely_count', 0)}",
        f"- Using defaults: {state.get('defaulted_count', 0)}",
        f"- Optional missing: {state.get('optional_missing_count', 0)}",
        f"- Ignored local-dev: {state.get('ignored_dev_only_count', 0)}",
        "",
        "Env readiness:",
        f"- ready: **{'true' if ready else 'false'}**",
        f"- mode: {ready_mode}",
        f"- env_profile: {profile}",
        f"- execution_mode: {execution_mode}",
        f"- minimum_secret_set_complete: **{str(state.get('minimum_secret_set_complete', False)).lower()}**",
    ]

    score = state.get("env_readiness_score")
    confidence = state.get("env_readiness_confidence")
    if score is not None:
        lines.append(f"- env_readiness_score: {score}/100")
    if confidence:
        lines.append(f"- env_readiness_confidence: {confidence}")

    blockers = list(state.get("critical_blockers") or state.get("critical_missing") or [])
    if blockers:
        lines.extend(["", "Critical blockers:"])
        for name in blockers[:12]:
            entry = dict((state.get("values") or {}).get(name) or {})
            lines.append(
                f"- `{name}` — tier: {entry.get('operational_tier', '—')}, "
                f"confidence: {entry.get('confidence', 'missing')}"
            )
        if len(blockers) > 12:
            lines.append(f"- …and {len(blockers) - 12} more")

    configured = list(state.get("configured_securely") or [])
    if configured:
        lines.extend(["", "Configured securely:"])
        for name in configured[:12]:
            entry = dict((state.get("values") or {}).get(name) or {})
            lines.append(f"- `{name}` — source: {secure_source_label(entry.get('source'))}")

    defaults = list(state.get("using_default_names") or [])
    if defaults:
        lines.extend(["", "Using defaults:"])
        for name in defaults[:12]:
            lines.append(f"- `{name}`")

    optional = list(state.get("optional_missing") or [])
    if optional:
        lines.extend(["", "Optional integrations not configured:"])
        for name in optional[:8]:
            lines.append(f"- `{name}`")

    ignored = list(state.get("ignored_dev_only") or [])
    if ignored:
        lines.extend(["", "Ignored local-dev config:"])
        for name in ignored[:8]:
            lines.append(f"- `{name}`")

    warnings = list(state.get("observability_warnings") or [])
    if warnings:
        lines.extend(["", "Observability warnings (non-blocking):"])
        for name in warnings[:6]:
            lines.append(f"- `{name}`")

    lines.extend(
        [
            "",
            "How to configure:",
            credential_center_path(project=project, environment=environment, service_name=service),
            "",
            "No secret values displayed.",
            "No Railway env vars have been written.",
            "No mutation performed.",
        ]
    )
    return "\n".join(lines)
