# SPDX-License-Identifier: Apache-2.0
"""Confidence-based Vercel project health — production vs preview vs latest deployment."""

from __future__ import annotations

import re

from aethos_core.browser.platforms.vercel.vercel_entities import (
    HealthState,
    InfrastructureHealthSummary,
    VercelInventoryArtifact,
    VercelProject,
)
from aethos_core.browser.platforms.vercel.vercel_url_classifier import (
    classify_url_type,
    is_production_confidence_url,
)


def _deploy_low(text: str) -> str:
    return (text or "").lower()


def _card_text(project: VercelProject) -> str:
    return _deploy_low(
        f"{project.deployment_state or ''} {project.deployment_status or ''} "
        f"{project.last_deploy_state or ''}"
    )


def _explicit_no_production(card: str) -> bool:
    return bool(
        re.search(
            r"\b(no production deployment|not deployed to production|no production)\b",
            card,
            re.I,
        )
    )


def _explicit_failed(card: str) -> bool:
    return bool(re.search(r"\b(failed|error|errored|build failed|cancelled|canceled)\b", card, re.I))


def _has_deploy_activity(card: str) -> bool:
    return bool(
        re.search(
            r"\b(deployed|deployment|ready|production|building|queued)\b",
            card,
            re.I,
        )
    )


def _has_verified_production_url(project: VercelProject) -> bool:
    if not project.production_url:
        return False
    if not is_production_confidence_url(project.url_type):
        return False
    conf = getattr(project, "production_url_confidence", "none") or "none"
    if conf == "high" and (
        getattr(project, "production_url_verified", False)
        or project.production_url_source
        in (
            "memory",
            "detail_page",
            "deployments_tab",
            "project_href",
            "custom_domain",
            "project_card",
        )
    ):
        return True
    return conf == "high" and project.production_url_source == "memory"


def _has_any_url(project: VercelProject) -> bool:
    return bool(project.production_url) or bool(project.known_domains)


def infer_latest_deployment_state(project: VercelProject) -> str:
    card = _card_text(project)
    state = _deploy_low(project.deployment_state or project.last_deploy_state or "")
    if _explicit_failed(card) or any(x in state for x in ("fail", "error", "cancel")):
        return "failed"
    if any(x in state for x in ("building", "deploying", "queued")):
        return "building"
    if state in ("ready", "success", "production", "deployed") or _has_deploy_activity(card):
        return "success"
    return "unknown"


def infer_latest_deployment_scope(project: VercelProject) -> str:
    card = _card_text(project)
    state = _deploy_low(project.deployment_state or "")
    if "production" in card or state == "production":
        return "production"
    if "preview" in card or state == "preview":
        return "preview"
    if project.url_type == "preview_vercel":
        return "preview"
    if is_production_confidence_url(project.url_type):
        return "production"
    return "unknown"


def infer_production_health(project: VercelProject) -> str:
    """healthy | down | unknown — production app only, not preview deploys."""
    if project.url_type == "preview_vercel":
        return "unknown"
    if _has_verified_production_url(project):
        if (
            project.latest_deployment_scope == "production"
            and project.latest_deployment_state == "failed"
        ):
            return "down"
        return "healthy"
    if is_production_confidence_url(project.url_type) and project.production_url:
        if (
            project.latest_deployment_scope == "production"
            and project.latest_deployment_state == "failed"
        ):
            return "down"
        if project.latest_deployment_state == "failed":
            return "unknown"
        return "unknown"
    if _explicit_no_production(_card_text(project)):
        return "unknown"
    return "unknown"


def infer_operator_status(project: VercelProject) -> str:
    """healthy | needs_attention | unknown — operator-facing rollup."""
    if project.production_health == "down":
        return "needs_attention"
    if project.latest_deployment_state == "failed":
        if project.production_health == "healthy":
            return "needs_attention"
        if project.latest_deployment_scope == "preview" or project.url_type == "preview_vercel":
            return "needs_attention"
        return "needs_attention"
    if project.production_health == "healthy" and project.latest_deployment_state != "failed":
        return "healthy"
    if _explicit_no_production(_card_text(project)):
        return "needs_attention"
    if project.latest_deployment_state == "building":
        return "needs_attention"
    return "unknown"


