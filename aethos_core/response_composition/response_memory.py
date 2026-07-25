# SPDX-License-Identifier: Apache-2.0
"""Session response memory — last format preferences and result reference."""

from __future__ import annotations

from typing import Any

from aethos_core.response_composition.operational_result_store import get_latest_operational_result


def get_response_context(*, session_id: str = "default") -> dict[str, Any]:
    result = get_latest_operational_result(session_id=session_id)
    if result is None:
        return {"has_result": False}
    last_render = result.render_history[-1] if result.render_history else {}
    return {
        "has_result": True,
        "operation_type": result.operation_type,
        "provider": result.provider,
        "scope": result.scope,
        "last_output_format": last_render.get("output_format"),
        "last_filter_mode": last_render.get("filter_mode") or result.filters.get("mode", "all"),
        "result_timestamp": result.result_timestamp,
        "render_history": list(result.render_history),
    }
