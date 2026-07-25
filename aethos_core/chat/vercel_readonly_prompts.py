# SPDX-License-Identifier: Apache-2.0
"""Chat routing for Vercel read-only inspection and mutating-request blocks."""

from __future__ import annotations

from aethos_core.connections.adapters import auth_method_label
from aethos_core.runtime.authority import authority
from aethos_core.runtime.browser_capability import get_browser_capability_status
from aethos_core.runtime.vercel_readonly_jobs import (
    infer_vercel_mutating_intent,
    infer_vercel_readonly_job,
    mutating_request_blocked_reply,
    resolve_vercel_auth_for_chat,
    saved_vercel_profile_auth_for_chat,
    vercel_connect_required_reply,
    vercel_readonly_needs_session_reply,
    vercel_readonly_profile_not_persistent_reply,
    vercel_readonly_session_expired_reply,
)


def create_vercel_mutating_blocked_reply() -> tuple[str, str, dict[str, str]]:
    return mutating_request_blocked_reply(), "vercel_mutation_blocked", {}


def create_vercel_readonly_job_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.provider_read_intent import is_provider_read_inventory_request

    if is_provider_read_inventory_request(text):
        return None

    from aethos_core.conversation.provider_memory.active_provider_context import (
        block_vercel_inspection_for_active_context,
        compose_ambiguous_health_clarification_reply,
    )
    from aethos_core.chat.route_trace import is_internal_diagnostics_query
    from aethos_core.chat.operational_master_router import master_router_has_priority_route

    if is_internal_diagnostics_query(text):
        return None

    if master_router_has_priority_route(text, session_id=session_id):
        return None

    if block_vercel_inspection_for_active_context(text, session_id=session_id):
        return None
    ambiguous = compose_ambiguous_health_clarification_reply(text, session_id=session_id)
    if ambiguous is not None:
        return ambiguous

    from aethos_core.operational_target_resolution.explicit_target_resolver import (
        should_route_explicit_provider_diagnostics,
    )
    from aethos_core.provider_readonly_intent.readonly_provider_router import compose_readonly_provider_route_reply

    if should_route_explicit_provider_diagnostics(text, session_id=session_id):
        routed = compose_readonly_provider_route_reply(text, session_id=session_id)
        if routed is not None:
            body, intent, meta = routed
            meta = {**meta, "vercel_readonly_sync_diagnostics": "true"}
            return body, intent, meta

    inferred = infer_vercel_readonly_job(text)
    if inferred is None:
        return None

    auth = resolve_vercel_auth_for_chat()
    auth_method = auth.get("auth_method")
    credential_id = auth.get("credential_id")
    profile_id = auth.get("profile_id")
    block = auth.get("block_reason")

    if auth_method == "api_token" and credential_id:
        title, job_type, params = inferred
        params = {
            **params,
            "auth_method": "api_token",
            "auth_method_label": auth_method_label("api_token"),
            "credential_id": credential_id,
            "browser_used": False,
            "provider_used": "none",
        }
        job = authority.create_job(
            title=title,
            job_type=job_type,
            params=params,
            source="chat",
            session_id=session_id,
            auto_run=True,
        )
        body = (
            f"Created tracked job `{job.id}` to inspect Vercel using your **saved API token** "
            f"(`{credential_id}`).\n\n"
            f"**Type:** {job_type} · **read-only** · **auth:** API token\n\n"
            "Summary will appear here; the full report is in **Mission Control → Runtime → Tracked Work**."
        )
        return (
            body,
            "vercel_readonly_job_created",
            {
                "proposed_job_id": job.id,
                "proposed_job_type": job.job_type,
                "credential_id": credential_id,
                "auth_method": "api_token",
            },
        )

    status = get_browser_capability_status(probe_launch=False)
    if not status["enabled"]:
        saved = saved_vercel_profile_auth_for_chat()
        if saved and saved.get("authorization_status") == "saved":
            return (
                "**Browser automation is off**, but your saved Vercel session is still on disk.\n\n"
                "Enable `BROWSER_AUTOMATION_ENABLED=true` and restart the API to run read-only inspection "
                "without logging in again — or add a **Vercel API token** in Mission Control → Advanced settings → Credentials.",
                "vercel_readonly_unavailable",
                {"profile_id": str(saved.get("profile_id") or "")},
            )
        return (
            "**Browser automation is off** and no Vercel API token is configured.\n\n"
            "Add an API token in **Mission Control → Advanced settings → Credentials**, or enable "
            "`BROWSER_AUTOMATION_ENABLED=true` for saved browser sessions.",
            "vercel_readonly_unavailable",
            {},
        )

    if block == "expired":
        return vercel_readonly_session_expired_reply(), "vercel_readonly_session_expired", {}
    if block == "not_persistent":
        return vercel_readonly_profile_not_persistent_reply(), "vercel_readonly_not_persistent", {}
    if block == "missing" or not profile_id:
        return vercel_connect_required_reply(), "vercel_readonly_needs_session", {}

    title, job_type, params = inferred
    params = {
        **params,
        "auth_method": "browser",
        "auth_method_label": auth_method_label("browser"),
        "profile_id": profile_id,
        "browser_used": True,
        "provider_used": "none",
    }
    job = authority.create_job(
        title=title,
        job_type=job_type,
        params=params,
        source="chat",
        session_id=session_id,
        auto_run=True,
    )
    body = (
        f"Created tracked job `{job.id}` to inspect Vercel using your **approved saved session** "
        f"(`{profile_id}`).\n\n"
        f"**Type:** {job_type} · **read-only** · **auth:** browser session\n\n"
        "Summary will appear here; the full report is in **Mission Control → Runtime → Tracked Work**."
    )
    return (
        body,
        "vercel_readonly_job_created",
        {
            "proposed_job_id": job.id,
            "proposed_job_type": job.job_type,
            "profile_id": profile_id,
            "auth_method": "browser",
        },
    )
