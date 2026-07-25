# SPDX-License-Identifier: Apache-2.0
"""Shared approval phrase templates for inbox + UI execution."""

from __future__ import annotations

GATE_CHAT_PREFIX: dict[str, str] = {
    "planning_approved": "approve implementation planning",
    "branch_create": "create implementation branch",
    "patch_proposal_approved": "approve patch proposal",
    "workspace_apply": "apply approved patch to workspace",
    "github_preflight_approved": "approve github pr creation preflight",
}


def build_copy_phrase_text(*, gate_id: str, required_phrases: list[str]) -> str:
    prefix = GATE_CHAT_PREFIX.get(gate_id)
    phrases = [p.strip() for p in required_phrases if (p or "").strip()]
    if not prefix:
        return "\n".join(phrases)
    return "\n".join([prefix, *phrases])
