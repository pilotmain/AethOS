# SPDX-License-Identifier: Apache-2.0
"""Confidence modeling 2.0 — evidence-quality-based scoring."""

from __future__ import annotations

from typing import Any


def score_merged_confidence(
    *,
    bundle: list[dict[str, Any]],
    agent_results: list[dict[str, Any]],
    correlation: dict[str, Any] | None,
    deployment_intel: dict[str, Any] | None,
    conflicts: list[dict[str, str]],
) -> dict[str, Any]:
    """Score confidence from evidence quality — not agent count alone."""
    reasons: list[str] = []
    gaps: list[str] = []
    score = 0.0

    intel = deployment_intel or {}
    tq = str(intel.get("telemetry_quality") or "low")
    if tq == "high":
        score += 3
        reasons.append("high-quality provider telemetry")
    elif tq == "medium":
        score += 2
        reasons.append("provider telemetry available")
    elif intel.get("credential_state") == "unavailable":
        gaps.append("provider credentials missing")
    else:
        gaps.append("limited provider telemetry")

    if intel.get("logs_available"):
        score += 1.5
        reasons.append("deployment logs available")
    else:
        gaps.append("deployment logs unavailable")

    fresh = _artifact_freshness(bundle)
    if fresh >= 0.8:
        score += 1
        reasons.append("fresh artifact evidence")
    elif fresh < 0.3 and bundle:
        gaps.append("stale artifact evidence")

    corr = correlation or {}
    cc = int(corr.get("correlation_count") or 0)
    if cc >= 3:
        score += 2
        reasons.append("multi-source timeline correlation")
    elif cc >= 1:
        score += 1
        reasons.append("partial timeline correlation")
    else:
        gaps.append("timeline partially uncorrelated")

    agreement = _evidence_agreement(agent_results, corr)
    if agreement:
        score += 1
        reasons.append("evidence agreement across agents")
    if conflicts:
        score -= 1
        gaps.append("contradictory evidence detected")

    if any(r.get("agent_id") == "web_evidence" for r in agent_results):
        browser = next((r for r in agent_results if r.get("agent_id") == "web_evidence"), {})
        bp = browser.get("substrate_payload") or {}
        if bp.get("target_unresolved"):
            gaps.append("browser evidence unavailable")
        elif bp.get("ok") or bp.get("metadata_only"):
            score += 0.5
            reasons.append("browser/metadata evidence")

    if score >= 5:
        level = "high"
    elif score >= 3:
        level = "medium"
    else:
        level = "low"

    return {
        "level": level,
        "score": round(score, 2),
        "reasons": reasons[:8],
        "gaps": gaps[:6],
        "contradictions": [c.get("detail") for c in conflicts[:3]],
    }


def _artifact_freshness(bundle: list[dict[str, Any]]) -> float:
    if not bundle:
        return 0.0
    from time import time

    now = time()
    fresh = 0
    for item in bundle:
        rec = item.get("record") or {}
        created = rec.get("created_at")
        if isinstance(created, (int, float)) and now - created < 3600:
            fresh += 1
        elif created:
            fresh += 0.5
    return fresh / len(bundle)


def _evidence_agreement(results: list[dict[str, Any]], correlation: dict[str, Any]) -> bool:
    prov = next((r for r in results if r.get("agent_id") == "provider_ops"), {})
    if prov.get("credential_required"):
        return False
    conc = correlation.get("conclusions") or {}
    return bool(conc.get("confirmed")) and int(correlation.get("correlation_count") or 0) >= 1
