# SPDX-License-Identifier: Apache-2.0
"""Chat routing for governed browser evidence capture."""

from __future__ import annotations

from aethos_core.browser.runtime.browser_evidence_intents import infer_browser_evidence_job
from aethos_core.runtime.authority import authority


def create_browser_evidence_job_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.route_trace import is_internal_diagnostics_query
    from aethos_core.chat.operational_master_router import master_router_has_priority_route

    if is_internal_diagnostics_query(text):
        return None

    if master_router_has_priority_route(text, session_id=session_id):
        return None

    inferred = infer_browser_evidence_job(text)
    if inferred is None:
        return None
    job_type, params = inferred
    params = {**params, "session_id": session_id}
    title = "Browser evidence capture" if job_type == "browser_capture_execution" else "Browser evidence index"
    job = authority.create_job(
        title=title,
        job_type=job_type,
        params=params,
        source="chat",
        session_id=session_id,
        auto_run=True,
    )
    if params.get("blocked_request"):
        body = (
            f"Created browser policy review job `{job.id}`.\n\n"
            "**Status:** blocked interaction detected — governed policy will record denial, not execute clicks."
        )
    elif not params.get("target_url") and job_type == "browser_capture_execution":
        body = (
            f"Created browser capture job `{job.id}`.\n\n"
            "**Status:** needs URL — include a domain like `useinvoicepilot.com`."
        )
    else:
        body = (
            f"Created browser evidence job `{job.id}`.\n\n"
            f"**Capture:** {params.get('capture_type', 'screenshot')} · "
            f"**Target:** {params.get('target_url') or 'index'}\n\n"
            "Evidence will be stored under `data/browser_artifacts/` and visible in Mission Control → Browser."
        )
    return (
        body,
        "browser_evidence_job_created",
        {
            "proposed_job_id": job.id,
            "proposed_job_type": job_type,
            "capture_type": str(params.get("capture_type") or ""),
        },
    )
