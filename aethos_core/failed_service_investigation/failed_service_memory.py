# SPDX-License-Identifier: Apache-2.0
"""Access last provider-wide health report for failed-service investigation."""

from __future__ import annotations

from typing import Any

from aethos_core.response_composition.operational_result_store import find_latest_provider_wide_health
from aethos_core.response_composition.render_pipeline.filter_engine import (
    canonical_failed_rows,
    canonical_unknown_rows,
    is_failed_row,
)


def _health_result(*, session_id: str = "default", provider: str = "railway"):
    return find_latest_provider_wide_health(session_id=session_id, provider=provider)


def get_health_report_rows(*, session_id: str = "default", provider: str = "railway") -> list[dict[str, Any]]:
    result = _health_result(session_id=session_id, provider=provider)
    if result is None:
        return []
    payload = result.result_payload
    return list(payload.get("services") or [])


def get_failed_health_rows(*, session_id: str = "default", provider: str = "railway") -> list[dict[str, Any]]:
    result = _health_result(session_id=session_id, provider=provider)
    if result is None:
        return []
    payload = result.result_payload
    return canonical_failed_rows(payload)


def get_unknown_health_rows(*, session_id: str = "default", provider: str = "railway") -> list[dict[str, Any]]:
    result = _health_result(session_id=session_id, provider=provider)
    if result is None:
        return []
    payload = result.result_payload
    failed = canonical_failed_rows(payload)
    return canonical_unknown_rows(payload, failed_rows=failed)


def get_preemptible_health_rows(*, session_id: str = "default", provider: str = "railway") -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in get_failed_health_rows(session_id=session_id, provider=provider):
        rows[row_key(row)] = row
    for row in get_unknown_health_rows(session_id=session_id, provider=provider):
        rows[row_key(row)] = row
    return list(rows.values())


def get_health_report_meta(*, session_id: str = "default") -> dict[str, Any]:
    result = _health_result(session_id=session_id)
    if result is None:
        return {"has_report": False}
    return {
        "has_report": True,
        "provider": result.provider,
        "scope": result.scope,
        "result_timestamp": result.result_timestamp,
        "summary": dict(result.summary or {}),
        "resolved_session_id": session_id,
    }


def row_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("project") or ""),
            str(row.get("environment") or ""),
            str(row.get("service") or ""),
        ]
    )
