# SPDX-License-Identifier: Apache-2.0
"""Confidence tracking for investigations."""

from __future__ import annotations

from typing import Any

ConfidenceLabel = str


def root_confidence_to_score(confidence: str) -> float:
    mapping = {"low": 0.25, "medium": 0.55, "high": 0.85}
    return mapping.get(str(confidence or "low").lower(), 0.25)


def score_from_evidence(*, root: dict[str, Any], correlation: dict[str, Any], evidence_tags: list[str]) -> float:
    score = root_confidence_to_score(str(root.get("confidence") or "low"))
    if correlation.get("root_cause_confirmed"):
        score = min(1.0, score + 0.15)
    if "high_signal_logs" in evidence_tags:
        score = min(1.0, score + 0.12)
    if "stale_service_events" in evidence_tags:
        score = max(0.0, score - 0.12)
    if "success_event_conflict" in evidence_tags:
        score = max(0.0, score - 0.1)
    if root.get("bounded_diagnosis"):
        score = min(score, 0.75)
    if str(root.get("category") or "") in {"insufficient_evidence", "unknown_runtime_failure", "database_startup_or_storage_activity"}:
        score = min(score, 0.62)
    return round(max(0.0, min(1.0, score)), 2)


def confidence_label(score: float) -> ConfidenceLabel:
    if score < 0.3:
        return "weak"
    if score < 0.6:
        return "bounded"
    if score < 0.8:
        return "likely"
    return "strong"


def mutation_allowed(score: float, *, root: dict[str, Any] | None = None) -> bool:
    if score < 0.6:
        return False
    root = root or {}
    if root.get("bounded_diagnosis") and score < 0.8:
        return False
    return bool(root.get("suggests_mutation")) or score >= 0.8
