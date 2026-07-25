# SPDX-License-Identifier: Apache-2.0
"""Session cache for the last provider-wide health report."""

from __future__ import annotations

from typing import Any

from aethos_core.response_composition.operational_result_store import (
    clear_operational_results_for_tests,
    get_latest_operational_result,
)
from aethos_core.response_composition.response_composer import store_provider_wide_health_result


def _legacy_from_operational_result(result) -> dict[str, Any]:
    payload = result.result_payload
    services = list(payload.get("services") or [])
    counts = dict(payload.get("counts") or result.summary or {})
    return {
        "provider": result.provider,
        "rows": services,
        "summary": counts,
        "fetched_at": result.result_timestamp,
    }


def save_provider_wide_health_report(
    *,
    session_id: str,
    provider: str,
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    session_id = (session_id or "default").strip()
    payload = {
        "services": list(rows),
        "counts": dict(summary),
        "failures": [row for row in rows if row.get("health") == "failed" or row.get("status") == "failed"],
        "unknown": [
            row
            for row in rows
            if row.get("health") == "unknown"
            or row.get("status") in {"unknown", "deploying"}
        ],
    }
    result = store_provider_wide_health_result(
        session_id=session_id,
        provider=provider,
        payload=payload,
        summary=dict(summary),
        scope="provider_wide",
    )
    return _legacy_from_operational_result(result)


def get_provider_wide_health_report(*, session_id: str, provider: str = "railway") -> dict[str, Any] | None:
    session_id = (session_id or "default").strip()
    result = get_latest_operational_result(session_id=session_id)
    if result is None or result.operation_type != "provider_wide_health":
        return None
    if str(result.provider or "") != provider:
        return None
    return _legacy_from_operational_result(result)


def clear_provider_wide_health_for_tests() -> None:
    clear_operational_results_for_tests()
