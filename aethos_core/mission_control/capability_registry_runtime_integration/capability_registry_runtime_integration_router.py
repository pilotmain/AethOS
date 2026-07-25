# SPDX-License-Identifier: Apache-2.0
"""FIX 296 — chat router for capability registry runtime integration."""

from __future__ import annotations

from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_contract import (
    AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_296,
    CAPABILITY_ANSWERING_AUTHORITY_FIX_296,
    CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_ROUTE_ID,
    PROVIDER_AUTHORITY_FIX_296,
    TRUST_MUTATION_AUTHORITY_FIX_296,
)
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_intent import (
    is_general_capability_question,
)
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_renderer import (
    render_capability_registry_runtime_integration,
)
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
    build_capability_registry_runtime_integration,
)


def _meta(session_id: str) -> dict[str, str]:
    return {
        "route_id": CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_ROUTE_ID,
        "matched_module": (
            "mission_control.capability_registry_runtime_integration."
            "capability_registry_runtime_integration_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "capability_answering_authority": "false"
        if CAPABILITY_ANSWERING_AUTHORITY_FIX_296 is False
        else "true",
        "automatic_capability_promotion_enabled": "false"
        if AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_296 is False
        else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_296 is False else "true",
        "provider_authority": "false" if PROVIDER_AUTHORITY_FIX_296 is False else "true",
        "mutation_scope": "capability_registry_runtime_integration",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": "view",
        "lane_separation": "capability_answering_not_authority",
        "runtime_answer_from_fix_295": "true",
        "provider_only_answer_forbidden": "true",
    }


def route_capability_registry_runtime_integration(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_general_capability_question(text):
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    result = build_capability_registry_runtime_integration(session_id=sid)
    markdown = render_capability_registry_runtime_integration(result.capability_registry_runtime_integration)
    summary = (
        (result.capability_registry_runtime_integration.get("sections") or {})
        .get("capability_summary", [{}])[0]
    )
    headline = (
        f"Platform maturity **{summary.get('overall_maturity_tier', '—')}** across "
        f"**{summary.get('capability_count', 0)}** registered capabilities from live evidence. "
        "Capability answering ≠ capability authority."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_capability_registry_runtime_integration",
        _meta(sid),
    )
