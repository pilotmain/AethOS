# SPDX-License-Identifier: Apache-2.0
"""Provider signal binding — bind Tier-1 provider truth into conversational grounding."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.cross_surface_reality_convergence.surface_alignment import _subject_overlap

_TIER1_PROVIDERS = ("railway", "github", "vercel")


def _infer_provider(*, subject: str | None, category: str | None = None) -> str:
    lower = (subject or "").lower()
    cat = (category or "").lower()
    if "github" in lower or "workflow" in lower or "ci" in lower or cat == "provider":
        if "github" in lower or "workflow" in lower or "ci" in lower:
            return "github"
    if "vercel" in lower or "endpoint" in lower or "deploy" in lower and "railway" not in lower:
        if "vercel" in lower:
            return "vercel"
    return "railway"


def _assess_provider(provider: str) -> dict[str, Any]:
    if provider == "railway":
        from aethos_core.provider_runtime_truth.railway_runtime_convergence import assess_railway_runtime_convergence

        return assess_railway_runtime_convergence()
    if provider == "github":
        from aethos_core.provider_runtime_truth.github_ci_reconciliation import assess_github_ci_reconciliation

        return assess_github_ci_reconciliation()
    if provider == "vercel":
        from aethos_core.provider_runtime_truth.vercel_endpoint_convergence import assess_vercel_endpoint_convergence

        return assess_vercel_endpoint_convergence()
    return {"converged": False, "summary": "Provider not in Tier-1 scope."}


def bind_provider_signals(
    *,
    primary_subject: str | None = None,
    category: str | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    """Bind live Tier-1 provider signals when subject aligns."""
    provider = provider or _infer_provider(subject=primary_subject, category=category)
    if provider not in _TIER1_PROVIDERS:
        return {
            "provider": provider,
            "bound": False,
            "subject_aligned": False,
            "signals_fresh": False,
            "summary": "Provider outside Tier-1 live grounding scope.",
        }

    checked_at = time()
    truth = _assess_provider(provider)
    truth_subject = {
        "railway": "Railway deployment recovery",
        "github": "GitHub workflow execution",
        "vercel": "Vercel deployment endpoint",
    }.get(provider, primary_subject or "operational recovery")

    subject_aligned = True
    if primary_subject:
        subject_aligned = _subject_overlap(str(primary_subject), str(truth_subject)) >= 0.2 or _subject_overlap(
            str(primary_subject), provider
        ) >= 0.5

    converged = bool(truth.get("converged"))
    stabilized = converged and subject_aligned
    sustaining = converged  # sustained window required before "fully proven"

    runtime_signals = {
        "provider": provider,
        "deployment_stable": stabilized,
        "sustained_verification_active": not converged or sustaining,
        "replay_monitoring_active": True,
        "checked_at": checked_at,
        "summary": truth.get("summary") or f"{provider} runtime signal assessed.",
        "stabilizing_not_proven": converged and sustaining,
        "fully_proven": False,  # never claim fully proven without sustained windows
    }

    return {
        "provider": provider,
        "bound": True,
        "subject_aligned": subject_aligned,
        "signals_fresh": True,
        "checked_at": checked_at,
        "provider_truth": truth,
        "runtime_signals": runtime_signals,
        "stabilized": stabilized,
        "sustaining": sustaining,
        "summary": truth.get("summary", f"{provider} provider signals bound."),
    }
