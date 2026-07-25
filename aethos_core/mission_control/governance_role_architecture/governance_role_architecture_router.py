# SPDX-License-Identifier: Apache-2.0
"""FIX 150 — chat router for governance role architecture."""

from __future__ import annotations

from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_contract import (
    AUTONOMOUS_ROLE_ELEVATION_ENABLED_FIX_150,
    DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_150,
    GOVERNANCE_ROLE_ARCHITECTURE_ROUTE_ID,
    MUTATION_PERFORMED_FIX_150,
)
from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_intent import (
    is_governance_role_architecture_intent,
)
from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_renderer import (
    render_governance_role_architecture,
)
from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_service import (
    build_governance_role_architecture,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNANCE_ROLE_ARCHITECTURE_ROUTE_ID,
        "matched_module": "mission_control.governance_role_architecture.governance_role_architecture_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_150 is False else "true",
        "delegated_execution_authority_enabled": "false"
        if DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_150 is False
        else "true",
        "autonomous_role_elevation_enabled": "false"
        if AUTONOMOUS_ROLE_ELEVATION_ENABLED_FIX_150 is False
        else "true",
        "mutation_scope": "governance_role_architecture_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "topology_not_execution",
        **extra,
    }


def route_governance_role_architecture(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_governance_role_architecture_intent(text):
        return None

    result = build_governance_role_architecture(session_id=session_id)
    if not result.ok:
        body = f"Governance role architecture unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_governance_role_architecture_blocked", _meta(session_id, stage="blocked")

    body = render_governance_role_architecture(result.architecture)
    reviewers = len((result.architecture.get("sections") or {}).get("governance_role_taxonomy") or [])
    return (
        body,
        "mission_control_governance_role_architecture",
        _meta(
            session_id,
            stage="governance_role_architecture",
            role_taxonomy_count=str(reviewers),
        ),
    )
