# SPDX-License-Identifier: Apache-2.0
"""Pure renderers — no filtering, mutation, or side effects."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from aethos_core.response_composition.json_renderer import render_json_block
from aethos_core.response_composition.render_pipeline.filter_engine import canonical_failed_rows, canonical_unknown_rows
from aethos_core.response_composition.render_pipeline.render_validation import RenderValidationError
from aethos_core.response_composition.summary_renderer import (
    render_failed_service_list,
    render_needs_attention,
    render_summary_block,
    render_unknown_service_list,
)
from aethos_core.response_composition.table_renderer import render_service_table


def _validate_failed_view(payload: dict[str, Any], failed_rows: list[dict[str, Any]]) -> None:
    counts = dict(payload.get("counts") or {})
    failed_count = int(counts.get("failed") or 0)
    filter_mode = str(payload.get("filter_mode") or "all")
    if filter_mode == "failed" and failed_count > 0 and not failed_rows:
        raise RenderValidationError(
            f"failed count is {failed_count} but canonical failed rows are empty"
        )


def render_provider_wide_health(
    *,
    payload: dict[str, Any],
    output_format: str,
    intro: str = "",
    from_cache: bool = False,
    metadata: dict[str, Any] | None = None,
) -> str:
    counts = dict(payload.get("counts") or {})
    services = list(payload.get("services") or [])
    filter_mode = str(payload.get("filter_mode") or "all")
    failed_rows = canonical_failed_rows(payload)
    unknown_rows = canonical_unknown_rows(payload, failed_rows=failed_rows)

    if filter_mode == "failed":
        _validate_failed_view(payload, failed_rows)

    if from_cache:
        header = intro or "Re-rendering the last provider-wide health report (no refresh)."
    else:
        header = intro or "I checked all Railway services."

    if output_format == "json":
        return f"{header}\n\n{render_json_block(payload, metadata=metadata)}"

    if output_format == "executive_summary" or output_format == "concise":
        lines = [header, ""] + render_summary_block(counts)
        if filter_mode == "all":
            lines.extend(render_needs_attention(failed_rows, unknown_rows))
        elif filter_mode == "failed":
            lines.extend(render_failed_service_list(failed_rows))
        return "\n".join(lines)

    if output_format == "table":
        lines = [header, ""]
        if filter_mode == "all":
            lines.extend(render_summary_block(counts))
            lines.append("")
        rows = failed_rows if filter_mode == "failed" and not services else services
        lines.append(render_service_table(rows))
        return "\n".join(lines)

    if output_format == "grouped":
        lines = [header, ""]
        lines.extend(render_summary_block(counts))
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        rows = failed_rows if filter_mode == "failed" and not services else services
        for row in rows:
            grouped[str(row.get("project") or "unknown")].append(row)
        for project, project_rows in sorted(grouped.items()):
            lines.extend(["", f"### {project}"])
            lines.append(render_service_table(project_rows))
        return "\n".join(lines)

    if output_format == "detailed" or output_format == "markdown":
        lines = [header, ""] + render_summary_block(counts)
        if filter_mode == "all":
            lines.extend(render_needs_attention(failed_rows, unknown_rows))
        elif filter_mode == "failed":
            lines.extend(render_failed_service_list(failed_rows))
        lines.extend(["", "Full inventory:", "", render_service_table(services if services else failed_rows)])
        return "\n".join(lines)

    # conversational default
    lines = [header, ""] + render_summary_block(counts)
    if filter_mode == "all":
        lines.extend(render_needs_attention(failed_rows, unknown_rows))
        lines.extend(["", "Full inventory:", "", render_service_table(services)])
    elif filter_mode == "failed":
        lines.extend(render_failed_service_list(failed_rows))
    elif filter_mode == "unknown":
        lines.extend(render_unknown_service_list(unknown_rows))
    return "\n".join(lines)
