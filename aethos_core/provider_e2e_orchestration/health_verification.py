# SPDX-License-Identifier: Apache-2.0
"""Health verification for provider E2E orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_e2e_orchestration.job_model import ProviderE2EJobModel


def verify_health(
    model: ProviderE2EJobModel,
    *,
    deployment_url: str | None,
    poll_report: dict[str, Any],
) -> dict[str, Any]:
    url = (model.health_check_url or deployment_url or poll_report.get("deployment_url") or "").strip()
    if not url:
        return {
            "ok": True,
            "skipped": True,
            "detail": "No deployment URL available for health verification.",
        }
    if not url.startswith("http"):
        url = f"https://{url}"

    from aethos_core.operations.execution.execution_runner import _url_reachability

    reach = _url_reachability(url)
    status_code = reach.get("status_code")
    ok = bool(reach.get("reachable")) and (status_code is None or int(status_code) < 500)
    return {
        "ok": ok,
        "url": url,
        "status_code": status_code,
        "reachable": reach.get("reachable"),
        "detail": str(reach.get("summary") or ""),
        "expected_range": "2xx-4xx (5xx fails)",
    }
