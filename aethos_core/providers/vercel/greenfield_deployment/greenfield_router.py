# SPDX-License-Identifier: Apache-2.0
"""Chat router for Vercel greenfield deployment."""

from __future__ import annotations

import logging

from aethos_core.providers.vercel.greenfield_deployment.greenfield_flow import run_vercel_greenfield_deployment_flow
from aethos_core.providers.vercel.greenfield_deployment.greenfield_intent import is_vercel_greenfield_deployment_intent
from aethos_core.security.secret_redaction import redact_text

_log = logging.getLogger(__name__)


def route_vercel_greenfield_deployment_flow(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_vercel_greenfield_deployment_intent(text):
        return None
    try:
        result = run_vercel_greenfield_deployment_flow(text, session_id=session_id)
    except Exception as exc:
        _log.exception("Vercel greenfield deployment flow failed safely")
        detail = redact_text(str(exc))
        return (
            f"Vercel greenfield deployment blocked: {detail}",
            "vercel_greenfield_deployment_blocked",
            {
                "route_id": "vercel_greenfield_deployment_flow",
                "intent": "vercel_greenfield_deployment_blocked",
                "session_id": session_id,
            },
        )
    meta = {
        "route_id": "vercel_greenfield_deployment_flow",
        "intent": result.intent,
        "session_id": session_id,
        "flow": "vercel_greenfield_deployment",
        "readonly": "true" if result.blocked else "false",
        "preflight_created": "true" if result.preflight_job_id else "false",
    }
    if result.preflight_job_id:
        meta["job_id"] = result.preflight_job_id
    return result.reply, result.intent, meta
