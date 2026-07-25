# SPDX-License-Identifier: Apache-2.0
"""Confidence restraint — suppress raw telemetry in casual contexts."""

from __future__ import annotations

_ENGINEERING_MODES = frozenset({"engineering", "operator", "debug", "mission_control"})


def should_show_telemetry(*, mode: str, intent: str = "") -> bool:
    if mode in _ENGINEERING_MODES:
        return True
    if intent in ("research_synthesis_engineering", "operational_brief", "mutation_reconciliation"):
        return True
    from aethos_core.providers.railway.deployment_plan.deployment_plan_presentation import (
        is_railway_deployment_plan_presentation_bypass,
    )

    if is_railway_deployment_plan_presentation_bypass(intent=intent):
        return True
    return False
