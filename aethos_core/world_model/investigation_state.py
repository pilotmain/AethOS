# SPDX-License-Identifier: Apache-2.0
"""Investigation state model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class Hypothesis:
    type: str
    confidence: float
    status: str = "active"
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "confidence": self.confidence,
            "status": self.status,
            "label": self.label or self.type.replace("_", " "),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Hypothesis":
        return cls(
            type=str(payload.get("type") or "unknown"),
            confidence=_safe_float(payload.get("confidence"), default=0.0),
            status=str(payload.get("status") or "active"),
            label=str(payload.get("label") or ""),
        )


@dataclass
class InvestigationState:
    target: str
    session_id: str = "default"
    provider: str = "railway"
    service: str = ""
    project: str = ""
    environment: str = ""
    active_investigation: bool = True
    operator_intent: str = "diagnose_failure"
    hypotheses: list[Hypothesis] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    completed_checks: list[str] = field(default_factory=list)
    next_best_action: str = ""
    next_best_action_key: str = ""
    timeline: list[dict[str, Any]] = field(default_factory=list)
    conclusion: str = ""
    confidence_score: float = 0.0
    confidence_label: str = "weak"
    updated_at: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "session_id": self.session_id,
            "provider": self.provider,
            "service": self.service,
            "project": self.project,
            "environment": self.environment,
            "active_investigation": self.active_investigation,
            "operator_intent": self.operator_intent,
            "hypotheses": [item.to_dict() for item in self.hypotheses],
            "evidence": list(self.evidence),
            "missing_evidence": list(self.missing_evidence),
            "completed_checks": list(self.completed_checks),
            "next_best_action": self.next_best_action,
            "next_best_action_key": self.next_best_action_key,
            "timeline": list(self.timeline),
            "conclusion": self.conclusion,
            "confidence_score": self.confidence_score,
            "confidence_label": self.confidence_label,
            "updated_at": self.updated_at,
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InvestigationState":
        return cls(
            target=str(payload.get("target") or ""),
            session_id=str(payload.get("session_id") or "default"),
            provider=str(payload.get("provider") or "railway"),
            service=str(payload.get("service") or ""),
            project=str(payload.get("project") or ""),
            environment=str(payload.get("environment") or ""),
            active_investigation=bool(payload.get("active_investigation", True)),
            operator_intent=str(payload.get("operator_intent") or "diagnose_failure"),
            hypotheses=[Hypothesis.from_dict(row) for row in payload.get("hypotheses") or []],
            evidence=list(payload.get("evidence") or []),
            missing_evidence=list(payload.get("missing_evidence") or []),
            completed_checks=list(payload.get("completed_checks") or []),
            next_best_action=str(payload.get("next_best_action") or ""),
            next_best_action_key=str(payload.get("next_best_action_key") or ""),
            timeline=list(payload.get("timeline") or []),
            conclusion=str(payload.get("conclusion") or ""),
            confidence_score=_safe_float(payload.get("confidence_score"), default=0.0),
            confidence_label=str(payload.get("confidence_label") or "weak"),
            updated_at=str(payload.get("updated_at") or datetime.now(tz=UTC).isoformat()),
            meta=dict(payload.get("meta") or {}),
        )


def target_label_from_row(row: dict[str, Any]) -> str:
    project = str(row.get("project") or "—")
    service = str(row.get("service") or "—")
    environment = str(row.get("environment") or "—")
    return f"{project} / {environment} / {service}" if service != "—" else f"{project} / {service}"


def _safe_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
