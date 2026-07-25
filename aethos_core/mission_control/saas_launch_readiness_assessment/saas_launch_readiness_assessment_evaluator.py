# SPDX-License-Identifier: Apache-2.0
"""FIX 309 — SaaS launch readiness assessment evaluator."""

from __future__ import annotations

from typing import Any


def score_domain(*, signals_ready: int, signals_total: int, blockers: list[str]) -> str:
    if blockers:
        return "NOT_READY"
    if signals_total == 0:
        return "PARTIALLY_READY"
    ratio = signals_ready / signals_total
    if ratio >= 1.0:
        return "LAUNCH_READY"
    if ratio >= 0.75:
        return "READY"
    if ratio >= 0.4:
        return "PARTIALLY_READY"
    return "NOT_READY"


def derive_overall_status(*, domain_scores: dict[str, str], risks: list[dict[str, Any]]) -> str:
    scores = list(domain_scores.values())
    if any(score == "NOT_READY" for score in scores):
        return "BLOCKED"
    if any(r.get("level") == "critical" for r in risks):
        return "BLOCKED"
    if any(score == "PARTIALLY_READY" for score in scores):
        return "CONDITIONAL"
    if all(score in {"READY", "LAUNCH_READY"} for score in scores):
        if all(score == "LAUNCH_READY" for score in scores):
            return "READY_FOR_PUBLIC_LAUNCH"
        return "READY_FOR_LIMITED_BETA"
    return "CONDITIONAL"


def build_domain_report(
    *,
    report_id: str,
    domain: str,
    checks: list[dict[str, Any]],
    evidence_sources: list[str],
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    blockers = blockers or []
    ready_count = sum(1 for check in checks if check.get("ready"))
    score = score_domain(
        signals_ready=ready_count,
        signals_total=len(checks),
        blockers=blockers,
    )
    return {
        "report_id": report_id,
        "domain": domain,
        "score": score,
        "checks": checks,
        "blockers": blockers,
        "evidence_sources": evidence_sources,
        "launch_authority": False,
        "read_only": True,
    }


def aggregate_risks(*, domain_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    for report in domain_reports:
        domain = str(report.get("domain") or "")
        score = str(report.get("score") or "")
        for blocker in report.get("blockers") or []:
            risks.append(
                {
                    "risk_id": f"{domain}-{blocker}",
                    "domain": domain,
                    "level": "critical" if score == "NOT_READY" else "high",
                    "detail": blocker,
                    "evidence_backed": True,
                    "read_only": True,
                }
            )
        for check in report.get("checks") or []:
            if not check.get("ready"):
                risks.append(
                    {
                        "risk_id": f"{domain}-{check.get('check_id', 'check')}",
                        "domain": domain,
                        "level": "medium" if score != "NOT_READY" else "high",
                        "detail": check.get("detail") or check.get("label"),
                        "evidence_backed": True,
                        "read_only": True,
                    }
                )
    return risks
