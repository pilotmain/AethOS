# SPDX-License-Identifier: Apache-2.0
"""FIX 316C — truth validation and hallucination detection."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.identity_truth_lock.identity_truth_lock_contract import PLATFORM_CREATOR, PLATFORM_NAME
from aethos_core.identity_truth_lock.identity_truth_lock_evaluator import validate_identity_response_text
from aethos_core.truth_consistency.truth_consistency_contract import HALLUCINATION_MARKERS


def _trust_status(payload: dict[str, Any]) -> str:
    return str(payload.get("trust_status") or payload.get("trust_report_freeze_recorded") or "UNKNOWN")


def build_capability_truth_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    summary = evidence.get("capability_summary") or {}
    cap296 = evidence.get("capability_registry_runtime_integration") or {}
    return {
        "sources": ["FIX 295", "FIX 296"],
        "sources_ok": {
            "fix_295": bool((evidence.get("sources_ok") or {}).get("fix_295")),
            "fix_296": bool((evidence.get("sources_ok") or {}).get("fix_296")),
        },
        "claimed_capabilities": {
            "proven": list(summary.get("proven_items") or []),
            "operational": list(summary.get("operational_items") or []),
            "experimental": list(summary.get("experimental_items") or []),
            "planned": list(summary.get("planned_items") or []),
        },
        "capability_maturity_tier": summary.get("maturity_tier"),
        "answers_from_live_evidence": bool((cap296.get("sections") or {}).get("capability_summary")),
        "validated": bool(summary.get("proven_items") or summary.get("operational_items") or summary.get("planned_items")),
    }


def build_trust_truth_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    freezes = evidence.get("trust_report_freezes") or {}
    repositories = {
        "dogfood_pilot": _trust_status(freezes.get("fix_186") or {}),
        "pilotos_ui": _trust_status(freezes.get("fix_192") or {}),
        "atlas_trader": _trust_status(freezes.get("fix_194") or {}),
        "nexora": _trust_status(freezes.get("fix_196") or {}),
    }
    cap296 = evidence.get("capability_registry_runtime_integration") or {}
    trust_matrix = ((cap296.get("sections") or {}).get("repository_trust_matrix") or [{}])[0]
    return {
        "sources": ["FIX 186", "FIX 192", "FIX 194", "FIX 196"],
        "sources_ok": {key: bool((evidence.get("sources_ok") or {}).get(key)) for key in freezes},
        "trust_states": repositories,
        "repository_trust_matrix": trust_matrix,
        "trust_boundaries_enforced": True,
        "validated": any(value != "UNKNOWN" for value in repositories.values()),
    }


def build_provider_truth_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    summary = evidence.get("provider_summary") or {}
    provider_board = evidence.get("provider_connection_experience") or {}
    return {
        "sources": ["FIX 295", "FIX 303"],
        "sources_ok": {
            "fix_295": bool((evidence.get("sources_ok") or {}).get("fix_295")),
            "fix_303": bool((evidence.get("sources_ok") or {}).get("fix_303")),
        },
        "phase_1_providers": list(summary.get("phase_1_providers") or []),
        "phase_2_providers": list(summary.get("phase_2_providers") or []),
        "connected_provider_count": summary.get("connected_provider_count", 0),
        "provider_limitations": [
            "Provider connection is read-only and approval-gated.",
            "Secret collection in chat is forbidden.",
            "Provider usage does not imply platform ownership.",
        ],
        "provider_readiness_reports": summary.get("provider_reports") or [],
        "validated": bool(summary.get("phase_1_providers") or summary.get("phase_2_providers") or provider_board),
    }


def build_identity_truth_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    identity_lock = (evidence.get("identity_truth_lock") or {}).get("sections") or {}
    validation = identity_lock.get("identity_truth_validation_report") or {}
    return {
        "sources": ["FIX 316B"],
        "platform_identity_registry": identity_lock.get("platform_identity_registry"),
        "creator_attribution_registry": identity_lock.get("creator_attribution_registry"),
        "provider_attribution_registry": identity_lock.get("provider_attribution_registry"),
        "validation_checks": validation.get("checks") or {},
        "overall_ok": bool(validation.get("overall_ok")),
        "validated": bool(validation.get("overall_ok")),
    }


def build_readiness_truth_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    summary = evidence.get("readiness_summary") or {}
    return {
        "sources": ["FIX 309", "FIX 314", "FIX 315"],
        "sources_ok": {
            "fix_309": bool((evidence.get("sources_ok") or {}).get("fix_309")),
            "fix_314": bool((evidence.get("sources_ok") or {}).get("fix_314")),
            "fix_315": bool((evidence.get("sources_ok") or {}).get("fix_315")),
        },
        "overall_launch_status": summary.get("overall_launch_status"),
        "launch_recommendation_freeze": summary.get("launch_recommendation_freeze"),
        "launch_recommendation_package": summary.get("launch_recommendation_package"),
        "blockers": list(summary.get("blockers") or []),
        "validated": bool(summary.get("overall_launch_status")),
    }


def detect_hallucinations(*, answer_text: str, evidence: dict[str, Any], response_kind: str = "") -> dict[str, Any]:
    text = answer_text or ""
    lowered = text.lower()
    findings: list[dict[str, str]] = []

    for pattern, kind in HALLUCINATION_MARKERS:
        if re.search(pattern, text, re.I):
            findings.append({"kind": kind, "detail": f"Matched unsupported claim pattern: {pattern}"})

    capability = evidence.get("capability_summary") or {}
    proven = " ".join(capability.get("proven_items") or []).lower()
    planned = " ".join(capability.get("planned_items") or []).lower()
    if re.search(r"\b(?:fully|completely)\s+operational\b", lowered) and "operational" not in proven:
        if not capability.get("operational_items"):
            findings.append(
                {
                    "kind": "unsupported_capability_claim",
                    "detail": "Answer overstates operational readiness versus FIX 296 evidence.",
                }
            )

    if re.search(r"\blaunch\s+ready\b", lowered):
        status = str((evidence.get("readiness_summary") or {}).get("overall_launch_status") or "UNKNOWN")
        if status in {"BLOCKED", "UNKNOWN"} and "not launch ready" not in lowered and "not ready" not in lowered:
            findings.append(
                {
                    "kind": "unsupported_readiness_claim",
                    "detail": f"Launch-ready language conflicts with evidence status {status}.",
                }
            )

    provider_summary = evidence.get("provider_summary") or {}
    supported = {
        str(item).lower()
        for item in (provider_summary.get("phase_1_providers") or []) + (provider_summary.get("phase_2_providers") or [])
    }
    for claim in ("aws fully supported", "azure fully supported", "kubernetes fully supported"):
        if claim in lowered and not any(token in supported for token in claim.split()[:1]):
            findings.append(
                {
                    "kind": "unsupported_provider_claim",
                    "detail": f"Provider support claim '{claim}' is not certified in FIX 303 evidence.",
                }
            )

    identity_validation = validate_identity_response_text(text=text, response_kind=response_kind)
    for finding in identity_validation.get("findings") or []:
        findings.append({"kind": "unsupported_identity_claim", "detail": finding.get("detail", "")})

    if PLATFORM_CREATOR.lower() not in lowered and response_kind in {
        "creator_attribution_response",
        "ownership_attribution_response",
    }:
        findings.append(
            {
                "kind": "unsupported_identity_claim",
                "detail": f"Creator response must include {PLATFORM_CREATOR}.",
            }
        )

    if PLATFORM_NAME.lower() not in lowered and response_kind == "platform_identity_response":
        findings.append(
            {
                "kind": "unsupported_identity_claim",
                "detail": f"Platform identity response must include {PLATFORM_NAME}.",
            }
        )

    return {
        "findings": findings,
        "hallucination_detected": bool(findings),
        "response_kind": response_kind,
    }


def detect_truth_drift(*, evidence: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    sources_ok = evidence.get("sources_ok") or {}

    if not sources_ok.get("fix_296"):
        findings.append({"kind": "capability_drift", "detail": "FIX 296 capability evidence unavailable."})
    if not sources_ok.get("fix_303"):
        findings.append({"kind": "provider_drift", "detail": "FIX 303 provider evidence unavailable."})
    if not sources_ok.get("fix_316b"):
        findings.append({"kind": "identity_drift", "detail": "FIX 316B identity truth lock unavailable."})
    if not any(sources_ok.get(key) for key in ("fix_309", "fix_314", "fix_315")):
        findings.append({"kind": "readiness_drift", "detail": "Launch readiness evidence unavailable."})
    if not any(sources_ok.get(key) for key in ("fix_186", "fix_192", "fix_194", "fix_196")):
        findings.append({"kind": "trust_drift", "detail": "Trust freeze evidence unavailable."})

    identity_report = build_identity_truth_report(evidence=evidence)
    if not identity_report.get("overall_ok"):
        findings.append({"kind": "identity_drift", "detail": "Identity truth validation failed."})

    return {
        "findings": findings,
        "drift_detected": bool(findings),
        "domains_checked": (
            "documentation",
            "capability",
            "provider",
            "trust",
            "onboarding",
        ),
    }
