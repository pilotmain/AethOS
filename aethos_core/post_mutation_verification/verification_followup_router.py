# SPDX-License-Identifier: Apache-2.0
"""Route post-mutation verification follow-ups after lifecycle handling."""

from __future__ import annotations

from aethos_core.post_mutation_verification.verification_intent_router import (
    classify_verification_intent,
    is_post_mutation_verification_intent,
    route_post_mutation_verification,
)

__all__ = [
    "classify_verification_intent",
    "compose_post_mutation_verification_reply",
    "is_post_mutation_verification_intent",
]


def compose_post_mutation_verification_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.github.mutations.rerun_followup_router import compose_github_workflow_rerun_followup_reply

    rerun = compose_github_workflow_rerun_followup_reply(text, session_id=session_id)
    if rerun is not None:
        return rerun
    return route_post_mutation_verification(text, session_id=session_id)
