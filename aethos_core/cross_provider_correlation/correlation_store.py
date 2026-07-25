# SPDX-License-Identifier: Apache-2.0
"""Session-scoped cross-provider evidence store."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.cross_provider_correlation.deployment_identity import DeploymentIdentity
from aethos_core.cross_provider_correlation.provider_identity import ProviderIdentity

_STORE: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _session_bucket(session_id: str) -> dict[str, Any]:
    key = (session_id or "default").strip() or "default"
    bucket = _STORE.setdefault(
        key,
        {
            "session_id": key,
            "updated_at": _now_iso(),
            "github": None,
            "vercel": None,
            "railway": None,
            "raw": {},
        },
    )
    return bucket


def publish_github_evidence(session_id: str, evidence: dict[str, Any]) -> ProviderIdentity | None:
    bucket = _session_bucket(session_id)
    repo = str(evidence.get("repository") or "")
    branch = str((evidence.get("branch") or {}).get("branch") or "")
    commits = list((evidence.get("commits") or {}).get("commits") or [])
    commit_sha = str(commits[0].get("sha") or "") if commits else str((evidence.get("branch") or {}).get("sha") or "")

    workflow = dict(evidence.get("workflow_diagnostic") or {})
    checks = dict(evidence.get("checks") or {})
    if workflow.get("latest_failed_run") or checks.get("failed_count"):
        status = "failed"
    elif workflow.get("ok") or checks.get("ok"):
        status = "passed"
    else:
        status = "unknown"

    identity = ProviderIdentity(
        provider="github",
        repo=repo,
        branch=branch,
        commit_sha=commit_sha,
        status=status,
        metadata={
            "workflow_diagnostic": workflow,
            "checks": checks,
            "published_at": _now_iso(),
        },
    )
    bucket["github"] = identity.to_dict()
    bucket["raw"]["github"] = evidence
    bucket["updated_at"] = _now_iso()
    return identity


def publish_vercel_evidence(session_id: str, evidence: dict[str, Any]) -> DeploymentIdentity | None:
    bucket = _session_bucket(session_id)
    latest = dict(evidence.get("latest_deployment") or evidence.get("failed_deployment") or {})
    failed = dict(evidence.get("failed_deployment") or {})
    details = dict((evidence.get("project") or {}).get("details") or {})
    status = str((failed or latest).get("state") or "unknown").lower()
    if status in {"ready", "completed"}:
        normalized = "ready"
    elif status in {"error", "failed", "canceled"}:
        normalized = "failed"
    else:
        normalized = status

    identity = DeploymentIdentity(
        provider="vercel",
        project=str(evidence.get("project_name") or details.get("name") or ""),
        deployment_id=str(latest.get("id") or failed.get("id") or ""),
        commit_sha=str(latest.get("commit") or failed.get("commit") or ""),
        branch=str(latest.get("branch") or failed.get("branch") or ""),
        domain=str(details.get("production_url") or ""),
        status=normalized,
        metadata={
            "repo_link": details.get("repo_link"),
            "build_analysis": evidence.get("build_analysis"),
            "runtime_analysis": evidence.get("runtime_analysis"),
            "domain_health": evidence.get("domain_health"),
            "published_at": _now_iso(),
        },
    )
    bucket["vercel"] = identity.to_dict()
    bucket["raw"]["vercel"] = evidence
    bucket["updated_at"] = _now_iso()
    return identity


def publish_railway_evidence(session_id: str, evidence: dict[str, Any]) -> DeploymentIdentity | None:
    bucket = _session_bucket(session_id)
    status = str(evidence.get("status") or evidence.get("health") or "unknown").lower()
    identity = DeploymentIdentity(
        provider="railway",
        project=str(evidence.get("project") or ""),
        service=str(evidence.get("service") or ""),
        environment=str(evidence.get("environment") or "production"),
        deployment_id=str(evidence.get("deployment_id") or ""),
        commit_sha=str(evidence.get("commit_sha") or evidence.get("commit") or ""),
        branch=str(evidence.get("branch") or ""),
        status=status,
        metadata={"published_at": _now_iso(), **{k: v for k, v in evidence.items() if k not in {"project", "service"}}},
    )
    bucket["railway"] = identity.to_dict()
    bucket["raw"]["railway"] = evidence
    bucket["updated_at"] = _now_iso()
    return identity


def publish_railway_health_rows(session_id: str) -> list[DeploymentIdentity]:
    published: list[DeploymentIdentity] = []
    try:
        from aethos_core.failed_service_investigation.failed_service_memory import get_failed_health_rows

        rows = get_failed_health_rows(session_id=session_id, provider="railway")
    except Exception:
        rows = []
    if not rows:
        return published
    row = rows[0]
    identity = publish_railway_evidence(
        session_id,
        {
            "project": row.get("project"),
            "service": row.get("service"),
            "environment": row.get("environment"),
            "status": row.get("status") or row.get("health"),
            "health": row.get("health"),
        },
    )
    if identity:
        published.append(identity)
    return published


def get_session_snapshot(session_id: str) -> dict[str, Any]:
    bucket = _session_bucket(session_id)
    return {
        "session_id": bucket["session_id"],
        "updated_at": bucket["updated_at"],
        "github": bucket.get("github"),
        "vercel": bucket.get("vercel"),
        "railway": bucket.get("railway"),
        "raw": dict(bucket.get("raw") or {}),
    }


def clear_store_for_tests() -> None:
    _STORE.clear()


def mission_control_correlation_state(session_id: str) -> dict[str, Any]:
    from aethos_core.cross_provider_correlation.correlation_runtime import build_correlation_state

    return build_correlation_state(session_id=session_id)