def collect_health_evidence(project: VercelProject) -> list[str]:
    evidence: list[str] = []
    if project.production_url_verified or project.production_url_source in (
        "memory",
        "detail_page",
        "deployments_tab",
        "project_href",
        "custom_domain",
        "project_card",
    ):
        evidence.append("production_url_verified")
    if project.latest_deployment_state == "failed":
        evidence.append("latest_deployment_failed")
    if project.latest_deployment_scope == "production":
        evidence.append("scope_detected: production")
    elif project.latest_deployment_scope == "preview":
        evidence.append("scope_detected: preview")
    if project.production_url_source:
        evidence.append(f"source: {project.production_url_source}")
    return evidence


def apply_deployment_semantics(project: VercelProject) -> None:
    if project.production_url:
        project.url_type = classify_url_type(project.production_url)
    else:
        project.url_type = "unknown"
    project.latest_deployment_state = infer_latest_deployment_state(project)
    project.latest_deployment_scope = infer_latest_deployment_scope(project)
    project.production_health = infer_production_health(project)
    project.operator_status = infer_operator_status(project)
    project.evidence = collect_health_evidence(project)


def attention_reason_for(project: VercelProject) -> str | None:
    apply_deployment_semantics(project)
    card = _card_text(project)

    if project.latest_deployment_state == "failed":
        if project.production_health == "healthy":
            if project.latest_deployment_scope == "preview":
                return "production healthy, preview failed"
            return "latest deployment failed"
        if project.latest_deployment_scope == "preview" or project.url_type == "preview_vercel":
            return "latest deployment failed — production impact unclear"
        if "scope_detected: production" not in (project.evidence or []):
            return "latest deployment failed — production impact unclear"
        return "latest deployment failed"

    if _explicit_no_production(card):
        return "no production deployment"
    if any(x in card for x in ("building", "deploying", "queued")):
        return "deployment in progress"
    if any(x in card for x in ("degraded", "slow", "latency")):
        return "degraded performance signal"
    if project.url_type == "preview_vercel" and not is_production_confidence_url(project.url_type):
        if project.latest_deployment_state == "success":
            return "latest preview exists"
    if not _has_any_url(project):
        if _deploy_low(project.deployment_state or "") == "preview":
            return "preview only"
    return None


def classify_project_health(project: VercelProject) -> HealthState:
    apply_deployment_semantics(project)
    reason = attention_reason_for(project)
    project.attention_reason = reason
    card = _card_text(project)

    def _finish(state: HealthState, *, confidence: str | None = None) -> HealthState:
        if confidence:
            project.health_confidence = confidence
        project.health = state
        return state

    if project.production_health == "down":
        return _finish(HealthState.FAILED, confidence="failed")

    if project.latest_deployment_state == "failed":
        if project.production_health == "healthy":
            return _finish(HealthState.LIKELY_DEGRADED, confidence="likely_degraded")
        if project.latest_deployment_scope == "preview" or project.url_type == "preview_vercel":
            return _finish(HealthState.LIKELY_DEGRADED, confidence="likely_degraded")
        if not is_production_confidence_url(project.url_type):
            return _finish(HealthState.LIKELY_DEGRADED, confidence="likely_degraded")
        return _finish(HealthState.FAILED, confidence="failed")

    if _has_verified_production_url(project):
        return _finish(HealthState.HEALTHY, confidence="healthy")

    if project.production_url and is_production_confidence_url(project.url_type):
        conf = getattr(project, "production_url_confidence", "") or ""
        if getattr(project, "production_url_verified", False):
            return _finish(HealthState.HEALTHY, confidence="healthy")
        if conf in ("medium", "high"):
            return _finish(HealthState.LIKELY_HEALTHY, confidence="likely_healthy")

    if project.url_type == "preview_vercel":
        if reason == "latest preview exists":
            project.attention_reason = "latest preview exists — production status unclear"
        return _finish(HealthState.UNKNOWN, confidence="unknown")

    if reason == "no production deployment":
        return _finish(HealthState.LIKELY_DEGRADED, confidence="likely_degraded")

    if reason == "preview only":
        return _finish(HealthState.UNKNOWN, confidence="unknown")

    if reason in ("deployment in progress", "degraded performance signal"):
        return _finish(HealthState.LIKELY_DEGRADED, confidence="likely_degraded")

    state = _deploy_low(project.deployment_state or project.last_deploy_state or "")
    if state in ("ready", "success", "production") or _has_deploy_activity(card):
        return _finish(HealthState.LIKELY_HEALTHY, confidence="likely_healthy")

    if not _has_any_url(project) and not reason:
        return _finish(HealthState.UNKNOWN, confidence="unknown")

    if reason:
        return _finish(HealthState.LIKELY_DEGRADED, confidence="likely_degraded")

    return _finish(HealthState.UNKNOWN, confidence="unknown")


