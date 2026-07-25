# SPDX-License-Identifier: Apache-2.0
"""Operational artifacts — evolving findings and summaries."""

from __future__ import annotations

from typing import Any

from aethos_core.agent_progression_memory.progression_store import get_progression_state, record_progression_artifact


def list_session_artifacts(*, session_id: str = "default") -> list[dict[str, Any]]:
    return list(get_progression_state(session_id=session_id).get("artifacts") or [])


def store_finding_artifact(
    *,
    session_id: str = "default",
    agent_name: str,
    summary: str,
    artifact_type: str = "finding",
) -> dict[str, Any]:
    return record_progression_artifact(
        session_id=session_id,
        agent_name=agent_name,
        artifact_type=artifact_type,
        summary=summary,
    )
