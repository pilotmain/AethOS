# SPDX-License-Identifier: Apache-2.0
"""Global workflow discovery follow-up preemption — owns next-step/proposal prompts."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.providers.github.context.github_context_store import (
    get_active_github_context,
    get_github_rerun_context,
)
from aethos_core.providers.github.workflow_discovery.workflow_next_steps import (
    compose_workflow_discovery_next_steps,
    compose_workflow_proposal_reply,
    is_workflow_next_steps_intent,
    is_workflow_proposal_intent,
)

_HARD_NEXT_STEPS_RX = re.compile(
    r"\b("
    r"what\s+should\s+(?:i|we)\s+do\s+next"
    r"|what\s+next"
    r"|what(?:'s| is)\s+(?:the\s+)?next\s+step"
    r"|^next\s+step\b"
    r"|how\s+should\s+(?:i|we)\s+continue"
    r")\b",
    re.I,
)

_HARD_PROPOSAL_RX = re.compile(
    r"\b("
    r"draft\s+(?:a\s+)?workflow\s+proposal"
    r"|create\s+(?:a\s+)?workflow\s+proposal"
    r"|create\s+ci\s+workflow"
    r"|create\s+a\s+ci\s+workflow\s+proposal"
    r"|create\s+ci\s+proposal"
    r"|prepare\s+(?:the\s+)?ci\s+workflow"
    r"|prepare\s+(?:the\s+)?workflow\s+file"
    r"|prepare\s+workflow\s+file"
    r"|propose\s+ci\.yml"
    r"|propose\s+github\s+actions\s+workflow"
    r"|draft\s+ci\.yml"
    r"|generate\s+ci\s+workflow"
    r")\b",
    re.I,
)

_WORKFLOW_DISCOVERY_FOLLOWUP_RX = re.compile(
    r"\b("
    r"what\s+should\s+(?:i|we)\s+do\s+next"
    r"|what\s+next"
    r"|what(?:'s| is)\s+(?:the\s+)?next\s+step"
    r"|^next\s+step\b"
    r"|how\s+should\s+(?:i|we)\s+continue"
    r"|draft\s+(?:a\s+)?workflow\s+proposal"
    r"|create\s+(?:a\s+)?workflow\s+proposal"
    r"|create\s+ci\s+workflow"
    r"|create\s+a\s+ci\s+workflow\s+proposal"
    r"|create\s+ci\s+proposal"
    r"|prepare\s+(?:the\s+)?ci\s+workflow"
    r"|prepare\s+(?:the\s+)?workflow\s+file"
    r"|prepare\s+workflow\s+file"
    r"|propose\s+ci\.yml"
    r"|propose\s+github\s+actions\s+workflow"
    r"|draft\s+ci\.yml"
    r"|generate\s+ci\s+workflow"
    r"|how\s+do\s+i\s+enable\s+workflow"
    r"|how\s+do\s+i\s+create\s+workflow\s+runs?"
    r")\b",
    re.I,
)

_WORKFLOW_ENABLEMENT_RX = re.compile(
    r"\b(how\s+do\s+i\s+enable\s+workflow|how\s+do\s+i\s+create\s+workflow\s+runs?)\b",
    re.I,
)


def _discovery_from_params(params: dict[str, Any]) -> dict[str, Any] | None:
    pf = dict(params.get("mutation_preflight") or {})
    resolution = dict(params.get("workflow_resolution") or pf.get("workflow_resolution") or {})
    debug = dict(params.get("workflow_resolution_debug") or pf.get("workflow_resolution_debug") or {})
    for candidate in (
        params.get("workflow_discovery"),
        resolution.get("workflow_discovery"),
        debug.get("workflow_discovery"),
        pf.get("workflow_discovery"),
    ):
        if isinstance(candidate, dict) and candidate:
            return candidate
    return None


def get_latest_workflow_discovery_context(*, session_id: str = "default") -> dict[str, Any] | None:
    """Resolve the latest persisted workflow discovery for this session."""
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
        get_runtime_workflow_discovery,
    )

    return get_runtime_workflow_discovery(session_id=session_id)


def is_no_workflow_files_discovery(discovery: dict[str, Any] | None) -> bool:
    if not discovery:
        return False
    if discovery.get("workflows_dir_found") is False:
        return True
    if not list(discovery.get("workflow_file_names") or []):
        if not list(discovery.get("workflow_files") or []):
            return True
    likely = str(discovery.get("likely_reason") or "").lower()
    if "no_workflow_files" in likely:
        return True
    if "no `.github/workflows/`" in likely or "workflows are not configured" in likely:
        return True
    if "workflows directory exists but no workflow yaml" in likely:
        return True
    return False


def is_hard_workflow_discovery_next_steps_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _HARD_NEXT_STEPS_RX.search(raw):
        return True
    return is_workflow_next_steps_intent(raw)


def is_hard_workflow_discovery_proposal_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _HARD_PROPOSAL_RX.search(raw):
        return True
    return is_workflow_proposal_intent(raw)


def is_workflow_discovery_followup_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _WORKFLOW_DISCOVERY_FOLLOWUP_RX.search(raw):
        return True
    if is_workflow_next_steps_intent(raw):
        return True
    if is_workflow_proposal_intent(raw):
        return True
    return False


def should_hard_preempt_workflow_discovery(text: str, *, session_id: str = "default") -> bool:
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
        runtime_has_no_workflows,
    )

    if not runtime_has_no_workflows(session_id=session_id):
        return False
    return is_hard_workflow_discovery_next_steps_intent(text) or is_hard_workflow_discovery_proposal_intent(text)


def is_workflow_discovery_followup(text: str, *, session_id: str = "default") -> bool:
    if not is_workflow_discovery_followup_intent(text):
        return False
    return get_latest_workflow_discovery_context(session_id=session_id) is not None


def workflow_discovery_preemption_blocks_route(text: str, *, session_id: str = "default") -> bool:
    """True when workflow discovery context should preempt unrelated follow-up routers."""
    if should_hard_preempt_workflow_discovery(text, session_id=session_id):
        return True
    return is_workflow_discovery_followup(text, session_id=session_id)


def should_yield_active_thread_for_workflow_discovery(text: str, *, session_id: str = "default") -> bool:
    return workflow_discovery_preemption_blocks_route(text, session_id=session_id)


def route_workflow_discovery_followup(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if should_hard_preempt_workflow_discovery(text, session_id=session_id):
        return _compose_hard_preemption_reply(text, session_id=session_id)

    if not is_workflow_discovery_followup_intent(text):
        return None

    discovery = get_latest_workflow_discovery_context(session_id=session_id)
    if not discovery:
        return None

    return _compose_discovery_reply(text, discovery=discovery, session_id=session_id)


def route_workflow_discovery_hard_preemption(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not should_hard_preempt_workflow_discovery(text, session_id=session_id):
        return None
    return _compose_hard_preemption_reply(text, session_id=session_id)


def route_workflow_discovery_hard_preemption_turn(
    text: str,
    *,
    session_id: str = "default",
):
    routed = route_workflow_discovery_hard_preemption(text, session_id=session_id)
    if routed is None:
        return None
    from aethos_core.chat.service import ChatTurnResult

    reply, intent, meta = routed
    return ChatTurnResult(
        reply=reply,
        intent=intent,
        provider_stream=False,
        used_llm=False,
        meta=dict(meta),
    )


def _compose_hard_preemption_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    discovery = get_latest_workflow_discovery_context(session_id=session_id)
    if not discovery or not is_no_workflow_files_discovery(discovery):
        return None
    return _compose_discovery_reply(text, discovery=discovery, session_id=session_id, hard=True)


def _compose_discovery_reply(
    text: str,
    *,
    discovery: dict[str, Any],
    session_id: str,
    hard: bool = False,
) -> tuple[str, str, dict[str, str]]:
    repo_context = get_active_github_context(session_id) or {}
    lower = (text or "").lower()

    if is_hard_workflow_discovery_proposal_intent(text) or is_workflow_proposal_intent(text) or _is_ci_proposal_intent(lower):
        body = compose_workflow_proposal_reply(discovery, repo_context=repo_context)
        intent = "workflow_discovery_proposal"
        _persist_proposal_context(discovery, session_id=session_id)
    elif (
        is_hard_workflow_discovery_next_steps_intent(text)
        or is_workflow_next_steps_intent(text)
        or _is_next_step_intent(lower)
    ):
        body = compose_workflow_discovery_next_steps(discovery, repo_context=repo_context)
        intent = "workflow_discovery_next_steps"
    elif _WORKFLOW_ENABLEMENT_RX.search(lower):
        from aethos_core.providers.github.workflow_discovery.workflow_discovery_reply import (
            compose_workflow_discovery_reply,
        )

        body = compose_workflow_discovery_reply(discovery)
        intent = "workflow_discovery_next_steps"
    else:
        body = compose_workflow_discovery_next_steps(discovery, repo_context=repo_context)
        intent = "workflow_discovery_next_steps"

    return (
        body,
        intent,
        {
            "route_id": intent,
            "matched_module": "providers.github.workflow_discovery.workflow_discovery_followup_router",
            "provider": "github",
            "operation_type": "workflow_discovery_followup",
            "repository": str(discovery.get("repository") or repo_context.get("repo_full_name") or ""),
            "proposal_only": "true" if intent == "workflow_discovery_proposal" else "false",
            "workflow_discovery_preempted": "true",
            "workflow_discovery_hard_preempted": "true" if hard else "false",
        },
    )


def _is_next_step_intent(lower: str) -> bool:
    return any(
        phrase in lower
        for phrase in (
            "what next",
            "next step",
            "what's the next step",
            "what is the next step",
            "how should i continue",
            "how should we continue",
        )
    )


def _is_ci_proposal_intent(lower: str) -> bool:
    return any(
        phrase in lower
        for phrase in (
            "create workflow proposal",
            "create ci proposal",
            "prepare ci workflow",
            "prepare the ci workflow",
            "propose ci.yml",
        )
    )


def _persist_proposal_context(discovery: dict[str, Any], *, session_id: str) -> None:
    try:
        from aethos_core.providers.github.workflow_creation.workflow_creation_context import (
            save_pending_workflow_proposal,
        )
        from aethos_core.providers.github.workflow_discovery.workflow_next_steps import (
            compose_generic_ci_workflow_yaml,
        )

        repo = str(discovery.get("repository") or "")
        default_branch = str(discovery.get("default_branch") or "main")
        save_pending_workflow_proposal(
            session_id=session_id,
            repo=repo,
            file_path=".github/workflows/ci.yml",
            branch="add-ci-workflow",
            base_branch=default_branch,
            proposal_yaml=compose_generic_ci_workflow_yaml(default_branch=default_branch),
        )
    except Exception:
        pass
