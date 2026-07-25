# SPDX-License-Identifier: Apache-2.0
"""Filter .env.example keys down to Railway deployment-relevant names."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.env_value_readiness.env_classification import (
    EnvCriticality,
    classify_env_var,
    infer_deployment_profile,
    is_ignored_for_profile,
    should_block_deployment,
)
from aethos_core.providers.railway.env_value_readiness.env_minimum_secret_sets import (
    OPTIONAL_INTEGRATION_EXAMPLES,
    minimum_secrets_for_profile,
    production_only_secrets_for_profile,
)


def filter_greenfield_deployment_env_var_names(
    names: list[str],
    *,
    plan: dict[str, Any] | None = None,
) -> list[str]:
    """Keep secrets and runtime vars that must be resolved before deploy — not host config."""
    if str((plan or {}).get("deploy_component") or "") == "ui":
        from aethos_core.providers.railway.greenfield_deployment.greenfield_deploy_component import (
            ui_required_env_var_names,
        )

        return list(ui_required_env_var_names())
    profile = infer_deployment_profile(plan)
    minimum = {str(name).strip().upper() for name in minimum_secrets_for_profile(profile)}
    prod_only = {str(name).strip().upper() for name in production_only_secrets_for_profile(profile)}
    optional = {str(name).strip().upper() for name in OPTIONAL_INTEGRATION_EXAMPLES}
    filtered: set[str] = set(minimum)
    for raw in names:
        upper = str(raw or "").strip().upper()
        if not upper or upper in prod_only or upper in optional:
            continue
        criticality = classify_env_var(upper, profile=profile)
        if is_ignored_for_profile(criticality, profile=profile):
            continue
        if criticality == EnvCriticality.CRITICAL_SECRET:
            filtered.add(upper)
            continue
        if should_block_deployment(upper, profile=profile, present=False):
            filtered.add(upper)
    filtered -= prod_only
    filtered |= minimum
    return sorted(filtered)
