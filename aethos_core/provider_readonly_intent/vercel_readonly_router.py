# SPDX-License-Identifier: Apache-2.0
"""Vercel readonly inspection routing."""

from __future__ import annotations

import re

from aethos_core.provider_readonly_intent.readonly_intent_classifier import (
    ReadonlyProviderIntent,
    classify_vercel_readonly_intent,
)

_PROJECT_LIST_OPS = {"projects"}
_LIVE_DIAGNOSTIC_OPS = {
    "deployments",
    "logs",
    "domains",
    "env_metadata",
    "live_diagnosis",
    "failed_deployment",
}


def compose_vercel_readonly_route_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = classify_vercel_readonly_intent(text)
    if intent is None:
        return None

    if intent.operation in _PROJECT_LIST_OPS:
        return _route_vercel_inventory_job(text, session_id=session_id, intent=intent)

    from aethos_core.runtime.vercel_readonly_jobs import resolve_vercel_auth_for_chat

    auth = resolve_vercel_auth_for_chat()
    if auth.get("auth_method") != "api_token" or not auth.get("credential_id"):
        blocker = compose_vercel_readonly_blocker_reply(text, session_id=session_id, intent=intent)
        if blocker is not None:
            return blocker
        return _route_vercel_inventory_job(text, session_id=session_id, intent=intent)

    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    token = VercelAuthAdapter().get_api_token(str(auth["credential_id"]))
    if not token:
        return (
            "Vercel credentials are configured but the API token could not be loaded.\n\n"
            "Re-save the token in **Mission Control → Advanced settings → Credentials → Vercel**.",
            "vercel_readonly_needs_token",
            _vercel_meta(intent),
        )

    if intent.operation in _LIVE_DIAGNOSTIC_OPS:
        from aethos_core.operational_target_resolution.provider_intent_guard import (
            is_valid_vercel_project_hint,
            requires_vercel_in_text_for_readonly,
        )

        project = (intent.project or "").strip()
        if not requires_vercel_in_text_for_readonly(text, project_hint=project):
            return None
        if not project:
            return (
                "Which **Vercel project** should I inspect?\n\n"
                "Example: `check the error for killit in vercel` or `inspect Vercel deployments for invoicepilot`.",
                "vercel_readonly_needs_project",
                _vercel_meta(intent),
            )
        if not is_valid_vercel_project_hint(project):
            return (
                f"I couldn't treat `{project}` as a Vercel project name.\n\n"
                "Name the project explicitly (e.g. `killit`, `invoicepilot`).",
                "vercel_readonly_invalid_project",
                _vercel_meta(intent),
            )
        from aethos_core.providers.vercel.diagnostics.vercel_live_diagnostics import run_vercel_live_diagnostics

        body, meta = run_vercel_live_diagnostics(
            token,
            project_name=project,
            session_id=session_id,
            operation=intent.operation,
        )
        if meta.get("project"):
            meta["project"] = project
        elif project:
            meta["project"] = project
        return body, f"vercel_readonly_{intent.operation}", meta

    return _route_vercel_inventory_job(text, session_id=session_id, intent=intent)


