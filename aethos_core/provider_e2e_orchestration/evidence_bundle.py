# SPDX-License-Identifier: Apache-2.0
"""Evidence bundle for provider E2E orchestration."""

from __future__ import annotations

from typing import Any


def build_provider_e2e_evidence_bundle(
    *,
    preflight_job_id: str,
    approval_id: str,
    provider: str,
    env_report: dict[str, Any],
    redeploy_report: dict[str, Any],
    poll_report: dict[str, Any],
    health_report: dict[str, Any],
    model_snapshot: dict[str, Any],
) -> dict[str, Any]:
    return {
        "preflight_job_id": preflight_job_id,
        "approval_id": approval_id,
        "provider": provider,
        "env_var_names": list(env_report.get("applied_names") or []) + list(env_report.get("failed_names") or []),
        "env_applied_names": list(env_report.get("applied_names") or []),
        "env_failed_names": list(env_report.get("failed_names") or []),
        "deployment_id": redeploy_report.get("deployment_id") or poll_report.get("deployment_id"),
        "deployment_url": poll_report.get("deployment_url") or health_report.get("url"),
        "status_timeline": list(poll_report.get("timeline") or []),
        "final_poll_state": poll_report.get("final_state"),
        "verification": {
            "ok": health_report.get("ok"),
            "url": health_report.get("url"),
            "status_code": health_report.get("status_code"),
            "detail": health_report.get("detail"),
        },
        "errors": _collect_errors(env_report, redeploy_report, poll_report, health_report),
        "target": {
            "project_name": model_snapshot.get("project_name"),
            "service_name": model_snapshot.get("service_name"),
            "environment": model_snapshot.get("environment"),
        },
    }


def _collect_errors(*reports: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for report in reports:
        if not report.get("ok") and report.get("detail"):
            errors.append(str(report["detail"]))
        for err in report.get("errors") or []:
            errors.append(str(err))
    return errors[:12]
