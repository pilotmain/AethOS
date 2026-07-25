# SPDX-License-Identifier: Apache-2.0
"""Provider isolation guards — GitHub workflow lane must not run on Railway/Vercel mutations."""

from __future__ import annotations

import re

_RAILWAY_PROVIDER_RX = re.compile(r"\b(?:railway|rail\s*way)\b", re.I)
_GITHUB_WORKFLOW_LANE_HINT_RX = re.compile(
    r"\b("
    r"workflow\s+proposal"
    r"|workflow\s+file"
    r"|ci\.yml"
    r"|github\s+actions"
    r"|draft\s+workflow"
    r"|workflow\s+creation"
    r"|workflow\s+lane"
    r")\b",
    re.I,
)

_BARE_RETRY_RX = re.compile(r"^\s*(?:retry|try\s+again)\s*\.?\s*$", re.I)

_ACTIVE_LANE_STAGES = frozenset(
    {
        "proposal_ready",
        "creation_plan_ready",
        "execution_blocked",
        "executed",
    }
)


def is_railway_mutation_context(text: str, *, provider: str | None = None) -> bool:
    """True when the turn is clearly a Railway mutation, not a GitHub workflow lane turn."""
    if provider and provider.lower() == "railway":
        return True
    raw = text or ""
    if not _RAILWAY_PROVIDER_RX.search(raw):
        return False
    return not _GITHUB_WORKFLOW_LANE_HINT_RX.search(raw)


def has_github_workflow_lane_intent(text: str) -> bool:
    """Explicit GitHub workflow lane prompts (never bare retry / try again)."""
    from aethos_core.providers.github.workflow_lane.workflow_execution_followup import (
        is_workflow_execution_followup,
    )
    from aethos_core.providers.github.workflow_lane.workflow_lane_router import (
        _CANCEL_RX,
        _CREATION_RX,
        _PROPOSAL_RX,
        _PUSH_MAIN_RX,
        _WORKFLOW_LANE_EXPLICIT_RETRY_RX,
    )

    raw = text or ""
    if is_railway_mutation_context(raw):
        return False
    if _BARE_RETRY_RX.match(raw.strip()):
        return False
    return (
        bool(_PROPOSAL_RX.search(raw))
        or bool(_CREATION_RX.search(raw))
        or bool(_PUSH_MAIN_RX.search(raw))
        or bool(_CANCEL_RX.search(raw))
        or bool(_WORKFLOW_LANE_EXPLICIT_RETRY_RX.search(raw))
        or is_workflow_execution_followup(raw)
    )


def should_run_github_workflow_lane(text: str, *, provider: str | None = None) -> bool:
    if provider and provider.lower() != "github":
        return False
    if is_railway_mutation_context(text, provider=provider):
        return False
    return has_github_workflow_lane_intent(text)


def _has_active_github_workflow_lane(session_id: str) -> bool:
    from aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle import (
        load_latest_workflow_lane_state,
    )

    state = load_latest_workflow_lane_state(session_id=session_id)
    if not state:
        return False
    return str(state.get("stage") or "") in _ACTIVE_LANE_STAGES


def should_hydrate_github_workflow_context(
    *,
    text: str = "",
    session_id: str = "default",
    provider: str | None = None,
) -> bool:
    """Hydrate GitHub workflow discovery/lane only when the turn needs it."""
    if is_railway_mutation_context(text, provider=provider):
        return False
    if provider and provider.lower() not in ("", "github"):
        if provider.lower() in ("railway", "vercel"):
            return should_run_github_workflow_lane(text, provider=provider)
    if should_run_github_workflow_lane(text, provider=provider):
        return True
    from aethos_core.providers.github.workflow_lane.workflow_execution_followup import (
        is_workflow_execution_followup,
    )

    if is_workflow_execution_followup(text):
        return True
    return _has_active_github_workflow_lane(session_id)


def maybe_hydrate_github_workflow_context(
    *,
    text: str = "",
    session_id: str = "default",
    provider: str | None = None,
) -> None:
    if not should_hydrate_github_workflow_context(
        text=text, session_id=session_id, provider=provider
    ):
        return
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
        hydrate_workflow_discovery_context,
    )
    from aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle import (
        hydrate_workflow_lane_context,
    )

    hydrate_workflow_discovery_context(session_id=session_id)
    hydrate_workflow_lane_context(session_id=session_id)