def display_attention_label(project: VercelProject) -> str | None:
    apply_deployment_semantics(project)
    if project.operator_status == "healthy" and project.latest_deployment_state == "failed":
        return project.attention_reason or "needs attention — latest deployment failed"
    if project.health == HealthState.UNKNOWN and project.url_type == "preview_vercel":
        return "latest preview exists — production status unclear"
    if project.health == HealthState.UNKNOWN and not project.production_url:
        return "production status not confirmed"
    if project.health == HealthState.UNKNOWN and project.production_url:
        return "production status unclear"
    if project.attention_reason:
        if project.attention_reason == "failed deployment":
            return "needs attention — latest deployment failed"
        return project.attention_reason
    if project.operator_status == "needs_attention":
        return "needs attention"
    return None


def operator_display_label(project: VercelProject) -> str:
    """Chat/report line — e.g. `pilot-os-ui · needs attention — latest preview deployment failed`."""
    if project.health == HealthState.UNKNOWN and project.production_url:
        classify_project_health(project)
    apply_deployment_semantics(project)
    label = display_attention_label(project)
    if project.production_health == "down" and "scope_detected: production" in (project.evidence or []):
        return f"{project.name} · production down"
    if project.production_health == "down":
        return f"{project.name} · latest deployment failed — production impact unclear"
    if project.operator_status == "healthy" and project.production_health == "healthy":
        if project.url_type == "custom_domain":
            return f"{project.name} · healthy (custom domain)"
        return f"{project.name} · healthy"
    if label:
        return f"{project.name} · {label}"
    if project.health in (HealthState.HEALTHY, HealthState.LIKELY_HEALTHY):
        return f"{project.name} · likely healthy"
    return f"{project.name} · {project.health.value.replace('_', ' ')}"


def apply_health_to_projects(projects: list[VercelProject]) -> InfrastructureHealthSummary:
    summary = InfrastructureHealthSummary()
    for p in projects:
        p.health = classify_project_health(p)
        if p.health == HealthState.HEALTHY:
            summary.healthy.append(p.name)
        elif p.health == HealthState.LIKELY_HEALTHY:
            summary.likely_healthy.append(p.name)
        elif p.health == HealthState.FAILED:
            summary.failed.append(p.name)
            if p.attention_reason:
                summary.needs_attention.append((p.name, p.attention_reason))
        elif p.health in (HealthState.DEGRADED, HealthState.LIKELY_DEGRADED):
            summary.degraded.append(p.name)
            if p.health == HealthState.LIKELY_DEGRADED:
                summary.likely_degraded.append(p.name)
            if p.attention_reason:
                summary.needs_attention.append((p.name, p.attention_reason))
        else:
            summary.unknown.append(p.name)
            if p.attention_reason:
                summary.needs_attention.append((p.name, p.attention_reason))
    return summary


def count_health_buckets(projects: list[VercelProject]) -> tuple[int, int, int, int]:
    healthy = failing = no_prod = degraded = 0
    for p in projects:
        if p.health in (HealthState.HEALTHY, HealthState.LIKELY_HEALTHY):
            healthy += 1
        elif p.health == HealthState.FAILED:
            failing += 1
        elif p.health in (HealthState.DEGRADED, HealthState.LIKELY_DEGRADED):
            degraded += 1
            if p.attention_reason and "no production" in (p.attention_reason or ""):
                no_prod += 1
    return healthy, failing, no_prod, degraded


def enrich_inventory(artifact: VercelInventoryArtifact) -> VercelInventoryArtifact:
    artifact.health_summary = apply_health_to_projects(artifact.projects)
    h, f, np, d = count_health_buckets(artifact.projects)
    artifact.healthy_count = h
    artifact.failing_count = f
    artifact.no_prod_count = np
    artifact.degraded_count = d
    artifact.unknown_count = sum(
        1 for p in artifact.projects if p.health == HealthState.UNKNOWN
    )
    return artifact
