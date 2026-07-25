# SPDX-License-Identifier: Apache-2.0
"""Failure diagnostic artifact refinement — evidence priority and operator clarity."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.execution.execution_artifacts import ExecutionArtifact
from aethos_core.operations.execution.execution_evidence import (
    CONFIDENCE_CONFIRMED,
    CONFIDENCE_INSUFFICIENT,
    CONFIDENCE_LIKELY,
    _FAILED_STATES,
    evidence_from_deployment,
    evidence_from_inventory_tags,
    evidence_from_log_payload,
    evidence_from_reachability,
    evidence_item,
    operational_events_from_deployment,
    select_failed_deployment,
    sort_operational_events,
)
from aethos_core.operations.execution.execution_formatting import format_timestamp, truncate_text

_PRODUCTION_TARGETS = frozenset({"production", "prod"})


def select_last_successful_production_deployment(deployments: list[Any]) -> dict[str, Any] | None:
    for dep in deployments:
        if not isinstance(dep, dict):
            continue
        state = str(dep.get("state") or "").lower()
        target = str(dep.get("target") or "").lower()
        if state == "ready" and target in _PRODUCTION_TARGETS:
            return dep
    for dep in deployments:
        if not isinstance(dep, dict):
            continue
        if str(dep.get("state") or "").lower() == "ready":
            return dep
    return None


def deployment_summary(dep: dict[str, Any] | None) -> dict[str, Any]:
    if not dep:
        return {}
    return {
        "id": str(dep.get("id") or ""),
        "state": str(dep.get("state") or "unknown"),
        "target": str(dep.get("target") or "unknown"),
        "branch": str(dep.get("branch") or ""),
        "commit": str(dep.get("commit") or ""),
        "created_at": dep.get("created_at"),
        "created_at_label": format_timestamp(dep.get("created_at")),
        "error_message": truncate_text(str(dep.get("error_message") or ""), limit=500),
        "commit_message": truncate_text(str(dep.get("commit_message") or ""), limit=120),
    }


def derive_production_impact(
    *,
    failed_dep: dict[str, Any] | None,
    last_prod: dict[str, Any] | None,
    reachability: dict[str, Any] | None,
    prod_url: str | None,
) -> tuple[str, str, str]:
    failed_target = str((failed_dep or {}).get("target") or "unknown").lower()
    if reachability and reachability.get("reachable") is False:
        return (
            "Production URL appears unreachable from the live probe.",
            CONFIDENCE_LIKELY,
            "down",
        )
    if reachability and reachability.get("reachable") is True and last_prod:
        if failed_target not in _PRODUCTION_TARGETS and failed_target != "unknown":
            return (
                "Unclear / likely not confirmed down — the failed deployment target is not production "
                "and recent production deployments appear ready.",
                CONFIDENCE_INSUFFICIENT,
                "ready",
            )
        if failed_target == "unknown":
            return (
                "Unclear / likely not confirmed down — the failed deployment target is unknown "
                "and recent production deployments appear ready.",
                CONFIDENCE_INSUFFICIENT,
                "ready",
            )
        if failed_target in _PRODUCTION_TARGETS:
            return (
                "Production-scoped deployment failed — production impact may be confirmed.",
                CONFIDENCE_LIKELY,
                "degraded",
            )
        return (
            "No confirmed production outage from API evidence; live URL check succeeded.",
            CONFIDENCE_INSUFFICIENT,
            "ready",
        )
    if last_prod and failed_target in ("unknown", ""):
        return (
            "Unclear — failed deployment target is unknown; a recent successful deployment exists.",
            CONFIDENCE_INSUFFICIENT,
            "unknown",
        )
    if prod_url and not reachability:
        return (
            "Production impact unclear — URL reachability was not checked or URL was unavailable.",
            CONFIDENCE_INSUFFICIENT,
            "unknown",
        )
    return (
        "Production impact could not be confirmed from available API evidence.",
        CONFIDENCE_INSUFFICIENT,
        "unknown",
    )


def build_primary_finding(failed_dep: dict[str, Any] | None) -> str:
    if not failed_dep:
        return "No failed deployment was identified in the recent deployment list."
    dep_id = str(failed_dep.get("id") or "")[:16]
    err = str(failed_dep.get("error_message") or "").strip()
    if err:
        return f"Deployment `{dep_id}` failed because `{truncate_text(err, limit=200)}`."
    return f"Deployment `{dep_id}` failed (state: {failed_dep.get('state', 'unknown')})."


def build_actionable_summary(failed_dep: dict[str, Any] | None, *, api_logs_limited: bool) -> str:
    if not failed_dep:
        return "Insufficient evidence to determine root cause from available API data."
    err = str(failed_dep.get("error_message") or "").strip()
    if not err:
        return "The API did not return a specific failure reason for the failed deployment."
    low = err.lower()
    if "npm run build" in low or "exited with" in low:
        base = (
            "The API reports the failed deployment stopped during the build command. "
            "The exact underlying compile/test error is not available from the API evidence shown here."
        )
    else:
        base = f"The API reports: {truncate_text(err, limit=200)}"
    if api_logs_limited:
        base += " Vercel API provided the failure signal but not detailed build logs."
    return base


def build_next_safe_checks(
    *,
    failed_dep: dict[str, Any] | None,
    last_prod: dict[str, Any] | None,
    api_logs_limited: bool,
) -> list[str]:
    checks: list[str] = []
    if api_logs_limited:
        checks.append("Fetch detailed deployment events/logs if available (API or browser fallback).")
    else:
        checks.append("Review deployment build log excerpts in the evidence artifact.")
    commit = str((failed_dep or {}).get("commit") or "").strip()
    if commit:
        checks.append(f"Inspect commit `{commit}`.")
    if last_prod and failed_dep and last_prod.get("id") != failed_dep.get("id"):
        checks.append("Compare with last successful production deployment.")
    checks.append("Check package/build scripts for the failing branch.")
    return checks


def build_evidence_groups(
    *,
    failed_dep: dict[str, Any] | None,
    last_prod: dict[str, Any] | None,
    all_deployments: list[Any],
    inventory_evidence: list[str],
    log_evidence: list[dict[str, Any]],
    reachability_evidence: dict[str, Any] | None,
    diagnosis_evidence: dict[str, Any] | None,
    source: str,
) -> dict[str, list[dict[str, Any]]]:
    primary: list[dict[str, Any]] = []
    supporting: list[dict[str, Any]] = []
    historical: list[dict[str, Any]] = []
    debug: list[dict[str, Any]] = []

    if failed_dep:
        for item in evidence_from_deployment(failed_dep, source=source):
            if item.get("type") in ("failure_reason", "deployment_state"):
                primary.append({**item, "tier": "primary"})
            else:
                supporting.append({**item, "tier": "supporting"})
    for item in log_evidence:
        tier = "primary" if item.get("type") == "deployment_event" else "supporting"
        (primary if tier == "primary" else supporting).append({**item, "tier": tier})
    if reachability_evidence:
        supporting.append({**reachability_evidence, "tier": "supporting"})
    if diagnosis_evidence:
        primary.append({**diagnosis_evidence, "tier": "primary"})
    if last_prod and failed_dep and last_prod.get("id") != failed_dep.get("id"):
        historical.append(
            evidence_item(
                source=source,
                type="last_successful_production",
                confidence=CONFIDENCE_LIKELY,
                message=(
                    f"Last successful production deployment `{str(last_prod.get('id', ''))[:12]}` "
                    f"on branch `{last_prod.get('branch') or '—'}` · commit `{last_prod.get('commit') or '—'}`"
                ),
                deployment_id=str(last_prod.get("id") or ""),
                tier="historical",
            )
        )
    for tag_item in evidence_from_inventory_tags(inventory_evidence):
        supporting.append({**tag_item, "tier": "supporting"})

    failed_id = str((failed_dep or {}).get("id") or "")
    last_id = str((last_prod or {}).get("id") or "")
    for dep in all_deployments:
        if not isinstance(dep, dict):
            continue
        dep_id = str(dep.get("id") or "")
        if dep_id and dep_id in {failed_id, last_id}:
            continue
        for item in evidence_from_deployment(dep, source=source):
            debug.append({**item, "tier": "debug"})

    return {
        "primary": primary,
        "supporting": supporting,
        "historical": historical,
        "debug": debug,
    }


def enrich_failure_diagnostic_artifact(
    artifact: ExecutionArtifact,
    *,
    inventory_evidence: list[str],
    api_deployments: dict[str, Any] | None,
    api_log_payload: dict[str, Any] | None,
    prod_url: str | None,
    reachability: dict[str, Any] | None,
) -> None:
    deployments = list((api_deployments or {}).get("deployments") or [])
    failed_dep = select_failed_deployment(deployments)
    if not failed_dep and api_log_payload and isinstance(api_log_payload.get("deployment"), dict):
        failed_dep = api_log_payload["deployment"]
    last_prod = select_last_successful_production_deployment(deployments)

    artifact.evidence = []
    if isinstance(failed_dep, dict):
        artifact.operational_events.extend(operational_events_from_deployment(failed_dep))
    artifact.operational_events = sort_operational_events(artifact.operational_events)

    api_logs_limited = bool((api_log_payload or {}).get("api_limited")) and not (api_log_payload or {}).get(
        "log_lines"
    )
    log_evidence = evidence_from_log_payload(api_log_payload or {}) if api_log_payload else []

    failure_reason = str((failed_dep or {}).get("error_message") or "").strip()
    failure_reason_confidence = CONFIDENCE_CONFIRMED if failure_reason else CONFIDENCE_INSUFFICIENT
    if not failure_reason and failed_dep and str(failed_dep.get("state") or "").lower() in _FAILED_STATES:
        failure_reason_confidence = CONFIDENCE_LIKELY

    impact_summary, impact_confidence, prod_state = derive_production_impact(
        failed_dep=failed_dep if isinstance(failed_dep, dict) else None,
        last_prod=last_prod,
        reachability=reachability,
        prod_url=prod_url,
    )

    actionable = build_actionable_summary(
        failed_dep if isinstance(failed_dep, dict) else None,
        api_logs_limited=api_logs_limited,
    )
    next_checks = build_next_safe_checks(
        failed_dep=failed_dep if isinstance(failed_dep, dict) else None,
        last_prod=last_prod,
        api_logs_limited=api_logs_limited,
    )

    diagnosis_item = evidence_item(
        source=artifact.data_source or "vercel_api",
        type="diagnosis",
        confidence=failure_reason_confidence,
        message=actionable,
    )
    reach_ev = evidence_from_reachability(reachability) if reachability and reachability.get("url") else None

    groups = build_evidence_groups(
        failed_dep=failed_dep if isinstance(failed_dep, dict) else None,
        last_prod=last_prod,
        all_deployments=deployments,
        inventory_evidence=inventory_evidence,
        log_evidence=log_evidence,
        reachability_evidence=reach_ev,
        diagnosis_evidence=diagnosis_item,
        source=str(artifact.data_source or "vercel_api"),
    )

    artifact.evidence = (
        groups["primary"] + groups["supporting"] + groups["historical"] + groups["debug"]
    )
    artifact.confidence = failure_reason_confidence
    artifact.probable_root_cause = actionable
    artifact.diagnostic = {
        "primary_finding": build_primary_finding(failed_dep if isinstance(failed_dep, dict) else None),
        "production_impact_summary": impact_summary,
        "failure_reason_confidence": failure_reason_confidence,
        "production_impact_confidence": impact_confidence,
        "production_current_state": prod_state,
        "failed_deployment_target": str((failed_dep or {}).get("target") or "unknown"),
        "failed_deployment": deployment_summary(failed_dep if isinstance(failed_dep, dict) else None),
        "last_successful_production_deployment": deployment_summary(last_prod),
        "next_safe_checks": next_checks,
        "evidence_groups": {k: len(v) for k, v in groups.items()},
        "evidence_by_tier": groups,
    }
