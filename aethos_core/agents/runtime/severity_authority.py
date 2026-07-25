# SPDX-License-Identifier: Apache-2.0
"""Canonical severity authority — single source for final report severity."""

from __future__ import annotations

from typing import Any

_LEVELS = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def resolve_final_severity(
    *,
    agent_results: list[dict[str, Any]],
    report_mode: str,
    confidence: dict[str, Any] | None = None,
    provider_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute one canonical severity from substrate signals — never exaggerate."""
    reasons: list[str] = []
    score = 0

    prov = provider_payload or {}
    failed = ((prov.get("correlation") or {}).get("failed_deployment") or {})
    failed_state = str(failed.get("state") or prov.get("deployment_state") or "").lower()
    confirmed_failure = bool(
        failed.get("id")
        and failed_state in ("failed", "crashed", "error", "crashed")
    )
    credential_missing = bool(prov.get("credential_required"))

    if confirmed_failure:
        score += 6
        reasons.append(f"Confirmed failed deployment `{failed.get('id')}` ({failed_state})")
    elif credential_missing:
        score += 0
        reasons.append("Provider credential unavailable — no confirmed deployment failure evidence")
    elif report_mode == "deployment_failure":
        score += 0
        reasons.append("No confirmed failed deployment found in provider evidence")

    if report_mode == "architecture_risk":
        for r in agent_results:
            if r.get("agent_id") != "code_intelligence":
                continue
            payload = r.get("substrate_payload") or {}
            bottlenecks = payload.get("bottlenecks") or []
            if bottlenecks:
                score += 2
                reasons.append(f"{len(bottlenecks)} orchestration bottleneck(s) identified")
            gov = payload.get("governance_observations") or []
            if any("not detected" in str(g).lower() for g in gov):
                score += 1
                reasons.append("Governance gap detected in architecture scan")

    if report_mode == "pr_proposal":
        for r in agent_results:
            payload = r.get("substrate_payload") or {}
            if r.get("agent_id") == "code_intelligence" and payload.get("dependency_findings"):
                sev = str((payload.get("dependency_findings") or {}).get("severity") or payload.get("severity") or "")
                if sev.lower() == "high":
                    score += 3
                    reasons.append("High-severity dependency vulnerabilities in audit")
                elif sev.lower() == "medium":
                    score += 2
                    reasons.append("Medium dependency risk in audit")
                else:
                    score += 1
                    reasons.append("Dependency modernization recommended from audit")

    conf_level = str((confidence or {}).get("level") or "low").lower()
    if conf_level == "high" and confirmed_failure:
        score += 1
        reasons.append("High confidence from multi-source evidence")
    elif conf_level == "low" and report_mode == "deployment_failure":
        reasons.append("Low confidence — insufficient cross-source confirmation")

    # Ignore per-agent severity recommendations — authority decides
    if score >= 8:
        level = "CRITICAL"
    elif score >= 5:
        level = "HIGH"
    elif score >= 2:
        level = "MEDIUM"
    else:
        level = "LOW"

    if report_mode == "deployment_failure" and not confirmed_failure and level in ("HIGH", "CRITICAL"):
        level = "LOW" if score < 3 else "MEDIUM"
        if "No confirmed failed deployment" not in " ".join(reasons):
            reasons.append("Severity capped — no confirmed production/runtime failure evidence")

    return {"severity": level, "severity_reason": reasons[:8], "score": score}
