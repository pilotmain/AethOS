# SPDX-License-Identifier: Apache-2.0
"""FIX 316C — public answer validation against platform evidence."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.identity_truth_lock.identity_truth_lock_contract import PLATFORM_CREATOR, PLATFORM_NAME
from aethos_core.truth_consistency.truth_consistency_evaluator import (
    build_capability_truth_report,
    build_identity_truth_report,
    build_provider_truth_report,
    build_readiness_truth_report,
    detect_hallucinations,
)
from aethos_core.truth_consistency.truth_consistency_evidence import collect_truth_evidence


def _normalize_question(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def classify_public_question(text: str) -> str | None:
    question = _normalize_question(text)
    if re.search(r"what can you do", question):
        return "what_can_you_do"
    if re.search(r"who are you", question):
        return "who_are_you"
    if re.search(r"who created", question):
        return "who_created_you"
    if re.search(r"launch ready|ready for launch|ready for public launch", question):
        return "are_you_launch_ready"
    if re.search(r"which providers? do you support", question):
        return "which_providers_do_you_support"
    return None


def validate_public_answer(
    *,
    question: str,
    answer: str,
    session_id: str = "default",
    response_kind: str = "",
    evidence: dict[str, Any] | None = None,
    lightweight: bool = False,
) -> dict[str, Any]:
    if evidence is None:
        if lightweight:
            from aethos_core.truth_consistency.truth_consistency_evidence import collect_truth_evidence_lightweight

            bundle = collect_truth_evidence_lightweight(session_id=session_id)
        else:
            bundle = collect_truth_evidence(session_id=session_id)
    else:
        bundle = evidence
    public_question = classify_public_question(question) or response_kind
    hallucination = detect_hallucinations(answer_text=answer, evidence=bundle, response_kind=response_kind)

    checks: list[dict[str, Any]] = []
    valid = not hallucination["hallucination_detected"]

    if public_question in {"what_can_you_do", "capability_response"}:
        report = build_capability_truth_report(evidence=bundle)
        checks.append({"domain": "capability_truth_report", "report": report, "ok": report.get("validated")})
        if "What I can do" not in answer and "capabilities" not in answer.lower():
            valid = False
            hallucination["findings"].append(
                {"kind": "capability_answer_shape", "detail": "Capability answer must describe proven platform capabilities."}
            )

    if public_question in {"who_are_you", "platform_identity_response"}:
        report = build_identity_truth_report(evidence=bundle)
        checks.append({"domain": "identity_truth_report", "report": report, "ok": report.get("overall_ok")})
        if PLATFORM_NAME.lower() not in answer.lower():
            valid = False

    if public_question in {"who_created_you", "creator_attribution_response", "ownership_attribution_response"}:
        report = build_identity_truth_report(evidence=bundle)
        checks.append({"domain": "identity_truth_report", "report": report, "ok": report.get("overall_ok")})
        if PLATFORM_CREATOR.lower() not in answer.lower():
            valid = False

    if public_question in {"which_providers_do_you_support", "provider_support_response", "capability_response"}:
        if public_question == "which_providers_do_you_support" or "provider" in _normalize_question(question):
            report = build_provider_truth_report(evidence=bundle)
            checks.append({"domain": "provider_truth_report", "report": report, "ok": report.get("validated")})
            supported_tokens = [
                str(item).lower()
                for item in (report.get("phase_1_providers") or []) + (report.get("phase_2_providers") or [])
            ]
            if supported_tokens and not any(token.split()[0] in answer.lower() for token in supported_tokens if token):
                if "provider" not in answer.lower():
                    valid = False

    if public_question in {"are_you_launch_ready", "launch_readiness_response"}:
        report = build_readiness_truth_report(evidence=bundle)
        checks.append({"domain": "readiness_truth_report", "report": report, "ok": report.get("validated")})
        status = str(report.get("overall_launch_status") or "UNKNOWN")
        if status and status.lower() not in answer.lower() and "launch" not in answer.lower():
            valid = False

    if hallucination["findings"]:
        valid = False

    return {
        "question": question,
        "public_question": public_question,
        "response_kind": response_kind,
        "checks": checks,
        "hallucination_detection_report": hallucination,
        "valid": valid,
        "generated_response_ne_platform_truth": not valid,
    }
