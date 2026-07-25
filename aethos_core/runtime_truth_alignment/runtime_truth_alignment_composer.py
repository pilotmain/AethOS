# SPDX-License-Identifier: Apache-2.0
"""FIX 316A — runtime truth alignment response composers."""

from __future__ import annotations

from typing import Any

from aethos_core.identity_truth_lock.identity_truth_lock_responses import (
    compose_creator_attribution_response as _compose_creator_introduction,
    compose_platform_identity_response as _compose_self_introduction,
)


def _safe_capability_evidence(*, session_id: str) -> dict[str, Any]:
    try:
        from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
            build_capability_registry_runtime_integration,
        )

        result = build_capability_registry_runtime_integration(session_id=session_id)
        board = result.capability_registry_runtime_integration
        sections = board.get("sections") or {}
        summary = (sections.get("capability_summary") or [{}])[0]
        proven = (sections.get("proven_capabilities") or [{}])[0]
        operational = (sections.get("operational_capabilities") or [{}])[0]
        authority = (sections.get("authority_boundaries") or [{}])[0]
        provider_matrix = (sections.get("provider_capability_matrix") or [{}])[0]
        return {
            "summary": summary,
            "proven_items": list(proven.get("items") or [])[:6],
            "operational_items": list(operational.get("items") or [])[:4],
            "authority_note": str(authority.get("summary") or authority.get("detail") or ""),
            "provider_readiness": list(provider_matrix.get("providers") or [])[:4],
            "maturity_tier": summary.get("overall_maturity_tier"),
        }
    except Exception:
        return {}


def compose_platform_identity_response(*, session_id: str = "default") -> str:
    return _compose_self_introduction(session_id=session_id)


def compose_creator_attribution_response(*, focus: str = "creator") -> str:
    return _compose_creator_introduction(focus=focus)


def compose_capability_response(*, session_id: str = "default") -> str:
    from aethos_core.identity.plain_capability_intro import compose_plain_capability_overview_reply

    return compose_plain_capability_overview_reply(session_id=session_id)


def compose_human_support_response() -> str:
    return "\n".join(
        [
            "I'm sorry you're going through this. Your wellbeing matters more than any operational task.",
            "",
            "I'm an operational intelligence platform, not a clinician or crisis counselor. "
            "If you're in immediate danger or thinking about harming yourself, please contact local emergency services "
            "or a crisis line in your country right now.",
            "",
            "If you can, reach out to someone you trust — a friend, family member, manager, or mental health professional. "
            "You don't have to carry this alone.",
            "",
            "When you're ready, I'm here for calm, practical help with work or systems — at your pace.",
        ]
    )
