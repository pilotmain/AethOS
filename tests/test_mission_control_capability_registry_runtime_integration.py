"""Tests for FIX 296 — capability registry runtime integration."""

from __future__ import annotations

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.governance.governance_friction_approval_contract import FIX_296_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_contract import (
    AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_296,
    CAPABILITY_ANSWERING_AUTHORITY_FIX_296,
    CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_FIX,
    PROVIDER_AUTHORITY_FIX_296,
    TRUST_MUTATION_AUTHORITY_FIX_296,
)
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_intent import (
    is_general_capability_question,
)
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_renderer import (
    render_capability_registry_runtime_integration,
)
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_router import (
    route_capability_registry_runtime_integration,
)
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
    build_capability_registry_runtime_integration,
    compose_capability_runtime_reply,
)


def test_fix_296_contract_authority_flags_false() -> None:
    assert CAPABILITY_ANSWERING_AUTHORITY_FIX_296 is False
    assert AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_296 is False
    assert TRUST_MUTATION_AUTHORITY_FIX_296 is False
    assert PROVIDER_AUTHORITY_FIX_296 is False


def test_fix_296_certification_requirements_count() -> None:
    assert len(FIX_296_CERTIFICATION_REQUIREMENTS) == 10


def test_general_capability_intent_matches_spec_prompts() -> None:
    assert is_general_capability_question("what can you do?")
    assert is_general_capability_question("what are you capable of doing?")
    assert is_general_capability_question("what are you capable of?")
    assert is_general_capability_question("what can AethOS do?")
    assert is_general_capability_question("what is implemented?")
    assert is_general_capability_question("what is operational?")
    assert is_general_capability_question("what is trusted?")
    assert is_general_capability_question("what providers do you support?")
    assert is_general_capability_question("what can you not do?")
    assert is_general_capability_question("what is experimental?")
    assert is_general_capability_question("what is planned?")


def test_general_capability_intent_excludes_e2e_provider_questions() -> None:
    assert not is_general_capability_question("what can you do on railway?")
    assert not is_general_capability_question("what can you do on vercel?")


def test_build_payload_composes_fix_295_and_300() -> None:
    result = build_capability_registry_runtime_integration(session_id="fix296-test")
    payload = result.capability_registry_runtime_integration
    assert payload["fix"] == CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_FIX
    assert payload["self_awareness_report"]
    assert payload["sources"]["composes_fix_295_capability_registry"] is True
    assert payload["sources"]["composes_fix_300_multi_tenant_platform_foundation"] is True
    assert payload["capability_answering_authority"] is False


def test_regression_what_can_you_do_includes_platform_sections() -> None:
    reply = compose_capability_runtime_reply(session_id="fix296-regression")
    lowered = reply.lower()
    assert "capability summary" in lowered
    assert "governed software delivery" in lowered
    assert "repository intelligence" in lowered
    assert "product evolution" in lowered
    assert "lifecycle management" in lowered or "application lifecycle management" in lowered
    assert "business operating system" in lowered
    assert "multi-tenant foundation" in lowered
    assert "provider capability matrix" in lowered
    assert "repository trust matrix" in lowered
    assert "authority boundaries" in lowered
    assert "proven capabilities" in lowered
    assert "operational capabilities" in lowered


def test_regression_what_can_you_do_not_provider_only() -> None:
    reply = compose_capability_runtime_reply(session_id="fix296-not-provider-only")
    assert "Provider maturity" not in reply
    assert "governed software delivery" in reply.lower()


def test_router_matches_general_capability_question() -> None:
    routed = route_capability_registry_runtime_integration(
        "what can you do?",
        session_id="fix296-router",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_capability_registry_runtime_integration"
    assert meta["route_id"] == "mission_control_capability_registry_runtime_integration"
    assert "governed software delivery" in body.lower()


def test_renderer_includes_required_sections() -> None:
    result = build_capability_registry_runtime_integration(session_id="fix296-render")
    rendered = render_capability_registry_runtime_integration(result.capability_registry_runtime_integration)
    for section in (
        "Capability summary",
        "Proven capabilities",
        "Operational capabilities",
        "Experimental / expanding capabilities",
        "Planned / blocked capabilities",
        "Provider capability matrix",
        "Repository trust matrix",
        "Authority boundaries",
    ):
        assert section in rendered


def test_chat_route_general_capability_question() -> None:
    turn = resolve_chat_turn("what can you do?", session_id="fix296-chat")
    assert turn.intent == "mission_control_capability_registry_runtime_integration"
    assert (turn.meta or {}).get("route_id") == "mission_control_capability_registry_runtime_integration"
    assert "governed software delivery" in turn.reply.lower()
