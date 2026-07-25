# SPDX-License-Identifier: Apache-2.0
"""Operational tiers for env vars — why a variable matters."""

from __future__ import annotations

from enum import Enum

from aethos_core.providers.railway.env_value_readiness.env_classification import (
    EnvCriticality,
    classify_env_var,
)


class EnvOperationalTier(str, Enum):
    REQUIRED_FOR_BOOT = "required_for_boot"
    REQUIRED_FOR_AI = "required_for_ai"
    REQUIRED_FOR_INTEGRATIONS = "required_for_integrations"
    OPTIONAL_FEATURE = "optional_feature"
    OBSERVABILITY = "observability"
    LOCAL_DEV_ONLY = "local_dev_only"


_OBSERVABILITY_NAMES = frozenset(
    {
        "SPLUNK_HEC_TOKEN",
        "SPLUNK_HEC_URL",
        "DATADOG_API_KEY",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
    }
)

_AI_SECRETS = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "WEB_SEARCH_API_KEY",
    }
)

_INTEGRATION_PREFIXES = ("TELEGRAM_", "NGROK_", "TRIGGER_")


def classify_operational_tier(name: str, *, profile: str = "railway_production") -> EnvOperationalTier:
    upper = (name or "").strip().upper()
    if not upper:
        return EnvOperationalTier.OPTIONAL_FEATURE

    criticality = classify_env_var(upper, profile=profile)
    if criticality == EnvCriticality.DEVELOPMENT_ONLY:
        return EnvOperationalTier.LOCAL_DEV_ONLY
    if upper in _OBSERVABILITY_NAMES or "SPLUNK" in upper or "OTEL" in upper:
        return EnvOperationalTier.OBSERVABILITY
    if upper in _AI_SECRETS or (criticality == EnvCriticality.CRITICAL_SECRET and "API_KEY" in upper):
        return EnvOperationalTier.REQUIRED_FOR_AI
    if any(upper.startswith(prefix) for prefix in _INTEGRATION_PREFIXES):
        if criticality == EnvCriticality.OPTIONAL_FEATURE:
            return EnvOperationalTier.OPTIONAL_FEATURE
        return EnvOperationalTier.REQUIRED_FOR_INTEGRATIONS
    if criticality in {EnvCriticality.CRITICAL_RUNTIME, EnvCriticality.DEFAULTABLE_RUNTIME}:
        return EnvOperationalTier.REQUIRED_FOR_BOOT
    if criticality == EnvCriticality.OPTIONAL_FEATURE:
        return EnvOperationalTier.OPTIONAL_FEATURE
    if criticality == EnvCriticality.CRITICAL_SECRET:
        return EnvOperationalTier.REQUIRED_FOR_AI
    return EnvOperationalTier.OPTIONAL_FEATURE
