# SPDX-License-Identifier: Apache-2.0
"""KERNEL_REALITY_PROOF_001 Phase 7 — dedicated provider routing accuracy."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_RAILWAY_RX = re.compile(r"\brailway\b", re.I)
_VERCEL_RX = re.compile(r"\bvercel\b", re.I)
_KNOWN_VERCEL = re.compile(r"\b(killit|invoicepilot)\b", re.I)
_KNOWN_RAILWAY = re.compile(r"\b(aethos-api|aethos-ui|pilotos)\b", re.I)


@dataclass(frozen=True)
class ProviderRoutingEvaluation:
    requested_provider: str
    resolved_provider: str
    correct_provider: bool
    confidence: str
    provider_misroute: bool
    manual_correction_required: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_provider": self.requested_provider,
            "resolved_provider": self.resolved_provider,
            "correct_provider": self.correct_provider,
            "confidence": self.confidence,
            "provider_misroute": self.provider_misroute,
            "manual_correction_required": self.manual_correction_required,
        }


def infer_requested_provider(request: str) -> str:
    raw = (request or "").strip()
    if not raw:
        return ""

    from aethos_core.operational_target_resolution.provider_intent_guard import primary_explicit_provider

    primary = primary_explicit_provider(raw)
    if primary in {"railway", "vercel"}:
        return primary

    has_vercel = bool(_VERCEL_RX.search(raw)) or bool(_KNOWN_VERCEL.search(raw))
    has_railway = bool(_RAILWAY_RX.search(raw)) or bool(_KNOWN_RAILWAY.search(raw))
    if has_vercel and not has_railway:
        return "vercel"
    if has_railway and not has_vercel:
        return "railway"
    if _KNOWN_VERCEL.search(raw) and not _KNOWN_RAILWAY.search(raw):
        return "vercel"
    if _KNOWN_RAILWAY.search(raw) and not _KNOWN_VERCEL.search(raw):
        return "railway"
    if has_vercel and has_railway:
        return "multi"
    return ""


def evaluate_provider_routing(*, request: str, resolved_provider: str) -> ProviderRoutingEvaluation:
    requested = infer_requested_provider(request)
    resolved = (resolved_provider or "").lower()
    if not requested:
        return ProviderRoutingEvaluation(
            requested_provider="",
            resolved_provider=resolved,
            correct_provider=True,
            confidence="low",
            provider_misroute=False,
            manual_correction_required=False,
        )
    if requested == "multi":
        correct = resolved in {"railway", "vercel", ""}
        return ProviderRoutingEvaluation(
            requested_provider="multi",
            resolved_provider=resolved,
            correct_provider=correct,
            confidence="medium",
            provider_misroute=not correct and bool(resolved),
            manual_correction_required=not correct,
        )
    correct = requested == resolved
    misroute = bool(requested) and bool(resolved) and not correct
    return ProviderRoutingEvaluation(
        requested_provider=requested,
        resolved_provider=resolved,
        correct_provider=correct or not resolved,
        confidence="high" if requested and resolved else "medium",
        provider_misroute=misroute,
        manual_correction_required=misroute,
    )
