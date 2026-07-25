# SPDX-License-Identifier: Apache-2.0
"""FIX 295 — chat router for autonomous capability registry."""

from __future__ import annotations

from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_contract import (
    AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_295,
    AUTONOMOUS_CAPABILITY_REGISTRY_ROUTE_ID,
    CAPABILITY_AUTHORITY_FIX_295,
    GATE_BYPASS_ENABLED_FIX_295,
    MERGE_AUTHORITY_FIX_295,
    MUTATION_PERFORMED_FIX_295,
    PROVIDER_MUTATION_AUTHORITY_FIX_295,
    REPOSITORY_MUTATION_AUTHORITY_FIX_295,
    SELF_AUTHORITY_GRANTING_ENABLED_FIX_295,
    TRUST_MUTATION_AUTHORITY_FIX_295,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_intent import (
    handle_autonomous_capability_registry_intent,
    parse_autonomous_capability_registry_intent,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_renderer import (
    render_autonomous_capability_registry,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
    build_autonomous_capability_registry,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": AUTONOMOUS_CAPABILITY_REGISTRY_ROUTE_ID,
        "matched_module": (
            "mission_control.autonomous_capability_registry."
            "autonomous_capability_registry_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_295 is False else "true",
        "capability_authority": "false" if CAPABILITY_AUTHORITY_FIX_295 is False else "true",
        "self_authority_granting_enabled": "false"
        if SELF_AUTHORITY_GRANTING_ENABLED_FIX_295 is False
        else "true",
        "automatic_capability_promotion_enabled": "false"
        if AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_295 is False
        else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_295 is False else "true",
        "repository_mutation_authority": "false"
        if REPOSITORY_MUTATION_AUTHORITY_FIX_295 is False
        else "true",
        "provider_mutation_authority": "false"
        if PROVIDER_MUTATION_AUTHORITY_FIX_295 is False
        else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_295 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_295 is False else "true",
        "mutation_scope": "autonomous_capability_registry",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "capability_awareness_not_authority",
        **extra,
    }


def route_autonomous_capability_registry(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_autonomous_capability_registry_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_autonomous_capability_registry_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded capability registry note ({record.get('kind', 'note')}). "
            "Capability awareness ≠ capability authority."
        )
        return (
            body,
            "mission_control_autonomous_capability_registry_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "dashboard")
    result = build_autonomous_capability_registry(session_id=sid)
    markdown = render_autonomous_capability_registry(
        result.autonomous_capability_registry,
        focus=focus,
    )
    self_awareness = (
        (result.autonomous_capability_registry.get("sections") or {})
        .get("self_awareness_report", [{}])[0]
    )
    maturity = (
        (result.autonomous_capability_registry.get("sections") or {})
        .get("capability_maturity_dashboard", [{}])[0]
    )
    headline = (
        f"Platform maturity **{maturity.get('capability_maturity_tier', '—')}**. "
        f"I can do **{len(self_awareness.get('what_can_you_do') or [])}** proven/advisory capabilities "
        f"from live evidence. Capability awareness ≠ capability authority."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_autonomous_capability_registry",
        _meta(sid, stage="view", focus=focus),
    )
