# SPDX-License-Identifier: Apache-2.0
"""FIX 250 — chat router for governed application generation."""

from __future__ import annotations

from aethos_core.mission_control.governed_application_generation.governed_application_generation_contract import (
    APPLICATION_GENERATION_AUTHORITY_FIX_250,
    CODE_GENERATION_AUTHORITY_FIX_250,
    DEPLOYMENT_AUTHORITY_FIX_250,
    GATE_BYPASS_ENABLED_FIX_250,
    GITHUB_MUTATION_AUTHORITY_FIX_250,
    GOVERNED_APPLICATION_GENERATION_ROUTE_ID,
    MERGE_AUTHORITY_FIX_250,
    MUTATION_PERFORMED_FIX_250,
    PROVIDER_AUTHORITY_FIX_250,
    REPOSITORY_CREATION_AUTHORITY_FIX_250,
    ROLLBACK_AUTHORITY_FIX_250,
)
from aethos_core.mission_control.governed_application_generation.governed_application_generation_intent import (
    is_governed_application_generation_handoff_intent,
    is_governed_application_generation_intent,
    parse_governed_application_generation_record_intent,
)
from aethos_core.mission_control.governed_application_generation.governed_application_generation_renderer import (
    render_governed_application_generation,
)
from aethos_core.mission_control.governed_application_generation.governed_application_generation_service import (
    build_governed_application_generation,
    prepare_governed_application_generation_handoff,
)
from aethos_core.mission_control.governed_application_generation.governed_application_generation_store import (
    append_governed_application_generation_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_APPLICATION_GENERATION_ROUTE_ID,
        "matched_module": (
            "mission_control.governed_application_generation.governed_application_generation_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_250 is False else "true",
        "application_generation_authority": "false"
        if APPLICATION_GENERATION_AUTHORITY_FIX_250 is False
        else "true",
        "repository_creation_authority": "false"
        if REPOSITORY_CREATION_AUTHORITY_FIX_250 is False
        else "true",
        "github_mutation_authority": "false"
        if GITHUB_MUTATION_AUTHORITY_FIX_250 is False
        else "true",
        "code_generation_authority": "false"
        if CODE_GENERATION_AUTHORITY_FIX_250 is False
        else "true",
        "deployment_authority": "false" if DEPLOYMENT_AUTHORITY_FIX_250 is False else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_250 is False else "true",
        "rollback_authority": "false" if ROLLBACK_AUTHORITY_FIX_250 is False else "true",
        "provider_authority": "false" if PROVIDER_AUTHORITY_FIX_250 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_250 is False else "true",
        "mutation_scope": "governed_application_generation",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "generation_not_autonomous_authority",
        **extra,
    }


def route_governed_application_generation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_governed_application_generation_record_intent(text)
    if record_intent is not None:
        kind, content, metadata = record_intent
        record, blockers = append_governed_application_generation_record(
            session_id=session_id,
            kind=kind,
            content=content,
            metadata=metadata,
        )
        if blockers or not record:
            body = f"Application generation record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_governed_application_generation_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Application generation record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "application_generation ≠ autonomous_authority."
        )
        return (
            body,
            "mission_control_governed_application_generation_record",
            _meta(session_id, stage="generation_memory", record_id=str(record.get("record_id") or "")),
        )

    if is_governed_application_generation_handoff_intent(text):
        handoff = prepare_governed_application_generation_handoff(session_id=session_id)
        if not handoff.ok:
            body = f"Delivery pipeline handoff blocked: {', '.join(handoff.blockers)}"
            return (
                body,
                "mission_control_governed_application_generation_handoff_blocked",
                _meta(session_id, stage="handoff_blocked"),
            )
        body = (
            f"Delivery pipeline handoff prepared (`{handoff.delivery_pipeline_handoff.get('handoff_id')}`). "
            "Feed existing Plan → Patch → Verify → PR pipeline — AethOS does not create repositories."
        )
        return (
            body,
            "mission_control_governed_application_generation_handoff",
            _meta(session_id, stage="existing_delivery_pipeline"),
        )

    if not is_governed_application_generation_intent(text):
        return None

    result = build_governed_application_generation(session_id=session_id)
    body = render_governed_application_generation(result.governed_application_generation)
    return (
        body,
        "mission_control_governed_application_generation",
        _meta(session_id, stage="governed_application_generation"),
    )
