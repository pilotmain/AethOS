# SPDX-License-Identifier: Apache-2.0
"""FIX 191 — chat router for cross-repository multi-agent delivery validation."""

from __future__ import annotations

from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_contract import (
    CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_ROUTE_ID,
    DEPLOY_AUTHORITY_FIX_191,
    GATE_BYPASS_ENABLED_FIX_191,
    MERGE_AUTHORITY_FIX_191,
    MUTATION_PERFORMED_FIX_191,
    PROVIDER_AUTHORITY_FIX_191,
    RAILWAY_AUTHORITY_FIX_191,
)
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_intent import (
    is_cross_repository_multi_agent_delivery_validation_intent,
    parse_cross_repository_multi_agent_delivery_validation_record_intent,
)
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_renderer import (
    render_cross_repository_multi_agent_delivery_validation,
)
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
    build_cross_repository_multi_agent_delivery_validation,
)
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_store import (
    append_cross_repository_multi_agent_delivery_validation_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_ROUTE_ID,
        "matched_module": (
            "mission_control.cross_repository_multi_agent_delivery_validation."
            "cross_repository_multi_agent_delivery_validation_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_191 is False else "true",
        "cross_repo_validation_grants_trust": "false"
        if CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191 is False
        else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_191 is False else "true",
        "deploy_authority": "false" if DEPLOY_AUTHORITY_FIX_191 is False else "true",
        "railway_authority": "false" if RAILWAY_AUTHORITY_FIX_191 is False else "true",
        "provider_authority": "false" if PROVIDER_AUTHORITY_FIX_191 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_191 is False else "true",
        "mutation_scope": "cross_repository_multi_agent_delivery_validation",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "cross_repo_validation_not_trust_granting",
        **extra,
    }


def route_cross_repository_multi_agent_delivery_validation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_cross_repository_multi_agent_delivery_validation_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        record, blockers = append_cross_repository_multi_agent_delivery_validation_record(
            session_id=session_id,
            kind=kind,
            content=content,
        )
        if blockers or not record:
            body = f"Cross-repo validation record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_cross_repository_multi_agent_delivery_validation_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Cross-repo validation record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Validation ≠ trust granting."
        )
        return (
            body,
            "mission_control_cross_repository_multi_agent_delivery_validation_record",
            _meta(session_id, stage="validation_record", record_id=str(record.get("record_id") or "")),
        )

    if not is_cross_repository_multi_agent_delivery_validation_intent(text):
        return None

    result = build_cross_repository_multi_agent_delivery_validation(session_id=session_id)
    body = render_cross_repository_multi_agent_delivery_validation(
        result.cross_repository_multi_agent_delivery_validation
    )
    return (
        body,
        "mission_control_cross_repository_multi_agent_delivery_validation",
        _meta(session_id, stage="cross_repository_multi_agent_delivery_validation"),
    )
