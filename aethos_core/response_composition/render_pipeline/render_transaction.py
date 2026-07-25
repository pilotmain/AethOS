# SPDX-License-Identifier: Apache-2.0
"""Render transaction orchestration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from aethos_core.response_composition.conversational_renderer import render_provider_wide_health
from aethos_core.response_composition.final_response_validator import (
    JSON_VALIDATION_FAILURE,
    finalize_operational_response,
    validate_final_response,
)
from aethos_core.response_composition.render_pipeline.immutable_result_snapshot import ImmutableResultSnapshot
from aethos_core.response_composition.render_pipeline.render_guard import guarded_render
from aethos_core.response_composition.render_pipeline.render_validation import RenderValidationError
from aethos_core.response_composition.render_pipeline.response_transformer import transform_snapshot

FilterMode = Literal["all", "failed", "unknown"]

_TRANSACTIONS: list[dict[str, Any]] = []


@dataclass
class RenderTransaction:
    render_id: str
    source_payload_hash: str
    renderer: str
    filters: dict[str, str]
    started_at: str
    completed_at: str = ""
    validation_status: str = "pending"
    output: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


def get_render_transactions() -> list[dict[str, Any]]:
    return list(_TRANSACTIONS)


def clear_render_transactions_for_tests() -> None:
    _TRANSACTIONS.clear()


def execute_render_pipeline(
    *,
    payload: dict[str, Any],
    output_format: str,
    filter_mode: FilterMode = "all",
    intro: str = "",
    from_cache: bool = False,
    operation_type: str = "provider_wide_health",
    render_metadata: dict[str, Any] | None = None,
) -> tuple[str, RenderTransaction]:
    snapshot = ImmutableResultSnapshot.freeze(payload)
    transformed = transform_snapshot(snapshot, filter_mode=filter_mode)
    render_snapshot = ImmutableResultSnapshot.freeze(transformed)
    started_at = datetime.now(UTC).isoformat()
    render_id = str(uuid.uuid4())

    validation_status = "skipped"
    renderer_name = "unsupported"
    try:
        if operation_type == "provider_wide_health":
            body = guarded_render(
                render_provider_wide_health,
                render_snapshot.view(),
                payload_hash=render_snapshot.payload_hash,
                output_format=output_format,
                intro=intro,
                from_cache=from_cache,
                metadata=render_metadata,
            )
            renderer_name = f"provider_wide_health:{output_format}"
        else:
            body = f"Result available for `{operation_type}`, but no renderer is registered yet."
    except RenderValidationError as exc:
        validation_status = f"failed:{exc}"
        body = (
            "Structured render failed: filtered failed services could not be rendered reliably.\n\n"
            f"Reason: {exc}\n\n"
            "Retry with **show all** or rerun the provider-wide health check."
        )
        renderer_name = f"provider_wide_health:{output_format}"

    if output_format == "json" and not validation_status.startswith("failed:"):
        boundary = validate_final_response(body, output_format="json")
        if not boundary.ok:
            validation_status = f"failed:{boundary.error}"
            body = JSON_VALIDATION_FAILURE
        else:
            validation_status = "passed"

    body = finalize_operational_response(body, output_format=output_format)

    completed_at = datetime.now(UTC).isoformat()
    tx = RenderTransaction(
        render_id=render_id,
        source_payload_hash=snapshot.payload_hash,
        renderer=renderer_name,
        filters={"mode": filter_mode},
        started_at=started_at,
        completed_at=completed_at,
        validation_status=validation_status,
        output=body,
        meta={"output_format": output_format, "from_cache": from_cache},
    )
    _TRANSACTIONS.append(
        {
            "render_id": tx.render_id,
            "source_payload_hash": tx.source_payload_hash,
            "renderer": tx.renderer,
            "filters": dict(tx.filters),
            "started_at": tx.started_at,
            "completed_at": tx.completed_at,
            "validation_status": tx.validation_status,
        }
    )
    return body, tx
