# SPDX-License-Identifier: Apache-2.0
"""FIX 311 — public product experience tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.public_product_experience.public_product_experience_contract import (
    AUTOMATIC_CUSTOMER_ONBOARDING_ENABLED_FIX_311,
    PUBLIC_PRODUCT_AUTHORITY_FIX_311,
    PUBLIC_PRODUCT_EXPERIENCE_ROUTE_ID,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_intent import (
    parse_public_product_experience_intent,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_service import (
    build_public_product_experience,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_store import (
    clear_public_product_experience_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_public_product_experience_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()
    yield
    clear_public_product_experience_records_for_tests()
    clear_orgs_for_tests()
    get_settings.cache_clear()


def test_public_product_experience_intent():
    assert parse_public_product_experience_intent("show public product experience") == {
        "action": "view",
        "focus": "public_product_dashboard",
    }
    assert parse_public_product_experience_intent("show capability explorer") == {
        "action": "view",
        "focus": "capability_explorer",
    }
    parsed = parse_public_product_experience_intent(
        "public experience review approve: Human approves public experience review only"
    )
    assert parsed == {
        "action": "record",
        "kind": "public_experience_review_decision_approve",
        "content": "Human approves public experience review only",
    }


def test_build_public_product_experience():
    result = build_public_product_experience(session_id="mc-ppe-311")
    assert result.ok is True
    board = result.public_product_experience
    assert board["public_product_authority"] is False
    assert board["automatic_customer_onboarding_enabled"] is False
    sections = board["sections"]
    for key in (
        "public_landing_experience",
        "capability_explorer",
        "trust_explorer",
        "guided_product_tour",
        "use_case_explorer",
        "customer_journey_explorer",
        "plan_entitlement_explorer",
        "public_readiness_explorer",
        "public_education_center",
        "public_product_dashboard",
    ):
        assert sections[key]


def test_capability_explorer_composes_fix_295():
    result = build_public_product_experience(session_id="mc-ppe-capability")
    explorer = result.public_product_experience["sections"]["capability_explorer"][0]
    assert "FIX 295" in explorer["evidence_sources"]
    assert "proven" in explorer
    assert "experimental" in explorer


def test_trust_explorer_composes_trust_baselines():
    result = build_public_product_experience(session_id="mc-ppe-trust")
    explorer = result.public_product_experience["sections"]["trust_explorer"][0]
    fixes = {row["fix"] for row in explorer["baselines"]}
    assert "FIX 186" in fixes
    assert "FIX 192" in fixes
    assert "FIX 194" in fixes
    assert "FIX 196" in fixes


def test_readiness_explorer_composes_fix_309():
    result = build_public_product_experience(session_id="mc-ppe-readiness")
    explorer = result.public_product_experience["sections"]["public_readiness_explorer"][0]
    assert explorer["evidence_sources"] == ["FIX 309"]
    assert "overall_launch_status" in explorer


def test_education_center_composes_onboarding_and_provider_guidance():
    result = build_public_product_experience(session_id="mc-ppe-education")
    center = result.public_product_experience["sections"]["public_education_center"][0]
    assert "FIX 295" in center["evidence_sources"]
    assert "FIX 301" in center["evidence_sources"]
    assert "FIX 303" in center["evidence_sources"]
    assert len(center["faqs"]) >= 4


def test_public_dashboard_composes_all_domains():
    result = build_public_product_experience(session_id="mc-ppe-dashboard")
    dashboard = result.public_product_experience["sections"]["public_product_dashboard"][0]
    assert dashboard["evidence_coverage"]["domains_total"] == 10
    assert dashboard["evidence_coverage"]["domains_composed"] == 10


def test_no_authority_flags_enabled():
    result = build_public_product_experience(session_id="mc-ppe-authority")
    board = result.public_product_experience
    sources = board["sources"]
    assert board["public_product_authority"] is False
    assert board["trust_mutation_authority"] is False
    assert board["provider_mutation_authority"] is False
    assert board["tenant_mutation_authority"] is False
    assert sources["governance_bypass_performed"] is False
    assert sources["automatic_onboarding_performed"] is False
    assert sources["customer_provisioning_performed"] is False


def test_regression_show_public_product_experience():
    turn = resolve_chat_turn("show public product experience", session_id="mc-ppe-regression")
    assert turn.intent == "mission_control_public_product_experience"
    lowered = turn.reply.lower()
    assert "capabilit" in lowered or "trust" in lowered or "govern" in lowered
    assert "authority" in lowered or "governance" in lowered


def test_authority_flags():
    assert PUBLIC_PRODUCT_AUTHORITY_FIX_311 is False
    assert AUTOMATIC_CUSTOMER_ONBOARDING_ENABLED_FIX_311 is False


def test_chat_route():
    turn = resolve_chat_turn("show trust explorer", session_id="mc-ppe-chat")
    assert turn.intent == "mission_control_public_product_experience"
    assert (turn.meta or {}).get("route_id") == PUBLIC_PRODUCT_EXPERIENCE_ROUTE_ID


def test_api_get_and_record():
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/public-product-experience",
        params={"session_id": "mc-ppe-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["ok"] is True
    assert body["public_product_authority"] is False
    assert body["public_product_experience"]
    assert body["markdown"]

    post_resp = client.post(
        "/api/v1/mission-control/public-product-experience",
        json={
            "session_id": "mc-ppe-api",
            "kind": "public_experience_note",
            "content": "Public landing copy reviewed — no automatic onboarding performed",
            "domain": "public_product_dashboard",
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["ok"] is True
