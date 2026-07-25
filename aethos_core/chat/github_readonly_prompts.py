# SPDX-License-Identifier: Apache-2.0
"""Chat routing for GitHub on-demand repository inventory jobs."""

from __future__ import annotations

from aethos_core.connections.adapters import auth_method_label_for_provider
from aethos_core.runtime.authority import authority
from aethos_core.runtime.github_readonly_jobs import (
    github_connect_required_reply,
    infer_github_readonly_job,
    resolve_github_auth_for_chat,
)


def create_github_readonly_job_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    inferred = infer_github_readonly_job(text)
    if inferred is None:
        return None

    auth = resolve_github_auth_for_chat()
    if auth.get("block_reason") == "missing" or not auth.get("credential_id"):
        return github_connect_required_reply(), "github_readonly_needs_token", {}

    title, job_type, params = inferred
    credential_id = str(auth["credential_id"])
    params = {
        **params,
        "auth_method": "api_token",
        "auth_method_label": auth_method_label_for_provider("github", "api_token"),
        "credential_id": credential_id,
        "browser_used": False,
        "provider_used": "github",
        "data_source": "provider_api",
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
        f"Created tracked job `{job.id}` to list GitHub repositories using your **saved API token**.\n\n"
        f"**Type:** {job_type} · **read-only** · **auth:** GitHub API token\n\n"
        "Summary will appear here; the full report is in **Mission Control → Jobs**."
    )
    return (
        body,
        "github_readonly_job_created",
        {
            "proposed_job_id": job.id,
            "proposed_job_type": job.job_type,
            "credential_id": credential_id,
            "auth_method": "api_token",
            "provider": "github",
        },
    )
