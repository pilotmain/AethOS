# SPDX-License-Identifier: Apache-2.0
"""Deployment-profile minimum viable secret sets."""

from __future__ import annotations

from aethos_core.providers.railway.env_value_readiness.env_classification import DeploymentProfile

PRODUCTION_ONLY_SECRETS: frozenset[str] = frozenset(
    {
        "TRIGGER_WEBHOOK_SECRET",
        "WEB_API_TOKEN",
    }
)

MINIMUM_SECRET_SETS: dict[str, tuple[str, ...]] = {
    DeploymentProfile.RAILWAY_STAGING.value: (
        "ANTHROPIC_API_KEY",
        "WEB_SEARCH_API_KEY",
    ),
    DeploymentProfile.RAILWAY_PRODUCTION.value: (
        "ANTHROPIC_API_KEY",
        "WEB_SEARCH_API_KEY",
        "TRIGGER_WEBHOOK_SECRET",
        "WEB_API_TOKEN",
    ),
    DeploymentProfile.HOSTED_CLOUD.value: (
        "ANTHROPIC_API_KEY",
        "WEB_SEARCH_API_KEY",
        "TRIGGER_WEBHOOK_SECRET",
        "WEB_API_TOKEN",
    ),
    DeploymentProfile.LOCAL_DEV.value: (
        "ANTHROPIC_API_KEY",
    ),
}

OPTIONAL_INTEGRATION_EXAMPLES: tuple[str, ...] = (
    "TELEGRAM_BOT_TOKEN",
    "NGROK_AUTHTOKEN",
)


def minimum_secrets_for_profile(profile: str) -> tuple[str, ...]:
    return MINIMUM_SECRET_SETS.get(profile) or MINIMUM_SECRET_SETS[DeploymentProfile.RAILWAY_PRODUCTION.value]


def production_only_secrets_for_profile(profile: str) -> tuple[str, ...]:
    if profile == DeploymentProfile.RAILWAY_STAGING.value:
        return tuple(PRODUCTION_ONLY_SECRETS)
    return ()


def assess_minimum_secret_set(
    *,
    profile: str,
    values: dict[str, dict],
    plan_env_names: list[str] | None = None,
) -> dict[str, object]:
    required = list(minimum_secrets_for_profile(profile))
    plan_set = {str(n).strip().upper() for n in (plan_env_names or []) if str(n).strip()}
    applicable = [name for name in required if name.upper() in plan_set] if plan_set else list(required)
    missing = [name for name in applicable if not (values.get(name) or {}).get("present")]
    return {
        "required": required,
        "applicable": applicable,
        "missing": missing,
        "complete": not missing,
    }


def should_block_env_for_readiness(
    name: str,
    *,
    profile: str,
    present: bool,
    execution_mode: str = "disabled",
) -> bool:
    """Whether a missing env should block readiness for the current execution context."""
    from aethos_core.providers.railway.env_value_readiness.env_classification import (
        classify_env_var,
        default_runtime_value,
        is_ignored_for_profile,
        should_block_deployment,
    )
    from aethos_core.providers.railway.env_value_readiness.env_operational_tiers import (
        EnvOperationalTier,
        classify_operational_tier,
    )

    if present:
        return False

    upper = (name or "").strip().upper()
    tier = classify_operational_tier(upper, profile=profile)
    criticality = classify_env_var(upper, profile=profile)

    if is_ignored_for_profile(criticality, profile=profile):
        return False

    mode = (execution_mode or "disabled").strip().lower()
    if mode == "dry_run":
        if upper in production_only_secrets_for_profile(profile):
            return False
        if tier in {
            EnvOperationalTier.OPTIONAL_FEATURE,
            EnvOperationalTier.OBSERVABILITY,
            EnvOperationalTier.LOCAL_DEV_ONLY,
        }:
            return False
        minimum = minimum_secrets_for_profile(profile)
        if upper in minimum:
            return True
        if tier == EnvOperationalTier.REQUIRED_FOR_BOOT:
            return default_runtime_value(upper, profile=profile) is None
        return False

    return should_block_deployment(upper, profile=profile, present=False)
