# SPDX-License-Identifier: Apache-2.0
"""FIX 316C — truth consistency service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.truth_consistency.truth_consistency_contract import (
    AUTHORITY_FLAGS,
    TRUTH_CONSISTENCY_DOMAINS,
    TRUTH_CONSISTENCY_FIX,
)
from aethos_core.truth_consistency.truth_consistency_evaluator import (
    build_capability_truth_report,
    build_identity_truth_report,
    build_provider_truth_report,
    build_readiness_truth_report,
    build_trust_truth_report,
    detect_hallucinations,
    detect_truth_drift,
)
from aethos_core.truth_consistency.truth_consistency_evidence import collect_truth_evidence
from aethos_core.truth_consistency.truth_consistency_store import list_truth_review_records


@dataclass(frozen=True)
class TruthConsistencyResult:
    truth_consistency: dict[str, Any]

    @property
    def sections(self) -> dict[str, Any]:
        return self.truth_consistency.get("sections") or {}


def build_truth_consistency(
    *,
    session_id: str = "default",
    sample_answer: str = "",
    sample_response_kind: str = "",
) -> TruthConsistencyResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_truth_evidence(session_id=sid)

    capability_truth_report = build_capability_truth_report(evidence=evidence)
    trust_truth_report = build_trust_truth_report(evidence=evidence)
    provider_truth_report = build_provider_truth_report(evidence=evidence)
    identity_truth_report = build_identity_truth_report(evidence=evidence)
    readiness_truth_report = build_readiness_truth_report(evidence=evidence)
    hallucination_detection_report = detect_hallucinations(
        answer_text=sample_answer,
        evidence=evidence,
        response_kind=sample_response_kind,
    )
    truth_drift_report = detect_truth_drift(evidence=evidence)

    from aethos_core.truth_consistency.truth_consistency_public_answer_validator import validate_public_answer

    public_answer_validation_report = validate_public_answer(
        question="",
        answer=sample_answer,
        session_id=sid,
        response_kind=sample_response_kind,
        evidence=evidence,
    ) if sample_answer else {
        "valid": None,
        "detail": "Provide question and answer to validate public responses.",
    }

    truth_dashboard = {
        "capability_truth_ok": capability_truth_report.get("validated"),
        "trust_truth_ok": trust_truth_report.get("validated"),
        "provider_truth_ok": provider_truth_report.get("validated"),
        "identity_truth_ok": identity_truth_report.get("overall_ok"),
        "readiness_truth_ok": readiness_truth_report.get("validated"),
        "hallucination_detected": hallucination_detection_report.get("hallucination_detected"),
        "truth_drift_detected": truth_drift_report.get("drift_detected"),
        "authority_flags": dict(AUTHORITY_FLAGS),
        "core_principle": "generated_response ≠ platform_truth",
    }
    truth_review_registry = {
        "records": list_truth_review_records(),
        "commands": (
            "truth note: ...",
            "truth review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "capability_truth_report": capability_truth_report,
        "trust_truth_report": trust_truth_report,
        "provider_truth_report": provider_truth_report,
        "identity_truth_report": identity_truth_report,
        "readiness_truth_report": readiness_truth_report,
        "hallucination_detection_report": hallucination_detection_report,
        "truth_drift_report": truth_drift_report,
        "public_answer_validation_report": public_answer_validation_report,
        "truth_dashboard": truth_dashboard,
        "truth_review_registry": truth_review_registry,
    }

    return TruthConsistencyResult(
        truth_consistency={
            "fix": TRUTH_CONSISTENCY_FIX,
            "session_id": sid,
            "domains": list(TRUTH_CONSISTENCY_DOMAINS),
            "sections": sections,
        }
    )
