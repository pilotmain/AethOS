# SPDX-License-Identifier: Apache-2.0
"""Chat routing for Railway read-only inventory and deployment diagnostics."""

from __future__ import annotations

import re

from aethos_core.connections.adapters import auth_method_label_for_provider
from aethos_core.runtime.railway_readonly_jobs import (
    infer_railway_readonly_job,
    railway_connect_required_reply,
    resolve_railway_auth_for_chat,
)

_RAILWAY_DEPLOY_ENV_RX = re.compile(
    r"\b(check|show|read|list|what(?:'s| is)|status)\b.*\b(railway)\b.*\b(deployment|deployments?|env|environment|config)\b"
    r"|\b(railway)\b.*\b(deployment|deployments?)\b.*\b(status|health)\b",
    re.I,
)


def is_railway_readonly_direct_request(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or not re.search(r"\brailway\b", raw, re.I):
        return False
    # "render/show a diff of the railway env … on the canvas" is a Canvas render, not a
    # Railway readonly status request — defer so the canvas lane handles it.
    from aethos_core.chat.front_door_intent import is_canvas_render_request

    if is_canvas_render_request(raw):
        return False
    from aethos_core.chat.explicit_mutation_intent import has_explicit_mutation_verb

    if has_explicit_mutation_verb(raw):
        return False
    if infer_railway_readonly_job(raw) is not None:
        return True
    return bool(_RAILWAY_DEPLOY_ENV_RX.search(raw))


def _execute_railway_readonly_direct(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.operational_session.active_subject_resolver import resolve_active_subject
    from aethos_core.operational_session.operational_readonly_goal import ReadonlyGoal, classify_readonly_goal
    from aethos_core.operational_session.operational_session import load_operational_session
    from aethos_core.operational_session.railway_readonly_executor import execute_railway_readonly
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        safe_run_deployment_readiness_checks,
    )

    session = load_operational_session(session_id=session_id)
    resolved = resolve_active_subject(text, session_id=session_id)
    goal = classify_readonly_goal(text, subject=resolved.subject, session=session)
    if goal is None and _RAILWAY_DEPLOY_ENV_RX.search(text):
        goal = ReadonlyGoal(operation="deployment_status", user_text=text)
    if goal is None and infer_railway_readonly_job(text) is not None:
        goal = ReadonlyGoal(operation="list_inventory", user_text=text)
    if goal is None:
        return None

    result = execute_railway_readonly(goal, resolved.subject, session_id=session_id)
    reply_prefix = ""
    if not result.ok and goal.operation in {"deployment_status", "health_check", "fetch_logs"}:
        inv = execute_railway_readonly(
            ReadonlyGoal(operation="list_inventory", user_text=text),
            resolved.subject,
            session_id=session_id,
        )
        if inv.ok:
            session = load_operational_session(session_id=session_id)
            resolved = resolve_active_subject(text, session_id=session_id)
            result = execute_railway_readonly(goal, resolved.subject, session_id=session_id)
        if inv.ok and inv.reply:
            reply_prefix = inv.reply.strip() + "\n\n"

    env_section = ""
    if re.search(r"\b(env|environment|config)\b", text, re.I):
        checks = safe_run_deployment_readiness_checks(user_text=text, session_id=session_id)
        env_lines = list(checks.get("required_env_vars") or [])[:12]
        if env_lines:
            env_section = "\n\n**Env requirements (read-only):**\n" + "\n".join(f"- {row}" for row in env_lines)

    reply = (result.reply or "").strip()
    if reply_prefix:
        reply = f"{reply_prefix}{reply}"
    if env_section:
        reply = f"{reply}{env_section}"

    credential_id = str(resolve_railway_auth_for_chat().get("credential_id") or "")
    meta = {
        "proposed_job_type": "railway_readonly_direct",
        "credential_id": credential_id,
        "auth_method": "api_token",
        "provider": "railway",
        "operation": result.operation,
        "read_only": "true",
        "lane": "railway_readonly_direct",
        "route_id": "railway_readonly_direct",
    }
    return reply, "railway_readonly_direct", meta


def create_railway_readonly_job_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    if not is_railway_readonly_direct_request(text):
        return None

    auth = resolve_railway_auth_for_chat()
    if auth.get("block_reason") == "missing" or not auth.get("credential_id"):
        return railway_connect_required_reply(), "railway_readonly_needs_token", {}

    credential_id = str(auth["credential_id"])
    direct = _execute_railway_readonly_direct(text, session_id=session_id)
    if direct is None:
        return (
            "I couldn't map that Railway request to a read-only diagnostic yet.",
            "railway_readonly_unmapped",
            {"provider": "railway", "credential_id": credential_id},
        )
    body, intent, meta = direct
    meta["credential_id"] = credential_id
    meta["auth_method_label"] = auth_method_label_for_provider("railway", "api_token")
    return body, intent, meta
