# SPDX-License-Identifier: Apache-2.0
"""Deterministic chat replies for source binding correction."""

from __future__ import annotations

from aethos_core.provider_topology.repo_reference_parser import is_railway_restart_with_repo_target
from aethos_core.provider_topology.source_binding_correction import (
    is_binding_confirmation,
    process_binding_correction,
    process_restart_with_repo_target,
    should_handle_binding_correction,
)


def compose_source_binding_correction_reply(
    text: str,
    *,
    session_id: str = "default",
    accessible_repos: list[str] | None = None,
) -> tuple[str, str, dict[str, str]] | None:
    if is_railway_restart_with_repo_target(text):
        restart = process_restart_with_repo_target(text, session_id=session_id, accessible_repos=accessible_repos)
        if restart is not None:
            return (
                restart["message"],
                "source_binding_correction",
                {
                    "kind": str(restart.get("kind") or ""),
                    "repo": str((restart.get("repo_ref") or {}).get("full_name") or ""),
                },
            )

    if not should_handle_binding_correction(text, session_id=session_id):
        return None

    if is_binding_confirmation(text):
        result = process_binding_correction(text, session_id=session_id, accessible_repos=accessible_repos)
        intent = "source_binding_updated" if result.get("kind") == "binding_updated" else "source_binding_correction"
        return (
            str(result.get("message") or ""),
            intent,
            {
                "kind": str(result.get("kind") or ""),
                "repo": str((result.get("repo_ref") or {}).get("full_name") or ""),
            },
        )

    result = process_binding_correction(text, session_id=session_id, accessible_repos=accessible_repos)
    kind = str(result.get("kind") or "")
    if kind == "no_repo":
        return None
    intent = "source_binding_correction"
    if kind == "binding_updated":
        intent = "source_binding_updated"
    elif kind == "repo_reconciliation":
        intent = "repo_reconciliation"
    elif kind == "access_failed":
        intent = "source_binding_access_failed"
    elif kind == "confirmation_needed":
        intent = "source_binding_confirmation"
    return (
        str(result.get("message") or ""),
        intent,
        {
            "kind": kind,
            "repo": str((result.get("repo_ref") or {}).get("full_name") or ""),
        },
    )
