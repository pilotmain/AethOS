# SPDX-License-Identifier: Apache-2.0
"""GitHub readonly inspection routing."""

from __future__ import annotations

from aethos_core.provider_readonly_intent.readonly_intent_classifier import (
    ReadonlyProviderIntent,
    classify_github_readonly_intent,
)


def compose_github_readonly_route_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.deployment_targets.resolver import get_session_deploy_target
    from aethos_core.providers.github.mutations.rerun_intent_continuation import should_readonly_yield_for_github_rerun

    pending = get_session_deploy_target(session_id)
    if pending and str(pending.get("flow") or "") == "railway_greenfield":
        return None

    if should_readonly_yield_for_github_rerun(text, session_id=session_id):
        return None
    intent = classify_github_readonly_intent(text)
    if intent is None:
        return None

    if intent.operation == "repo_inventory":
        from aethos_core.chat.github_readonly_prompts import create_github_readonly_job_reply

        job_reply = create_github_readonly_job_reply(text, session_id=session_id)
        if job_reply is not None:
            body, reply_intent, meta = job_reply
            meta = {
                **meta,
                "route_id": "provider_readonly_intent",
                "matched_module": "provider_readonly_intent.github_readonly_router",
                "readonly_provider": "github",
                "readonly_operation": intent.operation,
            }
            return body, reply_intent, meta
        return None

    if not intent.repo:
        return (
            _compose_repo_clarification(),
            "github_readonly_repo_clarification",
            {
                "route_id": "provider_readonly_intent",
                "matched_module": "provider_readonly_intent.github_readonly_router",
                "readonly_provider": "github",
                "readonly_operation": intent.operation,
            },
        )

    from aethos_core.runtime.github_readonly_jobs import resolve_github_auth_for_chat

    auth = resolve_github_auth_for_chat()
    if auth.get("block_reason") == "missing" or not auth.get("credential_id"):
        from aethos_core.runtime.github_readonly_jobs import github_connect_required_reply

        return (
            github_connect_required_reply(),
            "github_readonly_needs_token",
            {
                "route_id": "provider_readonly_intent",
                "readonly_provider": "github",
                "readonly_operation": intent.operation,
            },
        )

    from aethos_core.providers.github.auth import GitHubAuthAdapter

    token = GitHubAuthAdapter().get_api_token(str(auth["credential_id"]))
    if not token:
        return (
            "GitHub credentials are configured but the API token could not be loaded.\n\n"
            "Re-save the token in **Mission Control → Advanced settings → Credentials → GitHub**.",
            "github_readonly_needs_token",
            {
                "route_id": "provider_readonly_intent",
                "readonly_provider": "github",
            },
        )

    from aethos_core.providers.github.diagnostics.github_live_diagnostics import run_github_live_diagnostics

    body, meta = run_github_live_diagnostics(
        token,
        repository=intent.repo,
        session_id=session_id,
        operation=intent.operation,
    )
    return body, f"github_readonly_{intent.operation}", meta


def _compose_repo_clarification() -> str:
    return (
        "I can run GitHub live diagnostics read-only: repo status, branch divergence, commits, "
        "workflow failures, failed checks, PR status, releases/tags, and deploy correlation.\n\n"
        "Which GitHub repo should I inspect?\n"
        "Example: `pilotmain/aethos`\n\n"
        "No mutation has been performed."
    )
