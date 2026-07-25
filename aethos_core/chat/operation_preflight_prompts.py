# SPDX-License-Identifier: Apache-2.0
"""Chat routing for operational preflight jobs — planning only, no mutations."""

from __future__ import annotations

from aethos_core.connections.adapters import auth_method_label_for_provider
from aethos_core.operations.execution.execution_permissions import is_mutating_operation
from aethos_core.operations.intents import infer_operation_preflight_intent
from aethos_core.runtime.authority import authority


def create_operation_preflight_job_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.operational_master_router import master_router_has_priority_route
    from aethos_core.chat.route_trace import is_internal_diagnostics_query

    if is_internal_diagnostics_query(text):
        return None

    if master_router_has_priority_route(text, session_id=session_id):
        return None

    from aethos_core.operational_cognition.cognition_authority import cognition_authority_blocks_legacy_job

    if cognition_authority_blocks_legacy_job(
        attempted_route="operation_preflight",
        text=text,
        session_id=session_id,
    ):
        return None

    inferred = infer_operation_preflight_intent(text, session_id=session_id)
    if inferred is None:
        return None

    title, job_type, params = inferred
    if is_mutating_operation(str(params.get("operation_type") or "")):
        return None

    provider = str(params.get("provider") or "")
    if provider == "railway":
        from aethos_core.chat.railway_readonly_prompts import create_railway_readonly_job_reply

        railway_direct = create_railway_readonly_job_reply(text, session_id=session_id)
        if railway_direct is not None:
            return railway_direct

    job = authority.create_job(
        title=title,
        job_type=job_type,
        params=params,
        source="chat",
        session_id=session_id,
        auto_run=True,
    )
    op = str(params.get("operation_type") or job_type).replace("_", " ")
    provider = str(params.get("provider") or "unknown")
    auth_hint = ""
    if provider == "vercel":
        from aethos_core.providers.vercel.auth import VercelAuthAdapter

        resolved = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
        method = str(resolved.get("method") or "")
        if method == "api_token":
            auth_hint = (
                f"\n\n**Auth path:** {auth_method_label_for_provider('vercel', 'api_token')} "
                "(API-first read-only execution)."
            )
        elif method == "browser":
            auth_hint = (
                f"\n\n**Auth path:** {auth_method_label_for_provider('vercel', 'browser')} "
                "(browser fallback may be used for logs)."
            )
    elif provider == "railway":
        from aethos_core.providers.railway.auth import RailwayAuthAdapter

        resolved = RailwayAuthAdapter().resolve_best_auth_method(operation="read_projects")
        method = str(resolved.get("method") or "")
        if method == "api_token":
            auth_hint = (
                f"\n\n**Auth path:** {auth_method_label_for_provider('railway', 'api_token')} "
                "(API-first read-only execution)."
            )
    elif provider == "github":
        from aethos_core.providers.github.auth import GitHubAuthAdapter

        resolved = GitHubAuthAdapter().resolve_best_auth_method(operation="read_repos")
        method = str(resolved.get("method") or "")
        if method == "api_token":
            auth_hint = (
                f"\n\n**Auth path:** {auth_method_label_for_provider('github', 'api_token')} "
                "(API-first read-only execution)."
            )
    body = (
        f"Created tracked preflight job `{job.id}` (**read-only**).\n\n"
        f"**Operation:** {op} · **Provider:** {provider}{auth_hint}\n\n"
        "When the preflight completes, approve **read-only execution** in **Mission Control → Jobs** "
        "to run safe diagnostics (deployments, domains, logs, URL checks). "
        "Mutating operations remain disabled.\n\n"
        "Summary will appear here; the full preflight report is in **Mission Control → Jobs**."
    )
    return (
        body,
        "operation_preflight_job_created",
        {
            "proposed_job_id": job.id,
            "proposed_job_type": job.job_type,
            "operation_type": str(params.get("operation_type") or ""),
            "provider": provider,
        },
    )
