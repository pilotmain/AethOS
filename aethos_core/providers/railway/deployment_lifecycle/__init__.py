# SPDX-License-Identifier: Apache-2.0
"""Canonical Railway new-service deployment lifecycle — readiness through simulation."""

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
    PlanCreationReadinessResolution,
    lifecycle_plan_snapshot,
    lifecycle_preflight_snapshot,
    lifecycle_readiness_checks,
    lifecycle_readiness_passed,
    lifecycle_simulation_snapshot,
    materialize_lifecycle_to_legacy_stores,
    resolve_readiness_for_plan_creation,
    resolve_readiness_checks_for_plan_creation,
    resolve_railway_deployment_lifecycle,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
    has_passed_readiness_without_plan,
    normalize_lifecycle_for_plan_creation,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    clear_for_tests,
)

__all__ = [
    "PlanCreationReadinessResolution",
    "clear_for_tests",
    "has_passed_readiness_without_plan",
    "lifecycle_plan_snapshot",
    "lifecycle_preflight_snapshot",
    "lifecycle_readiness_checks",
    "lifecycle_readiness_passed",
    "lifecycle_simulation_snapshot",
    "materialize_lifecycle_to_legacy_stores",
    "normalize_lifecycle_for_plan_creation",
    "resolve_readiness_for_plan_creation",
    "resolve_readiness_checks_for_plan_creation",
    "resolve_railway_deployment_lifecycle",
]
