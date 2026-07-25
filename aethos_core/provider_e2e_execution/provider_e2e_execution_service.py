# SPDX-License-Identifier: Apache-2.0
"""Route provider deploy + env + verify to E2E orchestration (preflight or missing config)."""

from __future__ import annotations

from aethos_core.config import get_settings
from aethos_core.provider_e2e_execution.provider_e2e_execution_intent import (
    detect_provider_e2e_kind,
    is_provider_e2e_execution_intent,
)


def route_provider_e2e_execution(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not get_settings().provider_e2e_orchestration_enabled:
        return None
    if not is_provider_e2e_execution_intent(text):
        return None
    provider = detect_provider_e2e_kind(text)
    if provider == "railway":
        from aethos_core.provider_e2e_execution.railway_e2e_execution import route_railway_e2e_execution

        return route_railway_e2e_execution(text, session_id=session_id)
    if provider == "vercel":
        from aethos_core.provider_e2e_execution.vercel_e2e_execution import route_vercel_e2e_execution

        return route_vercel_e2e_execution(text, session_id=session_id)
    return None
