# SPDX-License-Identifier: Apache-2.0
"""GitHub combined delivery capability routing — FUNCTIONALITY_REALITY_SPRINT_001."""

from __future__ import annotations

import re


_GITHUB_RX = re.compile(r"\bgithub\b", re.I)
_BRANCH_RX = re.compile(r"\b(create\s+)?(?:a\s+)?branch\b", re.I)
_COMMIT_RX = re.compile(r"\bcommit\b", re.I)
_PUSH_RX = re.compile(r"\bpush\b", re.I)
_PR_RX = re.compile(r"\b(open\s+)?(?:a\s+)?(?:pr|pull\s+request)\b", re.I)


def is_github_combined_delivery_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or not _GITHUB_RX.search(raw):
        return False
    actions = sum(
        bool(rx.search(raw))
        for rx in (_BRANCH_RX, _COMMIT_RX, _PUSH_RX, _PR_RX)
    )
    return actions >= 2


def route_github_delivery_capability(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_github_combined_delivery_intent(text):
        return None

    from aethos_core.software_delivery.software_delivery_router import route_software_delivery

    delivery = route_software_delivery(text, session_id=session_id)
    if delivery is not None:
        return delivery

    body = "\n".join(
        [
            "**GitHub delivery — honest capability answer**",
            "",
            "AethOS does **not** expose generic branch/commit/push/PR as one-click ProviderRegistry mutations today.",
            "",
            "**Available via governed software delivery lane:**",
            "- Issue plan → patch proposal → workspace apply → branch push → PR preflight → open PR",
            "- Each step requires explicit approval; git-write ops are **not** enabled on the Connections mutation grid",
            "",
            "**Available on ProviderRegistry (readonly + one mutation):**",
            "- Repo metadata, branch status, commits, workflow runs, failed checks",
            "- **`workflow_rerun`** — governed mutation with preflight + approval",
            "",
            "**Disabled on ProviderRegistry:** `create_branch`, `commit_changes`, `push_branch`, `open_pr`",
            "",
            "**Start here:** `create software delivery issue plan for <your task>`",
            "Or say `push governed branch to github` after an approved patch is applied to the workspace.",
        ]
    )
    return body, "github_delivery_capability_truth", {
        "route_id": "github_delivery_capability",
        "matched_module": "provider_delivery.github_delivery_capability_router",
        "provider": "github",
        "suppress_governance_footer": "true",
        "readonly": "true",
        "mutation_performed": "false",
    }
