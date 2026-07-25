# SPDX-License-Identifier: Apache-2.0
"""Semantic response composer — render structured operational results."""

from __future__ import annotations

from typing import Any

from aethos_core.response_composition.filtered_view_state import (
    record_filtered_view,
    set_active_filter_mode,
)
from aethos_core.response_composition.final_response_validator import finalize_operational_response
from aethos_core.response_composition.operational_result_store import (
    OperationalResult,
    get_latest_operational_result,
    record_render_history,
    save_operational_result,
)
from aethos_core.response_composition.render_pipeline.render_transaction import execute_render_pipeline
from aethos_core.response_composition.response_intent_classifier import classify_response_intent
from aethos_core.response_composition.summary_renderer import render_fix_priority


def compose_from_result(
    result: OperationalResult,
    *,
    output_format: str = "conversational",
    filter_mode: str | None = None,
    intro: str = "",
    from_cache: bool = False,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]]:
    mode = filter_mode or str(result.filters.get("mode") or "all")

    if result.operation_type == "provider_wide_health":
        body, tx = execute_render_pipeline(
            payload=result.result_payload,
            output_format=output_format,
            filter_mode=mode,  # type: ignore[arg-type]
            intro=intro,
            from_cache=from_cache,
            operation_type=result.operation_type,
            render_metadata={
                "provider": result.provider,
                "scope": result.scope,
                "refreshed": not from_cache,
            },
        )
    else:
        body = f"Result available for `{result.operation_type}`, but no renderer is registered yet."
        tx = None

    body = finalize_operational_response(body, output_format=output_format)

    intent = f"operational_response_{output_format}"
    meta = {
        "provider": result.provider,
        "scope": result.scope,
        "output_format": output_format,
        "filter_mode": mode,
        "from_cache": "true" if from_cache else "false",
        "operation_type": result.operation_type,
    }
    if tx is not None:
        meta["render_id"] = tx.render_id
        meta["validation_status"] = tx.validation_status
    record_filtered_view(session_id=session_id, filter_mode=mode, output_format=output_format)
    record_render_history(session_id=session_id, output_format=output_format, filter_mode=mode)
    return body, intent, meta


def try_compose_rerender_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = classify_response_intent(text, session_id=session_id)

    if intent.kind == "new_operation":
        return None

    cached = get_latest_operational_result(session_id=session_id)
    if cached is not None and cached.scope == "named_service_health":
        from aethos_core.operational_planner.scope_classifier import is_provider_wide_phrase

        if is_provider_wide_phrase(text):
            return None

    if intent.kind == "fix_priority":
        result = get_latest_operational_result(session_id=session_id)
        if result is None:
            return _missing_result_reply(session_id)
        from aethos_core.response_composition.render_pipeline.filter_engine import (
            canonical_failed_rows,
            canonical_unknown_rows,
        )

        payload = result.result_payload
        failed = canonical_failed_rows(payload)
        unknown = canonical_unknown_rows(payload, failed_rows=failed)
        body = (
            "Using the last provider-wide health report (no refresh).\n\n"
            + render_fix_priority(failed, unknown)
        )
        record_render_history(session_id=session_id, output_format="fix_priority", filter_mode="all")
        return body, "operational_response_fix_priority", {"from_cache": "true", "provider": result.provider}

    if intent.kind == "filter":
        result = get_latest_operational_result(session_id=session_id)
        if result is None:
            return _missing_result_reply(session_id)
        set_active_filter_mode(session_id=session_id, filter_mode=intent.filter_mode)
        result = get_latest_operational_result(session_id=session_id)
        assert result is not None
        return compose_from_result(
            result,
            output_format=intent.output_format if intent.output_format != "conversational" else "conversational",
            filter_mode=intent.filter_mode,
            intro="Using the last provider-wide health report (no refresh).",
            from_cache=True,
            session_id=session_id,
        )

    if intent.kind == "rerender":
        result = get_latest_operational_result(session_id=session_id)
        if result is None:
            return _missing_result_reply(session_id)
        mode = str(result.filters.get("mode") or "all")
        if result.operation_type == "provider_inventory":
            from aethos_core.chat.provider_read_intent import _compose_inventory_body

            inventory = dict(result.result_payload.get("inventory") or {})
            body = _compose_inventory_body(
                result.provider,
                inventory,
                output_format=intent.output_format,
                intro="Re-rendering the last provider inventory (no refresh).",
            )
            meta = {
                "provider": result.provider,
                "scope": result.scope,
                "output_format": intent.output_format,
                "filter_mode": mode,
                "from_cache": "true",
                "operation_type": result.operation_type,
            }
            record_render_history(session_id=session_id, output_format=intent.output_format, filter_mode=mode)
            return body, f"operational_response_{intent.output_format}", meta
        return compose_from_result(
            result,
            output_format=intent.output_format,
            filter_mode=mode,
            intro="Re-rendering the last operational result (no refresh).",
            from_cache=True,
            session_id=session_id,
        )

    return None


def store_provider_inventory_result(
    *,
    session_id: str,
    provider: str,
    payload: dict[str, Any],
    summary: dict[str, Any],
    scope: str = "provider_inventory",
    meta: dict[str, Any] | None = None,
) -> OperationalResult:
    result = OperationalResult(
        operation_type="provider_inventory",
        provider=provider,
        scope=scope,
        result_payload=payload,
        result_timestamp=__import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
        summary=summary,
        filters={"mode": "all"},
        meta=dict(meta or {}),
    )
    save_operational_result(session_id=session_id, result=result)
    return result


def store_provider_wide_health_result(
    *,
    session_id: str,
    provider: str,
    payload: dict[str, Any],
    summary: dict[str, Any],
    scope: str = "provider_wide",
    meta: dict[str, Any] | None = None,
) -> OperationalResult:
    result = OperationalResult(
        operation_type="provider_wide_health",
        provider=provider,
        scope=scope,
        result_payload=payload,
        result_timestamp=__import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
        summary=summary,
        filters={"mode": "all"},
        meta=dict(meta or {}),
    )
    save_operational_result(session_id=session_id, result=result)
    return result


def compose_operational_response(
    result: OperationalResult,
    *,
    output_format: str = "conversational",
    filter_mode: str = "all",
    intro: str = "",
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]]:
    set_active_filter_mode(session_id=session_id, filter_mode=filter_mode)
    result = get_latest_operational_result(session_id=session_id)
    assert result is not None
    return compose_from_result(
        result,
        output_format=output_format,
        filter_mode=filter_mode,
        intro=intro,
        from_cache=False,
        session_id=session_id,
    )


def _missing_result_reply(session_id: str) -> tuple[str, str, dict[str, str]]:
    _ = session_id
    body = (
        "I don't have a recent operational result to re-render in this session.\n\n"
        "Run the operation first (for example: **check all services in railway**), "
        "then ask for **table format**, **json**, or **summary only** without rerunning it."
    )
    return body, "operational_response_missing_result", {"from_cache": "false"}
