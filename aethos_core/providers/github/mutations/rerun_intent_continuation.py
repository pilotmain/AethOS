# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow rerun intent continuation — pending repo and mutation routing."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.provider_readonly_intent.readonly_intent_classifier import extract_github_repo_slug
from aethos_core.providers.github.context.github_context_store import (
    assert_valid_repo_context,
    get_active_github_context,
    resolve_rerun_repository,
)

_GITHUB_WORKFLOW_RERUN_RX = re.compile(
    r"\brerun\b.*\b(?:failed\s+)?(?:github\s+)?workflow\b|\bworkflow\b.*\brerun\b|\brerun\b.*\bactions\b",
    re.I,
)

_PENDING: dict[str, dict[str, Any]] = {}


def is_github_workflow_rerun_request(text: str) -> bool:
    return bool(_GITHUB_WORKFLOW_RERUN_RX.search(text or ""))


def store_pending_rerun_intent(session_id: str, text: str) -> dict[str, Any]:
    entry = {
        "type": "github_workflow_rerun",
        "awaiting": "repo",
        "original_text": (text or "").strip(),
    }
    _PENDING[(session_id or "default").strip() or "default"] = entry
    return entry


def get_pending_rerun_intent(session_id: str = "default") -> dict[str, Any] | None:
    entry = _PENDING.get((session_id or "default").strip() or "default")
    return dict(entry) if isinstance(entry, dict) else None


def clear_pending_rerun_intent(session_id: str = "default") -> None:
    _PENDING.pop((session_id or "default").strip() or "default", None)


def is_pending_rerun_repo_reply(text: str, session_id: str = "default") -> bool:
    if get_pending_rerun_intent(session_id) is None:
        return False
    slug = _extract_repo_slug(text)
    if not slug:
        return False
    valid, _ = assert_valid_repo_context(slug)
    return valid


def continue_pending_rerun_with_repo(
    session_id: str,
    repo_full_name: str,
) -> tuple[str, str, dict[str, str]] | None:
    pending = get_pending_rerun_intent(session_id)
    if pending is None:
        return None
    valid, err = assert_valid_repo_context(repo_full_name)
    if not valid:
        return (
            str(err or "Invalid GitHub repository."),
            "github_workflow_rerun_invalid_repo",
            {"provider": "github", "operation_type": "workflow_rerun"},
        )
    original = str(pending.get("original_text") or "rerun the failed GitHub workflow")
    clear_pending_rerun_intent(session_id)
    return _create_rerun_preflight_reply(
        f"{original} for {repo_full_name}",
        session_id=session_id,
        target_name=repo_full_name,
    )


def compose_github_workflow_rerun_route_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not raw:
        return None

    if is_pending_rerun_repo_reply(raw, session_id=session_id):
        slug = _extract_repo_slug(raw)
        assert slug
        return continue_pending_rerun_with_repo(session_id, slug)

    if not is_github_workflow_rerun_request(raw):
        return None

    repo_resolution = resolve_rerun_repository(
        session_id=session_id,
        user_request=raw,
        target_hints=[],
    )
    if repo_resolution.get("repo"):
        clear_pending_rerun_intent(session_id)
        repo = str(repo_resolution["repo"])
        if extract_github_repo_slug(raw):
            return _create_rerun_preflight_reply(raw, session_id=session_id, target_name=repo)
        return _create_rerun_preflight_reply(
            f"{raw} for {repo}",
            session_id=session_id,
            target_name=repo,
        )

    store_pending_rerun_intent(session_id, raw)
    return (
        _compose_pending_repo_clarification(),
        "github_workflow_rerun_pending_repo",
        {
            "route_id": "github_workflow_rerun",
            "matched_module": "providers.github.mutations.rerun_intent_continuation",
            "provider": "github",
            "operation_type": "workflow_rerun",
            "awaiting": "repo",
        },
    )


def should_readonly_yield_for_github_rerun(text: str, *, session_id: str = "default") -> bool:
    if is_github_workflow_rerun_request(text):
        return True
    if get_pending_rerun_intent(session_id) is not None and _extract_repo_slug(text):
        valid, _ = assert_valid_repo_context(_extract_repo_slug(text) or "")
        return valid
    return False


def _create_rerun_preflight_reply(
    request_text: str,
    *,
    session_id: str,
    target_name: str | None = None,
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply

    reply = create_mutation_preflight_job_reply(request_text, session_id=session_id)
    if reply is None:
        from aethos_core.providers.github.mutations.workflow_rerun_preflight import prepare_workflow_rerun_preflight

        discovery = prepare_workflow_rerun_preflight(
            session_id=session_id,
            target_name=str(target_name or ""),
            user_request=request_text,
        )
        if discovery.get("no_failed_workflow"):
            body = "\n".join(discovery.get("preflight_sections") or [])
            return (
                body,
                "github_workflow_rerun_no_failed_workflow",
                {
                    "route_id": "github_workflow_rerun",
                    "provider": "github",
                    "operation_type": "workflow_rerun",
                    "repository": str(discovery.get("repository") or target_name or ""),
                },
            )
        return None
    body, intent, meta = reply
    meta = {
        **meta,
        "route_id": "github_workflow_rerun",
        "matched_module": "providers.github.mutations.rerun_intent_continuation",
        "provider": "github",
        "operation_type": "workflow_rerun",
    }
    if target_name:
        meta["target_name"] = target_name
    return body, intent, meta


def _compose_pending_repo_clarification() -> str:
    return (
        "Which GitHub repo should I check for failed workflow runs?\n"
        "Example: `pilotmain/aethos`\n\n"
        "No mutation has been performed."
    )


def _extract_repo_slug(text: str) -> str:
    slug = extract_github_repo_slug(text)
    if slug:
        return slug
    candidate = (text or "").strip().strip("`\"'")
    valid, _ = assert_valid_repo_context(candidate)
    return candidate if valid else ""


def clear_pending_rerun_intent_for_tests() -> None:
    _PENDING.clear()
