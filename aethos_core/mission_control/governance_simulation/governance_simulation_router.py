# SPDX-License-Identifier: Apache-2.0
"""FIX 144 — chat router for governance simulation."""

from __future__ import annotations

from aethos_core.mission_control.governance_simulation.governance_simulation_contract import (
    AUTOMATIC_GOVERNANCE_TUNING_ENABLED_FIX_144,
    AUTO_POLICY_UPDATE_ENABLED_FIX_144,
    GOVERNANCE_SIMULATION_ROUTE_ID,
    LIVE_POLICY_MUTATION_ENABLED_FIX_144,
    MUTATION_PERFORMED_FIX_144,
)
from aethos_core.mission_control.governance_simulation.governance_simulation_intent import (
    is_governance_simulation_intent,
)
from aethos_core.mission_control.governance_simulation.governance_simulation_renderer import (
    render_governance_simulation,
)
from aethos_core.mission_control.governance_simulation.governance_simulation_service import run_governance_simulation


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNANCE_SIMULATION_ROUTE_ID,
        "matched_module": "mission_control.governance_simulation.governance_simulation_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_144 is False else "true",
        "live_policy_mutation_enabled": "false" if LIVE_POLICY_MUTATION_ENABLED_FIX_144 is False else "true",
        "simulation_only": "true",
        "mutation_scope": "governance_simulation_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "simulation_not_mutation",
        **extra,
    }


def route_governance_simulation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_governance_simulation_intent(text):
        return None

    result = run_governance_simulation(session_id=session_id)
    if not result.ok:
        body = f"Governance simulation unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_governance_simulation_blocked", _meta(session_id, stage="blocked")

    body = render_governance_simulation(result.simulation)
    return (
        body,
        "mission_control_governance_simulation",
        _meta(
            session_id,
            stage="governance_simulation",
            scenarios=str((result.simulation.get("impact_summary") or {}).get("scenarios_run", 0)),
        ),
    )
