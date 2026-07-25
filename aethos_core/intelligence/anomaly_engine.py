# SPDX-License-Identifier: Apache-2.0
"""Operational anomaly engine — evidence-grounded risk detection."""

from __future__ import annotations

from time import time
from typing import Any
from uuid import uuid4

from aethos_core.intelligence.confidence_authority import score_anomaly_confidence
from aethos_core.intelligence.operational_memory import operational_memory_snapshot, recurring_failure_kinds


def detect_operational_anomalies(
    *,
    observations: dict[str, Any],
    window_hours: int = 48,
) -> list[dict[str, Any]]:
    """Detect anomalies from reality loop observations."""
    events = list(observations.get("events") or [])
    patterns = list(observations.get("recurring_patterns") or [])
    anomalies: list[dict[str, Any]] = []

    by_cat = _count_by_category(events)
    for cat, count in by_cat.items():
        if count < 3:
            continue
        anomaly = _build_anomaly(
            kind=cat,
            count=count,
            events=events,
            patterns=patterns,
            window_hours=window_hours,
        )
        if anomaly:
            anomalies.append(anomaly)

    for row in recurring_failure_kinds(min_count=3, window_hours=window_hours):
        if any(a.get("kind") == row["kind"] for a in anomalies):
            continue
        anomalies.append(
            _anomaly_record(
                kind=str(row["kind"]),
                severity="medium",
                confidence=score_anomaly_confidence(event_count=int(row["count"]), recurring=True),
                evidence=[f"Recurring {row['kind']} signal: {row['count']} occurrences"],
                related_systems=_systems_for_kind(str(row["kind"])),
                recommended_action=_action_for_kind(str(row["kind"])),
            )
        )

    drift = observations.get("drift") or {}
    if drift.get("detected"):
        anomalies.append(
            _anomaly_record(
                kind="operational_drift",
                severity=str(drift.get("severity") or "medium"),
                confidence=float(drift.get("confidence") or 0.75),
                evidence=list(drift.get("signals") or []),
                related_systems=list(drift.get("systems") or ["monorepo"]),
                recommended_action="Review operational drift signals in Mission Control",
            )
        )

    stale = observations.get("telemetry_freshness") or {}
    if stale.get("stale"):
        anomalies.append(
            _anomaly_record(
                kind="stale_telemetry",
                severity="low",
                confidence=0.78,
                evidence=[f"Stale telemetry: {s}" for s in (stale.get("stale_sources") or [])[:4]],
                related_systems=["observability"],
                recommended_action="Refresh readonly diagnostics",
            )
        )

    return sorted(anomalies, key=lambda a: _severity_rank(a.get("severity")), reverse=True)[:12]


def _count_by_category(events: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in events:
        cat = str(e.get("category") or "unknown")
        out[cat] = out.get(cat, 0) + 1
    return out


def _build_anomaly(
    *,
    kind: str,
    count: int,
    events: list[dict[str, Any]],
    patterns: list[str],
    window_hours: int,
) -> dict[str, Any] | None:
    samples = [str(e.get("detail") or "") for e in events if str(e.get("category") or "") == kind][:4]
    recurring = any(kind.replace("_", " ") in p.lower() for p in patterns)
    mem = operational_memory_snapshot(window_hours=window_hours)
    mem_count = int((mem.get("by_kind") or {}).get(kind, 0))
    confidence = score_anomaly_confidence(
        event_count=count,
        recurring=recurring,
        correlated_evidence=min(len(samples), 3),
        memory_reinforcement=min(mem_count, 3),
    )
    severity = "high" if count >= 4 or kind in ("flaky_workflow", "provider_auth_failure") else "medium"
    if kind in ("dependency_churn", "stale_telemetry"):
        severity = "low" if count < 5 else "medium"
    return _anomaly_record(
        kind=kind,
        severity=severity,
        confidence=confidence,
        evidence=samples or [f"{count} `{kind}` signals in {window_hours}h window"],
        related_systems=_systems_for_kind(kind),
        recommended_action=_action_for_kind(kind),
    )


def _anomaly_record(
    *,
    kind: str,
    severity: str,
    confidence: float,
    evidence: list[str],
    related_systems: list[str],
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "anomaly_id": f"anom-{uuid4().hex[:12]}",
        "kind": kind,
        "severity": severity,
        "confidence": confidence,
        "evidence": evidence[:6],
        "related_systems": related_systems,
        "recommended_action": recommended_action,
        "detected_at": time(),
        "readonly": True,
    }


def _systems_for_kind(kind: str) -> list[str]:
    mapping = {
        "flaky_workflow": ["CI", "GitHub Actions"],
        "workflow_rerun_failure": ["CI", "GitHub Actions"],
        "deployment_instability": ["Railway", "deployments"],
        "browser_evidence_failure": ["browser evidence", "deployments"],
        "provider_auth_failure": ["credentials", "Railway"],
        "dependency_churn": ["dependencies", "npm"],
        "dependency_risk": ["dependencies", "security"],
        "validation_failure_trend": ["engineering validation"],
        "operational_drift": ["monorepo", "runtime"],
        "stale_telemetry": ["observability"],
    }
    return mapping.get(kind, ["operations"])


def _action_for_kind(kind: str) -> str:
    mapping = {
        "flaky_workflow": "Generate governed engineering patch proposal",
        "workflow_rerun_failure": "Generate governed engineering patch proposal",
        "deployment_instability": "Inspect deployment timeline and browser evidence",
        "browser_evidence_failure": "Capture browser deployment evidence",
        "provider_auth_failure": "Review credential center diagnostics",
        "dependency_churn": "Prepare dependency modernization preflight",
        "dependency_risk": "Prepare dependency modernization preflight",
        "validation_failure_trend": "Review validation center failures",
        "operational_drift": "Review drift detection timeline",
        "stale_telemetry": "Run readonly diagnostics refresh",
    }
    return mapping.get(kind, "Review operational intelligence in Mission Control")


def _severity_rank(severity: str | None) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(str(severity or "low"), 0)
