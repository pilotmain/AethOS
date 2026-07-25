# SPDX-License-Identifier: Apache-2.0
"""Pure JSON renderer — atomic serialization, no conversational bleed."""

from __future__ import annotations

import json
from typing import Any

from aethos_core.response_composition.render_pipeline.structured_output_validator import validate_json_document


def build_json_export(payload: dict[str, Any], *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    filter_mode = str(payload.get("filter_mode") or "all")
    meta = {
        "provider": str((metadata or {}).get("provider") or "railway"),
        "scope": str((metadata or {}).get("scope") or "provider_wide"),
        "filter": filter_mode if filter_mode != "all" else "none",
        "refreshed": bool((metadata or {}).get("refreshed", False)),
    }
    return {
        "summary": dict(payload.get("counts") or {}),
        "services": list(payload.get("services") or []),
        "metadata": meta,
    }


def render_json_block(payload: dict[str, Any], *, metadata: dict[str, Any] | None = None) -> str:
    export = build_json_export(payload, metadata=metadata)
    validation = validate_json_document(export)
    if not validation.ok:
        raise ValueError(f"JSON document validation failed: {validation.error}")
    encoded = json.dumps(validation.parsed, indent=2, default=str)
    return f"```json\n{encoded}\n```"
