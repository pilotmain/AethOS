# SPDX-License-Identifier: Apache-2.0
"""Cross-provider correlation API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(tags=["cross-provider-correlation"])


@router.get("/correlation/state")
def correlation_state_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.cross_provider_correlation.correlation_store import mission_control_correlation_state

    return mission_control_correlation_state(session_id=session_id)
