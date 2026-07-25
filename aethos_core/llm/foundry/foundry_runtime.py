# SPDX-License-Identifier: Apache-2.0
"""Model Foundry — hardware probe and fit scoring (§B4)."""

from __future__ import annotations

from typing import Any

from aethos_core.workspace_suite.model_foundry import (
    create_serve_preflight,
    recommend_models,
    scan_hardware,
)


def probe_hardware() -> dict[str, Any]:
    return scan_hardware()


def score_model_fit(model_id: str) -> dict[str, Any]:
    snap = scan_hardware()
    recs = recommend_models()
    rows = recs.get("models") or recs.get("recommendations") or []
    for row in rows:
        if isinstance(row, dict) and str(row.get("id") or "") == model_id:
            return {"ok": True, "model_id": model_id, "fit": row, "hardware": snap}
    return {"ok": False, "error": "model_not_in_catalog", "model_id": model_id}


def propose_serve(model_id: str, *, port: int = 11434) -> dict[str, Any]:
    return create_serve_preflight(model_id=model_id, port=port)
