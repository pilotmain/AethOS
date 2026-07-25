# SPDX-License-Identifier: Apache-2.0
"""FIX 316C — truth consistency tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.identity_truth_lock.identity_truth_lock_contract import PLATFORM_CREATOR
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_classifier import classify_runtime_prompt
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_router import route_runtime_truth_alignment
from aethos_core.truth_consistency.truth_consistency_contract import AUTHORITY_FLAGS, TRUTH_CONSISTENCY_DOMAINS
from aethos_core.truth_consistency.truth_consistency_evaluator import detect_hallucinations, detect_truth_drift
from aethos_core.truth_consistency.truth_consistency_public_answer_validator import validate_public_answer
from aethos_core.truth_consistency.truth_consistency_service import build_truth_consistency
from aethos_core.truth_consistency.truth_consistency_store import (
    append_truth_review_record,
    clear_truth_review_records_for_tests,
    list_truth_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "tc-316c",
    "sources_ok": {
        "fix_295": True,
        "fix_296": True,
        "fix_303": True,
        "fix_316b": True,
        "fix_309": True,
        "fix_314": True,
        "fix_315": True,
        "fix_186": True,
        "fix_192": True,
        "fix_194": True,
        "fix_196": True,
    },
    "capability_summary": {
        "proven_items": ["Mission Control (PROVEN)"],
        "operational_items": ["Provider inspection (OPERATIONAL)"],
        "planned_items": ["Autonomous deploy (PLANNED)"],
        "experimental_items": [],
        "maturity_tier": "OPERATIONAL",
    },
    "provider_summary": {
        "phase_1_providers": ["GitHub", "Railway", "Vercel"],
        "phase_2_providers": ["AWS", "Azure", "GCP", "Kubernetes"],
        "connected_provider_count": 1,
        "provider_reports": [],
    },
    "readiness_summary": {
        "overall_launch_status": "CONDITIONAL",
        "launch_recommendation_freeze": "HOLD_LAUNCH",
        "launch_recommendation_package": "REVIEW",
        "blockers": ["Human launch approval pending"],
    },
    "identity_truth_lock": {
        "sections": {
            "identity_truth_validation_report": {"overall_ok": True, "checks": {}},
            "creator_attribution_registry": {"creator": PLATFORM_CREATOR},
        }
    },
    "trust_report_freezes": {
        "fix_186": {"trust_status": "HOLD"},
        "fix_192": {"trust_status": "HOLD"},
        "fix_194": {"trust_status": "HOLD"},
        "fix_196": {"trust_status": "HOLD"},
    },
    "capability_registry_runtime_integration": {"sections": {"repository_trust_matrix": [{}]}},
    "provider_connection_experience": {"sections": {}},
}


@pytest.fixture(autouse=True)
def _mock_truth_evidence():
    with patch(
        "aethos_core.truth_consistency.truth_consistency_service.collect_truth_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.truth_consistency.truth_consistency_responses.collect_truth_evidence_lightweight",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.truth_consistency.truth_consistency_evidence.collect_truth_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.truth_consistency.truth_consistency_evidence.collect_truth_evidence_lightweight",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _mock_capability_evidence():
    with patch(
        "aethos_core.identity_truth_lock.identity_truth_lock_responses._safe_capability_evidence",
        return_value={
            "proven_items": ["Mission Control (PROVEN)"],
            "operational_items": ["Provider inspection (OPERATIONAL)"],
            "authority_note": "Observation only.",
            "provider_readiness": [{"provider": "github", "readiness": "OPERATIONAL"}],
            "maturity_tier": "OPERATIONAL",
        },
    ), patch(
        "aethos_core.runtime_truth_alignment.runtime_truth_alignment_composer._safe_capability_evidence",
        return_value={
            "proven_items": ["Mission Control (PROVEN)"],
            "operational_items": ["Provider inspection (OPERATIONAL)"],
            "authority_note": "Observation only.",
            "provider_readiness": [{"provider": "github", "readiness": "OPERATIONAL"}],
            "maturity_tier": "OPERATIONAL",
        },
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_truth_store():
    clear_truth_review_records_for_tests()
    yield
    clear_truth_review_records_for_tests()


def test_truth_consistency_domains_and_authority_flags():
    result = build_truth_consistency(session_id="tc-316c")
    assert list(TRUTH_CONSISTENCY_DOMAINS) == list(result.sections.keys())
    assert AUTHORITY_FLAGS["truth_authority"] is False
    assert AUTHORITY_FLAGS["automatic_truth_rewrite_enabled"] is False


def test_capability_truth_regression():
    routed = route_runtime_truth_alignment("What can you do?", session_id="tc-316c-cap")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "capability_response"
    assert "What I can do" in body
    assert meta["truth_validated"] == "true"
    assert meta["hallucination_detected"] == "false"


def test_identity_truth_regression():
    routed = route_runtime_truth_alignment("Who created AethOS?", session_id="tc-316c-id")
    assert routed is not None
    assert PLATFORM_CREATOR in routed[0]
    assert routed[2]["truth_validated"] == "true"


def test_provider_truth_regression():
    routed = route_runtime_truth_alignment("Which providers do you support?", session_id="tc-316c-prov")
    assert routed is not None
    assert routed[1] == "provider_support_response"
    assert "GitHub" in routed[0]
    assert PLATFORM_CREATOR not in routed[0]
    assert routed[2]["truth_validated"] == "true"


def test_trust_truth_regression():
    report = build_truth_consistency(session_id="tc-316c").sections["trust_truth_report"]
    assert report["validated"] is True
    assert report["trust_states"]["dogfood_pilot"] == "HOLD"


def test_launch_readiness_truth_regression():
    assert classify_runtime_prompt("Are you launch ready?") == "launch_readiness_response"
    routed = route_runtime_truth_alignment("Are you launch ready?", session_id="tc-316c-launch")
    assert routed is not None
    assert "CONDITIONAL" in routed[0]
    assert routed[2]["truth_validated"] == "true"


def test_hallucination_detection_regression():
    report = detect_hallucinations(
        answer_text="Anthropic created AethOS and we are fully autonomous with unlimited trust.",
        evidence=_MOCK_EVIDENCE,
        response_kind="platform_identity_response",
    )
    assert report["hallucination_detected"] is True
    kinds = {item["kind"] for item in report["findings"]}
    assert "unsupported_identity_claim" in kinds
    assert "unsupported_capability_claim" in kinds or "unsupported_trust_claim" in kinds


def test_public_answer_validation_regression():
    validation = validate_public_answer(
        question="Who are you?",
        answer="I'm AethOS — a governed operational intelligence system.",
        response_kind="platform_identity_response",
        evidence=_MOCK_EVIDENCE,
    )
    assert validation["valid"] is True

    bad = validate_public_answer(
        question="Who created you?",
        answer="OpenAI built this platform.",
        response_kind="creator_attribution_response",
        evidence=_MOCK_EVIDENCE,
    )
    assert bad["valid"] is False


def test_truth_drift_detection_regression():
    drift = detect_truth_drift(evidence=_MOCK_EVIDENCE)
    assert drift["drift_detected"] is False


def test_truth_review_registry_record_only():
    append_truth_review_record(kind="truth_note", content="verify capability claims", session_id="tc-316c")
    routed = route_runtime_truth_alignment("truth note: keep evidence alignment", session_id="tc-316c")
    assert routed is not None
    assert "record-only" in routed[0].lower()
    assert len(list_truth_review_records()) == 2
