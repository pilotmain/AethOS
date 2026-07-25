# SPDX-License-Identifier: Apache-2.0
"""Filtered view state — separate from immutable source payload."""

from __future__ import annotations

from typing import Any

from aethos_core.response_composition.operational_result_store import (
    OperationalResult,
    get_latest_operational_result,
    save_operational_result,
)


def get_active_filter_mode(*, session_id: str = "default") -> str:
    result = get_latest_operational_result(session_id=session_id)
    if result is None:
        return "all"
    return str(result.filters.get("mode") or "all")


def set_active_filter_mode(*, session_id: str, filter_mode: str) -> OperationalResult | None:
    result = get_latest_operational_result(session_id=session_id)
    if result is None:
        return None
    result.filters = {"mode": filter_mode}
    save_operational_result(session_id=session_id, result=result)
    return result


def record_filtered_view(
    *,
    session_id: str,
    filter_mode: str,
    output_format: str,
) -> None:
    result = get_latest_operational_result(session_id=session_id)
    if result is None:
        return
    meta = dict(result.meta or {})
    meta["last_filtered_view"] = {
        "filter_mode": filter_mode,
        "output_format": output_format,
    }
    result.meta = meta
    save_operational_result(session_id=session_id, result=result)


def get_source_payload(*, session_id: str = "default") -> dict[str, Any] | None:
    result = get_latest_operational_result(session_id=session_id)
    if result is None:
        return None
    return dict(result.result_payload)
