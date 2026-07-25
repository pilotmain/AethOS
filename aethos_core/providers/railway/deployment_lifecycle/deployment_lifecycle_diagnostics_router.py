# SPDX-License-Identifier: Apache-2.0
"""Route Railway deployment lifecycle diagnostics and repair prompts."""

from __future__ import annotations

import re

_DIAGNOSTICS_RX = re.compile(
    r"\b(?:debug|show)\s+railway\s+deployment\s+lifecycle\b",
    re.I,
)
_REPAIR_RX = re.compile(
    r"\brepair\s+railway\s+deployment\s+lifecycle\b",
    re.I,
)
_CLEAR_STALE_RX = re.compile(
    r"\bclear\s+stale\s+railway\s+lifecycle\s+index\b",
    re.I,
)


def is_railway_deployment_lifecycle_diagnostics_intent(text: str) -> bool:
    return bool(_DIAGNOSTICS_RX.search((text or "").strip()))


def is_railway_deployment_lifecycle_repair_intent(text: str) -> bool:
    return bool(_REPAIR_RX.search((text or "").strip()))


def route_railway_deployment_lifecycle_diagnostics(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if _CLEAR_STALE_RX.search(raw):
        from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
            clear_stale_global_lifecycle_index,
        )

        result = clear_stale_global_lifecycle_index()
        if result.get("cleared"):
            body = "\n".join(
                [
                    "Cleared stale Railway global lifecycle index.",
                    "",
                    f"Removed index entries: **{result.get('removed_entries', 0)}**",
                    "",
                    "Recreate lifecycle with deployment plan commands when ready.",
                    "",
                    "No mutation has been performed.",
                ]
            )
            intent = "railway_deployment_lifecycle_index_cleared"
        else:
            body = "No global lifecycle index was cleared (index missing)."
            intent = "railway_deployment_lifecycle_index_clear_skipped"
        return body, intent, _meta(session_id, stage="clear_stale_index")

    if is_railway_deployment_lifecycle_repair_intent(raw):
        from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_repair import (
            format_lifecycle_repair_report,
            repair_railway_deployment_lifecycle,
        )

        result = repair_railway_deployment_lifecycle(session_id=session_id)
        body = format_lifecycle_repair_report(result)
        intent = (
            "railway_deployment_lifecycle_repair"
            if result.get("ok")
            else "railway_deployment_lifecycle_repair_failed"
        )
        return body, intent, _meta(session_id, stage="repair", repaired=str(result.get("ok")).lower())

    if not is_railway_deployment_lifecycle_diagnostics_intent(raw):
        return None

    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_diagnostics import (
        format_lifecycle_diagnostics_report,
        trace_railway_deployment_lifecycle_resolution,
    )

    trace = trace_railway_deployment_lifecycle_resolution(session_id=session_id, user_text=raw)
    body = format_lifecycle_diagnostics_report(trace)
    return body, "railway_deployment_lifecycle_diagnostics", _meta(
        session_id,
        stage="diagnostics",
        hydrated=str(trace.get("hydrated")).lower(),
        source=str(trace.get("source") or "none"),
    )


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    meta = {
        "route_id": "railway_deployment_lifecycle_diagnostics",
        "matched_module": "providers.railway.deployment_lifecycle.deployment_lifecycle_diagnostics_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "lifecycle_diagnostics_stage": stage,
    }
    meta.update(extra)
    return meta
