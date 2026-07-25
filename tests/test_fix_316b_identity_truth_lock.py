# SPDX-License-Identifier: Apache-2.0
"""FIX 316B — identity truth lock tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.identity_truth_lock.identity_truth_lock_contract import (
    AUTHORITY_FLAGS,
    IDENTITY_TRUTH_LOCK_DOMAINS,
    PLATFORM_CREATOR,
)
from aethos_core.identity_truth_lock.identity_truth_lock_evaluator import (
    detect_identity_drift,
    validate_identity_response_text,
)
from aethos_core.identity_truth_lock.identity_truth_lock_responses import (
    compose_creator_introduction_response,
    compose_model_creator_attribution_response,
    compose_provider_attribution_response,
    compose_self_introduction_response,
)
from aethos_core.identity_truth_lock.identity_truth_lock_service import build_identity_truth_lock
from aethos_core.identity_truth_lock.identity_truth_lock_store import (
    append_identity_review_record,
    clear_identity_review_records_for_tests,
    list_identity_review_records,
)
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_classifier import classify_runtime_prompt
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_router import route_runtime_truth_alignment

_MOCK_EVIDENCE = {
    "summary": {"overall_maturity_tier": "OPERATIONAL"},
    "proven_items": ["Mission Control (PROVEN)"],
    "operational_items": ["Provider inspection (OPERATIONAL)"],
    "authority_note": "Observation only — humans approve execution.",
    "provider_readiness": [{"provider": "github", "readiness": "OPERATIONAL"}],
    "maturity_tier": "OPERATIONAL",
}


@pytest.fixture(autouse=True)
def _mock_capability_evidence():
    with patch(
        "aethos_core.identity_truth_lock.identity_truth_lock_responses._safe_capability_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_identity_store():
    clear_identity_review_records_for_tests()
    yield
    clear_identity_review_records_for_tests()


def test_identity_truth_lock_domains_and_authority_flags():
    result = build_identity_truth_lock(session_id="itl-316b")
    sections = result.sections
    assert list(IDENTITY_TRUTH_LOCK_DOMAINS) == list(sections.keys())
    assert AUTHORITY_FLAGS["identity_authority"] is False
    assert AUTHORITY_FLAGS["automatic_identity_rewrite_enabled"] is False
    assert sections["creator_attribution_registry"]["creator"] == PLATFORM_CREATOR
    assert sections["runtime_identity_lock"]["identity_responses_bypass_provider_self_identity"] is True


def test_identity_routing_regression():
    routed = route_runtime_truth_alignment("Who are you?", session_id="itl-316b-id")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "platform_identity_response"
    assert "AethOS" in body
    assert meta["runtime_identity_lock"] == "true"
    assert meta["bypass_provider_self_identity"] == "true"


def test_creator_attribution_regression():
    body = compose_creator_introduction_response()
    assert PLATFORM_CREATOR in body
    assert "Anthropic" not in body
    assert "OpenAI" not in body

    routed = route_runtime_truth_alignment("Who created AethOS?", session_id="itl-316b-creator")
    assert routed is not None
    assert routed[1] == "creator_attribution_response"
    assert PLATFORM_CREATOR in routed[0]


def test_ownership_validation_regression():
    routed = route_runtime_truth_alignment("Who owns AethOS?", session_id="itl-316b-owner")
    assert routed is not None
    assert routed[1] == "ownership_attribution_response"
    assert PLATFORM_CREATOR in routed[0]
    assert "Anthropic" not in routed[0]


def test_provider_attribution_regression():
    routed = route_runtime_truth_alignment("Which model are you using?", session_id="itl-316b-provider")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "provider_attribution_response"
    assert PLATFORM_CREATOR not in body
    assert "Provider attribution" in body
    assert meta["runtime_identity_lock"] == "true"


def test_model_creator_attribution_regression():
    assert classify_runtime_prompt("Who created Claude?").startswith("model_creator_attribution_response:")
    claude = compose_model_creator_attribution_response(model_name="claude")
    assert "Anthropic" in claude
    assert PLATFORM_CREATOR not in claude

    gpt = compose_model_creator_attribution_response(model_name="gpt")
    assert "OpenAI" in gpt

    routed = route_runtime_truth_alignment("Who created GPT?", session_id="itl-316b-gpt")
    assert routed is not None
    assert "OpenAI" in routed[0]
    assert PLATFORM_CREATOR not in routed[0]


def test_runtime_identity_lock_regression():
    body = compose_self_introduction_response(session_id="itl-316b-lock")
    validation = validate_identity_response_text(
        text=body,
        response_kind="platform_identity_response",
    )
    assert validation["valid"] is True
    lock = build_identity_truth_lock(session_id="itl-316b-lock").sections["runtime_identity_lock"]
    assert lock["identity_source"] == "platform_identity_registry"


def test_identity_drift_detection_regression():
    drift = detect_identity_drift(text="Anthropic created AethOS and owns this platform.")
    assert drift["drift_detected"] is True
    kinds = {finding["kind"] for finding in drift["findings"]}
    assert "provider_presented_as_creator" in kinds or "incorrect_ownership_claim" in kinds


def test_identity_review_registry_record_only():
    append_identity_review_record(kind="identity_note", content="review boundary copy", session_id="itl-316b")
    assert len(list_identity_review_records()) == 1

    routed = route_runtime_truth_alignment("identity note: keep creator canonical", session_id="itl-316b")
    assert routed is not None
    assert "record-only" in routed[0].lower()
    assert len(list_identity_review_records()) == 2
