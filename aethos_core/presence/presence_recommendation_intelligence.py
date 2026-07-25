# SPDX-License-Identifier: Apache-2.0
"""Presence recommendation intelligence — contextual actionable recommendations."""

from __future__ import annotations

from time import time
from typing import Any
from uuid import uuid4

from aethos_core.intelligence.recommendations import generate_recommendations_from_anomalies, list_recommendations


def synthesize_intelligent_recommendations(
    *,
    clusters: list[dict[str, Any]],
    scored_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate contextual recommendations from clusters — merge with existing queue."""
    existing = {str(r.get("suggestion_fingerprint") or r.get("title")): r for r in list_recommendations(limit=20)}
    created: list[dict[str, Any]] = []

    for cluster in clusters:
        rec = _recommendation_for_cluster(cluster)
        if not rec:
            continue
        fp = rec.get("suggestion_fingerprint")
        if fp and fp in existing:
            created.append(existing[fp])
            continue
        created.append(rec)

    if not created:
        created.extend(_from_scored_events(scored_events))

    if not created:
        anomalies = _anomalies_from_clusters(clusters)
        if anomalies:
            created.extend(generate_recommendations_from_anomalies(anomalies))

    return _enrich_recommendations(created[:8])


def _recommendation_for_cluster(cluster: dict[str, Any]) -> dict[str, Any] | None:
    theme = str(cluster.get("theme") or "")
    count = int(cluster.get("event_count") or 0)
    if count < 2 and theme not in ("workflow_instability", "deployment_instability"):
        return None

    if theme == "workflow_instability":
        return _rec(
            title="GitHub workflow rerun instability",
            action="Generate governed workflow-resolution preflight for GitHub rerun instability?",
            rationale=f"{count} correlated workflow signals in cluster {cluster.get('cluster_id')}",
            kind="flaky_workflow",
            severity="elevated" if count < 4 else "high",
            confidence=float(cluster.get("confidence") or 0.75),
        )
    if theme == "deployment_instability":
        return _rec(
            title="Deployment instability investigation",
            action="Review deployment diagnostics and Railway restart timeline before additional rollout attempts?",
            rationale=f"{count} deployment-related signals across {', '.join(cluster.get('providers') or ['providers'])}",
            kind="deployment_instability",
            severity="elevated",
            confidence=float(cluster.get("confidence") or 0.7),
        )
    if theme == "dependency_risk":
        return _rec(
            title="Dependency modernization review",
            action="Prepare governed dependency modernization preflight across affected workspaces?",
            rationale="Dependency risk cluster detected with recurring CVE/churn signals",
            kind="dependency_churn",
            severity="medium",
            confidence=float(cluster.get("confidence") or 0.65),
        )
    return None


def _from_scored_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for event in events:
        if str(event.get("priority") or "") not in ("URGENT", "CRITICAL", "ELEVATED"):
            continue
        src = str(event.get("source") or "")
        if "workflow" in src or "workflow" in str(event.get("summary", "")).lower():
            out.append(
                _rec(
                    title="Workflow instability",
                    action="Generate governed engineering patch proposal for workflow rerun convergence?",
                    rationale=str(event.get("attention_reason") or event.get("summary")),
                    kind="flaky_workflow",
                    severity="elevated",
                    confidence=float(event.get("confidence") or 0.7),
                )
            )
            break
    return out


def _anomalies_from_clusters(clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    for c in clusters:
        if c.get("theme") == "internal_substrate":
            continue
        anomalies.append(
            {
                "anomaly_id": f"anom-clust-{c.get('cluster_id', '')[:8]}",
                "kind": c.get("theme"),
                "severity": "high" if int(c.get("event_count") or 0) >= 4 else "medium",
                "confidence": float(c.get("confidence") or 0.7),
                "evidence": [t.get("summary") for t in (c.get("timeline") or [])[:4] if t.get("summary")],
                "related_systems": c.get("related_systems") or [],
                "recommended_action": _recommendation_for_cluster(c).get("suggested_action") if _recommendation_for_cluster(c) else "Review in Mission Control",
            }
        )
    return anomalies


def _rec(
    *,
    title: str,
    action: str,
    rationale: str,
    kind: str,
    severity: str,
    confidence: float,
) -> dict[str, Any]:
    fp = f"{kind}:{action[:60]}"
    return {
        "recommendation_id": f"prec-{uuid4().hex[:10]}",
        "title": title,
        "suggested_action": action,
        "operator_rationale": rationale,
        "suggestion_fingerprint": fp,
        "severity": severity,
        "confidence": round(confidence, 2),
        "kind": kind,
        "approval_required": True,
        "autonomous_execution_blocked": True,
        "governance_statement": "Human approval required before preflight or execution.",
        "status": "active",
        "created_at": time(),
    }


def _enrich_recommendations(recs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for rec in recs:
        rec.setdefault("operator_rationale", rec.get("operator_rationale") or "Correlated operational evidence")
        rec.setdefault("governance_statement", "Human approval required — no auto-execution.")
    return recs
