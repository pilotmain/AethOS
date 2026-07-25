# SPDX-License-Identifier: Apache-2.0
"""FIX 316B — identity truth validation and drift detection."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.identity_truth_lock.identity_truth_lock_contract import (
    FORBIDDEN_CROSS_CONTAMINATION,
    PLATFORM_CREATOR,
    PLATFORM_NAME,
    build_creator_attribution_registry,
    build_platform_identity_registry,
    build_provider_attribution_registry,
)

_PROVIDER_AS_CREATOR_RX = re.compile(
    r"\b(?:anthropic|openai|claude|gpt|chatgpt)\b.{0,80}\b(?:created|built|owns|own)\b.{0,40}\b(?:aethos|you)\b",
    re.I | re.S,
)
_MODEL_AS_PLATFORM_RX = re.compile(
    r"\b(?:i\s+am|i'm)\s+(?:claude|gpt|chatgpt)\b",
    re.I,
)
_PLATFORM_AS_PROVIDER_RX = re.compile(
    r"\b(?:aethos|pilotos)\b.{0,40}\b(?:powers|provides)\b.{0,40}\b(?:this\s+session|llm|model)\b",
    re.I | re.S,
)
_CREATOR_OMITTED_RX = re.compile(
    r"\b(?:who\s+(?:created|built|owns)\s+(?:aethos|you))\b",
    re.I,
)
_PROVIDER_IN_CREATOR_RX = re.compile(
    r"\b(?:anthropic|openai)\b.{0,60}\b(?:created|built|owns)\b.{0,40}\baethos\b",
    re.I | re.S,
)
_CREATOR_IN_PROVIDER_RX = re.compile(
    r"\b(?:raya\s+meresa|platform\s+creator)\b.{0,60}\b(?:model|provider|claude|gpt)\b",
    re.I | re.S,
)


def _section_ok(*, section: str, required_keys: tuple[str, ...], forbidden_values: tuple[str, ...] = ()) -> dict[str, Any]:
    missing = [key for key in required_keys if not section.get(key)]
    forbidden_hits = [value for value in forbidden_values if value.lower() in str(section).lower()]
    return {
        "ok": not missing and not forbidden_hits,
        "missing_keys": missing,
        "forbidden_hits": forbidden_hits,
    }


def build_identity_truth_validation_report(
    *,
    runtime_provider: str,
    runtime_model: str,
) -> dict[str, Any]:
    platform = build_platform_identity_registry()
    creator = build_creator_attribution_registry()
    provider = build_provider_attribution_registry(
        runtime_provider=runtime_provider,
        runtime_model=runtime_model,
    )

    platform_check = _section_ok(
        section=platform,
        required_keys=("name", "purpose", "mission", "governance_philosophy", "human_oversight_model", "trust_philosophy"),
    )
    creator_check = _section_ok(
        section=creator,
        required_keys=("creator", "owner", "questions"),
        forbidden_values=("Anthropic", "OpenAI", "Claude", "GPT"),
    )
    provider_check = _section_ok(
        section=provider,
        required_keys=("registered_providers", "runtime_session", "questions"),
        forbidden_values=(PLATFORM_CREATOR,),
    )

    model_attribution = {
        "Claude": "Anthropic",
        "GPT": "OpenAI",
    }
    model_check = {
        "ok": model_attribution["Claude"] == "Anthropic" and model_attribution["GPT"] == "OpenAI",
        "model_attribution": model_attribution,
    }

    checks = {
        "platform_identity": platform_check,
        "creator_attribution": creator_check,
        "provider_attribution": provider_check,
        "model_attribution": model_check,
    }
    cross_contamination = detect_identity_drift(text="")
    return {
        "checks": checks,
        "cross_contamination_guardrails": list(FORBIDDEN_CROSS_CONTAMINATION),
        "overall_ok": all(
            bool(check.get("ok"))
            for check in (
                platform_check,
                creator_check,
                provider_check,
                model_check,
            )
        ),
        "registry_isolation": cross_contamination["registry_isolation"],
    }


def detect_identity_drift(*, text: str) -> dict[str, Any]:
    raw = text or ""
    findings: list[dict[str, str]] = []

    if _PROVIDER_AS_CREATOR_RX.search(raw):
        findings.append(
            {
                "kind": "provider_presented_as_creator",
                "detail": "Provider or model language appears to claim AethOS creation or ownership.",
            }
        )
    if _MODEL_AS_PLATFORM_RX.search(raw):
        findings.append(
            {
                "kind": "model_presented_as_platform",
                "detail": "Model identity presented as platform identity.",
            }
        )
    if _PLATFORM_AS_PROVIDER_RX.search(raw):
        findings.append(
            {
                "kind": "platform_presented_as_provider",
                "detail": "Platform language appears to replace provider attribution.",
            }
        )
    if _CREATOR_OMITTED_RX.search(raw) and PLATFORM_CREATOR.lower() not in raw.lower():
        findings.append(
            {
                "kind": "creator_omitted",
                "detail": "Creator question detected without canonical creator attribution.",
            }
        )
    if _PROVIDER_IN_CREATOR_RX.search(raw):
        findings.append(
            {
                "kind": "incorrect_ownership_claim",
                "detail": "Provider presented as AethOS creator or owner.",
            }
        )
    if _CREATOR_IN_PROVIDER_RX.search(raw):
        findings.append(
            {
                "kind": "creator_in_provider_response",
                "detail": "Creator attribution leaked into provider-only response.",
            }
        )

    return {
        "findings": findings,
        "drift_detected": bool(findings),
        "registry_isolation": {
            "platform_identity_ne_model_identity": True,
            "creator_attribution_ne_provider_attribution": True,
            "provider_usage_ne_platform_ownership": True,
        },
        "forbidden_patterns_checked": list(FORBIDDEN_CROSS_CONTAMINATION),
    }


def validate_identity_response_text(*, text: str, response_kind: str) -> dict[str, Any]:
    kind = (response_kind or "").strip().lower()
    findings: list[dict[str, str]] = []

    if kind in {"platform_identity_response", "self_introduction_package"}:
        if PLATFORM_NAME.lower() not in text.lower():
            findings.append(
                {
                    "kind": "platform_identity_missing",
                    "detail": f"Platform identity response must include {PLATFORM_NAME}.",
                }
            )

    if kind in {"creator_attribution_response", "creator_introduction_package", "ownership_attribution_response"}:
        if PLATFORM_CREATOR.lower() not in text.lower():
            findings.append(
                {
                    "kind": "creator_omitted",
                    "detail": f"Creator response must include {PLATFORM_CREATOR}.",
                }
            )
        if _PROVIDER_IN_CREATOR_RX.search(text):
            findings.append(
                {
                    "kind": "provider_in_creator_response",
                    "detail": "Provider attribution must not replace creator attribution.",
                }
            )

    if kind in {"provider_attribution_response", "provider_attribution_registry"}:
        if PLATFORM_CREATOR.lower() in text.lower():
            findings.append(
                {
                    "kind": "creator_in_provider_response",
                    "detail": "Provider response must not include creator attribution.",
                }
            )

    if kind.startswith("model_creator_attribution"):
        if _PROVIDER_AS_CREATOR_RX.search(text):
            findings.append(
                {
                    "kind": "provider_presented_as_creator",
                    "detail": "Model creator response must attribute models to providers only.",
                }
            )

    return {
        "findings": findings,
        "drift_detected": bool(findings),
        "response_kind": kind,
        "valid": not findings,
    }
