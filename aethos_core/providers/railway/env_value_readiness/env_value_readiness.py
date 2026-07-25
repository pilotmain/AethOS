# SPDX-License-Identifier: Apache-2.0
"""Assess Railway deployment env value readiness — presence metadata only."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.providers.railway.env_value_readiness.env_classification import (
    EnvCriticality,
    classify_env_var,
    default_runtime_value,
    infer_deployment_profile,
    is_ignored_for_profile,
    is_secret_env_name,  # re-exported for callers
)
from aethos_core.providers.railway.env_value_readiness.env_minimum_secret_sets import (
    assess_minimum_secret_set,
    should_block_env_for_readiness,
)
from aethos_core.providers.railway.env_value_readiness.env_operational_tiers import (
    EnvOperationalTier,
    classify_operational_tier,
)
from aethos_core.providers.railway.env_value_readiness.env_presence_confidence import (
    EnvPresenceConfidence,
    resolve_presence_confidence,
)
from aethos_core.providers.railway.env_value_readiness.env_rotation_metadata import (
    attach_rotation_metadata,
)

_PROVIDER_ENV_MAP: dict[str, str] = {
    "OPENAI_API_KEY": "openai",
    "ANTHROPIC_API_KEY": "anthropic",
    "GITHUB_TOKEN": "github",
    "GH_TOKEN": "github",
    "RAILWAY_API_TOKEN": "railway",
    "VERCEL_TOKEN": "vercel",
    "VERCEL_API_TOKEN": "vercel",
    "WEB_SEARCH_API_KEY": "tavily",
    "TAVILY_API_KEY": "tavily",
    "RESEND_API_KEY": "resend",
    "STRIPE_SECRET_KEY": "stripe",
    "STRIPE_API_KEY": "stripe",
    "SUPABASE_SERVICE_ROLE_KEY": "supabase",
    "SUPABASE_ACCESS_TOKEN": "supabase",
    "PLAID_CLIENT_ID": "plaid",
    "PLAID_SECRET": "plaid",
}


def credential_center_path(*, project: str, environment: str, service_name: str) -> str:
    return (
        f"AethOS Credential Center → Deployment env values → Railway → "
        f"{project} / {environment} / {service_name}"
    )


def build_target_key(*, repo: str, project: str, environment: str, service_name: str) -> str:
    return "|".join(
        [
            (repo or "").strip().lower(),
            (project or "").strip().lower(),
            (environment or "").strip().lower(),
            (service_name or "").strip().lower(),
        ]
    )


def _load_execution_mode() -> str:
    try:
        from aethos_core.providers.railway.execution_contract.execution_enablement import (
            load_railway_execution_enablement_config,
        )

        return str(load_railway_execution_enablement_config().mode or "disabled")
    except Exception:
        return "disabled"


def _enrich_entry(
    *,
    name: str,
    entry: dict[str, Any],
    profile: str,
    target_key: str,
) -> dict[str, Any]:
    criticality = classify_env_var(name, profile=profile)
    enriched = attach_rotation_metadata(name, dict(entry), target_key=target_key)
    enriched["criticality"] = criticality.value
    enriched["operational_tier"] = classify_operational_tier(name, profile=profile).value
    enriched["secret"] = criticality == EnvCriticality.CRITICAL_SECRET or bool(entry.get("secret"))
    enriched["using_default"] = bool(entry.get("using_default"))
    enriched["confidence"] = resolve_presence_confidence(enriched).value
    if enriched["using_default"]:
        enriched.pop("default_value", None)
    return enriched


def compute_env_readiness_score(*, state: dict[str, Any]) -> int:
    score = 100
    score -= 25 * len(list(state.get("critical_blockers") or []))
    score -= 10 * len(list(state.get("stale_secrets") or []))
    score -= 2 * len(list(state.get("optional_missing") or []))
    if not state.get("minimum_secret_set_complete"):
        score -= 15
    return max(0, min(100, score))


def compute_env_readiness_confidence(*, state: dict[str, Any]) -> str:
    if state.get("critical_blockers"):
        return "low"
    if not state.get("minimum_secret_set_complete"):
        return "low"
    if state.get("stale_secrets"):
        return "medium"
    if state.get("optional_missing") or state.get("using_default_names"):
        return "medium"
    if state.get("ready"):
        return "high"
    return "medium"


def assess_env_value_readiness(*, plan: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.providers.railway.env_value_readiness.env_value_inventory import (
        probe_env_var_presence,
    )

    profile = infer_deployment_profile(plan)
    execution_mode = _load_execution_mode()
    target_key = build_target_key(
        repo=str(plan.get("repo") or ""),
        project=str(plan.get("project") or ""),
        environment=str(plan.get("environment") or ""),
        service_name=str(plan.get("service_name") or ""),
    )
    names = sorted({str(n).strip() for n in (plan.get("required_env_var_names") or []) if str(n).strip()})
    values: dict[str, dict[str, Any]] = {}
    critical_blockers: list[str] = []
    optional_missing: list[str] = []
    using_default_names: list[str] = []
    ignored_dev_only: list[str] = []
    configured_securely: list[str] = []
    stale_secrets: list[str] = []
    observability_warnings: list[str] = []

    for name in names:
        entry = probe_env_var_presence(name, plan=plan, profile=profile)
        criticality = classify_env_var(name, profile=profile)
        tier = classify_operational_tier(name, profile=profile)

        if is_ignored_for_profile(criticality, profile=profile):
            entry = {
                **entry,
                "present": False,
                "ignored": True,
                "criticality": criticality.value,
            }
            ignored_dev_only.append(name)
            values[name] = _enrich_entry(name=name, entry=entry, profile=profile, target_key=target_key)
            continue

        if not entry.get("present"):
            default = default_runtime_value(name, profile=profile)
            if default and criticality in {
                EnvCriticality.CRITICAL_RUNTIME,
                EnvCriticality.DEFAULTABLE_RUNTIME,
            }:
                default_value, default_source = default
                entry = {
                    "present": True,
                    "source": default_source,
                    "secret": False,
                    "using_default": True,
                    "criticality": criticality.value,
                }
                using_default_names.append(name)

        entry = _enrich_entry(name=name, entry=entry, profile=profile, target_key=target_key)
        values[name] = entry
        confidence = str(entry.get("confidence") or "")

        if confidence == EnvPresenceConfidence.STALE.value:
            stale_secrets.append(name)

        if entry.get("present"):
            if confidence in {
                EnvPresenceConfidence.CONFIRMED_PRESENT.value,
                EnvPresenceConfidence.INFERRED_PRESENT.value,
            } and entry.get("secret"):
                configured_securely.append(name)
            elif tier == EnvOperationalTier.OBSERVABILITY and not entry.get("using_default"):
                if confidence == EnvPresenceConfidence.MISSING.value:
                    observability_warnings.append(name)
            continue

        blocks = False
        if execution_mode == "dry_run":
            blocks = should_block_env_for_readiness(
                name,
                profile=profile,
                present=False,
                execution_mode=execution_mode,
            )
        else:
            from aethos_core.providers.railway.env_value_readiness.env_classification import (
                should_block_deployment,
            )

            blocks = should_block_deployment(name, profile=profile, present=False)

        if blocks:
            critical_blockers.append(name)
        elif tier == EnvOperationalTier.OBSERVABILITY:
            observability_warnings.append(name)
        elif tier in {
            EnvOperationalTier.OPTIONAL_FEATURE,
            EnvOperationalTier.REQUIRED_FOR_INTEGRATIONS,
        }:
            optional_missing.append(name)
        elif criticality == EnvCriticality.OPTIONAL_FEATURE:
            optional_missing.append(name)
        elif criticality == EnvCriticality.DEFAULTABLE_RUNTIME:
            optional_missing.append(name)

    minimum_secret_set = assess_minimum_secret_set(
        profile=profile,
        values=values,
        plan_env_names=names,
    )
    minimum_complete = bool(minimum_secret_set.get("complete"))

    blocking = bool(critical_blockers)
    ready = not blocking and bool(names)
    if execution_mode == "dry_run" and names:
        ready = minimum_complete and not blocking

    if not names:
        ready = False

    uses_defaults = bool(using_default_names)
    ready_mode = "blocked"
    if ready:
        ready_mode = "pass_with_defaults" if uses_defaults or optional_missing else "ready"

    state = {
        "repo": str(plan.get("repo") or ""),
        "branch": str(plan.get("branch") or "main"),
        "project": str(plan.get("project") or ""),
        "environment": str(plan.get("environment") or ""),
        "service_name": str(plan.get("service_name") or ""),
        "deployment_profile": profile,
        "env_profile": profile,
        "execution_mode": execution_mode,
        "target_key": target_key,
        "required_env_names": names,
        "values": values,
        "ready": ready,
        "ready_mode": ready_mode,
        "ready_for_dry_run": minimum_complete and not blocking,
        "missing": list(critical_blockers),
        "critical_missing": list(critical_blockers),
        "critical_blockers": critical_blockers,
        "optional_missing": optional_missing,
        "using_defaults": [{"name": n} for n in using_default_names],
        "using_default_names": using_default_names,
        "ignored_dev_only": ignored_dev_only,
        "configured_securely": configured_securely,
        "critical_secrets_configured": [
            n
            for n in configured_securely
            if classify_env_var(n, profile=profile) == EnvCriticality.CRITICAL_SECRET
        ],
        "stale_secrets": stale_secrets,
        "observability_warnings": observability_warnings,
        "minimum_secret_set": minimum_secret_set,
        "minimum_secret_set_complete": minimum_complete,
        "critical_missing_count": len(critical_blockers),
        "configured_securely_count": len(configured_securely),
        "optional_missing_count": len(optional_missing),
        "defaulted_count": len(using_default_names),
        "ignored_dev_only_count": len(ignored_dev_only),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    state["env_readiness_score"] = compute_env_readiness_score(state=state)
    state["env_readiness_confidence"] = compute_env_readiness_confidence(state=state)
    return state


def get_or_assess_env_value_readiness(
    *,
    plan: dict[str, Any],
    session_id: str = "default",
    force_refresh: bool = False,
) -> dict[str, Any]:
    from aethos_core.providers.railway.env_value_readiness.env_value_context import (
        get_env_value_readiness,
        save_env_value_readiness,
    )

    if not force_refresh:
        cached = get_env_value_readiness(session_id=session_id, plan=plan)
        if cached and list(cached.get("required_env_names") or []) == list(plan.get("required_env_var_names") or []):
            profile = infer_deployment_profile(plan)
            if cached.get("deployment_profile") == profile:
                return cached
    state = assess_env_value_readiness(plan=plan)
    save_env_value_readiness(session_id=session_id, state=state)
    return state


def append_env_value_readiness_section(
    body: str,
    *,
    plan: dict[str, Any],
    session_id: str = "default",
) -> str:
    names = list(plan.get("required_env_var_names") or [])
    if not names:
        return body
    state = get_or_assess_env_value_readiness(plan=plan, session_id=session_id)
    lines = format_env_value_readiness_lines(state)
    if not lines:
        return body
    return f"{body}\n\n" + "\n".join(lines)


def format_env_value_readiness_lines(state: dict[str, Any] | None) -> list[str]:
    if not state:
        return []
    ready = bool(state.get("ready"))
    ready_mode = str(state.get("ready_mode") or ("ready" if ready else "blocked"))
    lines = [
        "Env value readiness:",
        f"- ready: **{'true' if ready else 'false'}**",
        f"- mode: {ready_mode}",
        f"- env_profile: {state.get('env_profile') or state.get('deployment_profile') or 'railway_production'}",
        f"- critical blockers: {state.get('critical_missing_count', 0)}",
        f"- configured securely: {state.get('configured_securely_count', 0)}",
        f"- minimum_secret_set_complete: {str(state.get('minimum_secret_set_complete', False)).lower()}",
    ]
    score = state.get("env_readiness_score")
    if score is not None:
        lines.append(f"- env_readiness_score: {score}/100")
    confidence = state.get("env_readiness_confidence")
    if confidence:
        lines.append(f"- env_readiness_confidence: {confidence}")
    return lines