def compose_vercel_readonly_blocker_reply(
    text: str,
    *,
    session_id: str = "default",
    intent: ReadonlyProviderIntent | None = None,
) -> tuple[str, str, dict[str, str]] | None:
    intent = intent or classify_vercel_readonly_intent(text)
    if intent is None:
        return None

    from aethos_core.runtime.browser_capability import get_browser_capability_status
    from aethos_core.runtime.vercel_readonly_jobs import (
        resolve_vercel_auth_for_chat,
        saved_vercel_profile_auth_for_chat,
        vercel_connect_required_reply,
        vercel_readonly_needs_session_reply,
        vercel_readonly_profile_not_persistent_reply,
        vercel_readonly_session_expired_reply,
    )

    auth = resolve_vercel_auth_for_chat()
    status = get_browser_capability_status(probe_launch=False)
    blockers: list[str] = []

    if auth.get("auth_method") != "api_token" or not auth.get("credential_id"):
        blockers.append("VERCEL_API_TOKEN missing")
    if not status.get("execution_ready"):
        blockers.append(f"Playwright/browser runtime not ready ({status.get('execution_label') or 'blocked'})")
    try:
        from aethos_core.runtime.browser_runtime import browser_inventory_refresh_blocked_reason

        inv_blocked, inv_reason = browser_inventory_refresh_blocked_reason(probe_launch=False)
        if inv_blocked:
            blockers.append(f"Vercel inventory unavailable ({inv_reason})")
    except Exception:
        pass

    if auth.get("block_reason") == "expired":
        return (
            vercel_readonly_session_expired_reply(),
            "vercel_readonly_session_expired",
            _vercel_meta(intent),
        )
    if auth.get("block_reason") == "not_persistent":
        return (
            vercel_readonly_profile_not_persistent_reply(),
            "vercel_readonly_not_persistent",
            _vercel_meta(intent),
        )
    if auth.get("block_reason") == "missing" and not auth.get("credential_id"):
        saved = saved_vercel_profile_auth_for_chat()
        if saved and saved.get("authorization_status") == "saved" and not status.get("enabled"):
            blockers.append("browser automation is disabled (`BROWSER_AUTOMATION_ENABLED=false`)")

    if blockers:
        operation_label = intent.operation.replace("_", " ")
        lines = [
            f"I can inspect Vercel **{operation_label}**, but Vercel readonly execution is blocked.",
            "",
            "Blocked by:",
        ]
        for item in blockers:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "Next step:",
                "Add **VERCEL_API_TOKEN** or refresh the Vercel connection in Mission Control → Advanced settings → Credentials.",
                "",
                "No mutation has been performed.",
            ]
        )
        return "\n".join(lines), "vercel_readonly_blocked", _vercel_meta(intent, blocked="true")

    if auth.get("block_reason") == "missing":
        return vercel_connect_required_reply(), "vercel_readonly_needs_session", _vercel_meta(intent)
    return vercel_readonly_needs_session_reply(), "vercel_readonly_needs_session", _vercel_meta(intent)


def _route_vercel_inventory_job(
    text: str,
    *,
    session_id: str,
    intent: ReadonlyProviderIntent,
) -> tuple[str, str, dict[str, str]] | None:
    job_reply = _create_vercel_readonly_job(text, session_id=session_id, intent=intent)
    if job_reply is not None:
        return job_reply
    return compose_vercel_readonly_blocker_reply(text, session_id=session_id, intent=intent)


def _create_vercel_readonly_job(
    text: str,
    *,
    session_id: str,
    intent: ReadonlyProviderIntent,
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.vercel_readonly_prompts import create_vercel_readonly_job_reply

    enriched = _enrich_vercel_request(text, intent)
    job_reply = create_vercel_readonly_job_reply(enriched, session_id=session_id)
    if job_reply is None:
        return None
    body, reply_intent, meta = job_reply
    meta = {
        **meta,
        "route_id": "provider_readonly_intent",
        "matched_module": "provider_readonly_intent.vercel_readonly_router",
        "readonly_provider": "vercel",
        "readonly_operation": intent.operation,
    }
    if intent.project:
        meta["project"] = intent.project
    return body, reply_intent, meta


def _enrich_vercel_request(text: str, intent: ReadonlyProviderIntent) -> str:
    raw = (text or "").strip()
    if intent.operation == "deployments" and "deployment" in raw.lower():
        if not re.search(r"\b(status|summary)\b", raw, re.I):
            return f"{raw} deployment status summary"
    return raw


def _vercel_meta(intent: ReadonlyProviderIntent, **extra: str) -> dict[str, str]:
    meta = {
        "route_id": "provider_readonly_intent",
        "matched_module": "provider_readonly_intent.vercel_readonly_router",
        "readonly_provider": "vercel",
        "readonly_operation": intent.operation,
    }
    meta.update(extra)
    return meta
