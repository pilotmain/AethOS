# SPDX-License-Identifier: Apache-2.0
"""Env var criticality classification and deployment profile defaults."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

_SECRET_SUFFIXES = ("_KEY", "_TOKEN", "_SECRET", "_PASSWORD", "_AUTH")
_SECRET_EXACT = frozenset(
    {
        "DATABASE_URL",
        "REDIS_URL",
        "TRIGGER_WEBHOOK_SECRET",
        "NGROK_AUTHTOKEN",
        "WEB_API_TOKEN",
    }
)

_CRITICAL_SECRETS = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "WEB_SEARCH_API_KEY",
        "WEB_API_TOKEN",
        "TRIGGER_WEBHOOK_SECRET",
        "TELEGRAM_BOT_TOKEN",
        "NGROK_AUTHTOKEN",
        "GITHUB_TOKEN",
        "RAILWAY_API_TOKEN",
        "VERCEL_TOKEN",
    }
)

_CRITICAL_RUNTIME = frozenset(
    {
        "APP_ENV",
        "API_PORT",
        "PORT",
        "HOST",
        "ACTIVE_PROVIDER",
        "NODE_ENV",
        "ENVIRONMENT",
        "DEPLOYMENT_MODE",
    }
)

_DEFAULTABLE_RUNTIME = frozenset(
    {
        "BROWSER_HEADLESS",
        "BROWSER_AUTOMATION_ENABLED",
        "BROWSER_PROVIDER",
        "BROWSER_CAPTURE_APPROVAL_REQUIRED",
        "WORKER_MODE",
        "WEB_RESEARCH_ENABLED",
        "WEB_SEARCH_PROVIDER",
        "JOB_MAX_RUNTIME_SEC",
        "JOB_PROVIDER_TIMEOUT_SEC",
        "TELEGRAM_ENABLED",
        "TELEGRAM_TYPING_ENABLED",
        "WEB_RESEARCH_MAX_RESULTS",
        "LOG_LEVEL",
        "USE_REAL_LLM",
        "ANTHROPIC_MODEL",
        "TRIGGER_ENABLED",
        "TRIGGER_ENV",
        "TRIGGER_DEFAULT_TIMEOUT_SECONDS",
        "TRIGGER_MAX_RETRIES",
        "TRIGGER_RETRY_BACKOFF_SECONDS",
        "TRIGGER_STALE_CALLBACK_MINUTES",
        "TRIGGER_ORPHANED_JOB_MINUTES",
        "TELEGRAM_TUNNEL_ENABLED",
        "TUNNEL_PROVIDER",
        "NGROK_REGION",
        "NGROK_TARGET_PORT",
        "HOSTED_CLOUD_ENABLED",
        "WEB_USER_ID",
    }
)

_OPTIONAL_FEATURE = frozenset(
    {
        "NGROK_DOMAIN",
        "TELEGRAM_PROGRESS_MESSAGE_ENABLED",
        "TELEGRAM_TYPING_INTERVAL_SECONDS",
        "TELEGRAM_PROGRESS_AFTER_SECONDS",
        "EDGE_RUNTIME_ENABLED",
        "HOST_EXECUTOR_ENABLED",
        "TRIGGER_API_KEY",
        "TRIGGER_PROJECT_ID",
    }
)

_HOST_CONFIG_PREFIXES = (
    "RAILWAY_GREENFIELD_",
    "RAILWAY_PRODUCTION_",
    "AETHOS_SOLO_",
    "AETHOS_WORKSPACE_",
    "SOFTWARE_DELIVERY_",
    "MISSION_CONTROL_",
    "PROVIDER_E2E_",
)

_DEVELOPMENT_ONLY = frozenset(
    {
        "LOCAL_WORKSPACE_ARTIFACTS_DIR",
        "LOCAL_WORKSPACE_REGISTRY_DIR",
        "RESEARCH_ARTIFACTS_DIR",
        "AGENT_ARTIFACTS_DIR",
        "BROWSER_ARTIFACTS_DIR",
    }
)

_DEV_ONLY_SUFFIXES = ("_ARTIFACTS_DIR", "_REGISTRY_DIR", "_DIR")

_PROFILE_DEFAULTS: dict[str, dict[str, tuple[str, str]]] = {
    "railway_production": {
        "APP_ENV": ("production", "deployment_default"),
        "API_PORT": ("$PORT", "deployment_default"),
        "PORT": ("$PORT", "deployment_default"),
        "ACTIVE_PROVIDER": ("railway", "deployment_default"),
        "BROWSER_AUTOMATION_ENABLED": ("true", "deployment_default"),
        "BROWSER_PROVIDER": ("playwright", "deployment_default"),
        "BROWSER_HEADLESS": ("true", "deployment_default"),
        "TELEGRAM_ENABLED": ("false", "deployment_default"),
        "LOG_LEVEL": ("info", "deployment_default"),
        "WORKER_MODE": ("embedded", "deployment_default"),
        "WEB_RESEARCH_ENABLED": ("false", "deployment_default"),
        "WEB_SEARCH_PROVIDER": ("none", "deployment_default"),
        "JOB_MAX_RUNTIME_SEC": ("300", "deployment_default"),
        "JOB_PROVIDER_TIMEOUT_SEC": ("90", "deployment_default"),
        "WEB_RESEARCH_MAX_RESULTS": ("5", "deployment_default"),
        "TELEGRAM_TYPING_ENABLED": ("true", "deployment_default"),
        "DEPLOYMENT_MODE": ("hosted", "deployment_default"),
    },
    "railway_staging": {
        "APP_ENV": ("staging", "deployment_default"),
        "API_PORT": ("$PORT", "deployment_default"),
        "PORT": ("$PORT", "deployment_default"),
        "ACTIVE_PROVIDER": ("railway", "deployment_default"),
        "BROWSER_HEADLESS": ("true", "deployment_default"),
        "LOG_LEVEL": ("info", "deployment_default"),
    },
    "hosted_cloud": {
        "APP_ENV": ("production", "deployment_default"),
        "API_PORT": ("$PORT", "deployment_default"),
        "ACTIVE_PROVIDER": ("railway", "deployment_default"),
    },
    "local_dev": {
        "APP_ENV": ("development", "deployment_default"),
        "API_PORT": ("8010", "deployment_default"),
        "ACTIVE_PROVIDER": ("anthropic", "deployment_default"),
        "BROWSER_HEADLESS": ("false", "deployment_default"),
    },
}


class EnvCriticality(str, Enum):
    CRITICAL_SECRET = "critical_secret"
    CRITICAL_RUNTIME = "critical_runtime"
    DEFAULTABLE_RUNTIME = "defaultable_runtime"
    OPTIONAL_FEATURE = "optional_feature"
    DEVELOPMENT_ONLY = "development_only"


class DeploymentProfile(str, Enum):
    LOCAL_DEV = "local_dev"
    HOSTED_CLOUD = "hosted_cloud"
    RAILWAY_PRODUCTION = "railway_production"
    RAILWAY_STAGING = "railway_staging"


_RAILWAY_HOSTED_PROFILES = frozenset(
    {
        DeploymentProfile.RAILWAY_PRODUCTION.value,
        DeploymentProfile.RAILWAY_STAGING.value,
        DeploymentProfile.HOSTED_CLOUD.value,
    }
)


def is_secret_env_name(name: str) -> bool:
    upper = (name or "").strip().upper()
    if not upper:
        return False
    if upper in _SECRET_EXACT:
        return True
    return any(upper.endswith(suffix) for suffix in _SECRET_SUFFIXES)


def infer_deployment_profile(plan: dict[str, Any] | None) -> str:
    if not plan:
        return DeploymentProfile.RAILWAY_PRODUCTION.value
    explicit = str(plan.get("deployment_profile") or "").strip().lower()
    if explicit in {p.value for p in DeploymentProfile}:
        return explicit
    environment = str(plan.get("environment") or "").strip().lower()
    if environment in {"staging", "stage", "preview"}:
        return DeploymentProfile.RAILWAY_STAGING.value
    if environment in {"development", "dev", "local"}:
        return DeploymentProfile.LOCAL_DEV.value
    return DeploymentProfile.RAILWAY_PRODUCTION.value


def classify_env_var(name: str, *, profile: str = DeploymentProfile.RAILWAY_PRODUCTION.value) -> EnvCriticality:
    upper = (name or "").strip().upper()
    if not upper:
        return EnvCriticality.DEFAULTABLE_RUNTIME

    if upper in _DEVELOPMENT_ONLY:
        return EnvCriticality.DEVELOPMENT_ONLY
    if any(upper.startswith(prefix) for prefix in _HOST_CONFIG_PREFIXES):
        return EnvCriticality.DEVELOPMENT_ONLY
    if any(upper.endswith(suffix) for suffix in _DEV_ONLY_SUFFIXES):
        if any(token in upper for token in ("LOCAL", "ARTIFACT", "RESEARCH", "WORKSPACE", "REGISTRY")):
            return EnvCriticality.DEVELOPMENT_ONLY

    if upper in _OPTIONAL_FEATURE:
        return EnvCriticality.OPTIONAL_FEATURE
    if upper in _CRITICAL_SECRETS:
        return EnvCriticality.CRITICAL_SECRET
    if upper in _CRITICAL_RUNTIME:
        return EnvCriticality.CRITICAL_RUNTIME
    if upper in _DEFAULTABLE_RUNTIME:
        return EnvCriticality.DEFAULTABLE_RUNTIME

    if is_secret_env_name(upper):
        return EnvCriticality.CRITICAL_SECRET

    if upper.startswith(("TELEGRAM_", "NGROK_", "TRIGGER_", "EDGE_", "HOST_")):
        return EnvCriticality.OPTIONAL_FEATURE
    if upper.startswith(("BROWSER_", "WEB_RESEARCH", "WEB_SEARCH", "JOB_")):
        return EnvCriticality.DEFAULTABLE_RUNTIME

    return EnvCriticality.DEFAULTABLE_RUNTIME


def default_runtime_value(
    name: str,
    *,
    profile: str = DeploymentProfile.RAILWAY_PRODUCTION.value,
) -> tuple[str, str] | None:
    upper = (name or "").strip().upper()
    if not upper:
        return None
    profile_defaults = _PROFILE_DEFAULTS.get(profile) or _PROFILE_DEFAULTS[DeploymentProfile.RAILWAY_PRODUCTION.value]
    if upper in profile_defaults:
        return profile_defaults[upper]
    fallback = _PROFILE_DEFAULTS[DeploymentProfile.RAILWAY_PRODUCTION.value]
    return fallback.get(upper)


def is_ignored_for_profile(criticality: EnvCriticality, *, profile: str) -> bool:
    if criticality != EnvCriticality.DEVELOPMENT_ONLY:
        return False
    return profile in _RAILWAY_HOSTED_PROFILES


def should_block_deployment(
    name: str,
    *,
    profile: str = DeploymentProfile.RAILWAY_PRODUCTION.value,
    present: bool = False,
) -> bool:
    if present:
        return False
    criticality = classify_env_var(name, profile=profile)
    if is_ignored_for_profile(criticality, profile=profile):
        return False
    if criticality == EnvCriticality.CRITICAL_SECRET:
        return True
    if criticality == EnvCriticality.CRITICAL_RUNTIME:
        return default_runtime_value(name, profile=profile) is None
    return False
