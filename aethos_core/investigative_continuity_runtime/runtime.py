# SPDX-License-Identifier: Apache-2.0
"""Investigative continuity runtime aggregate — Phase 11.7.8."""

from __future__ import annotations

from typing import Any

from aethos_core.investigative_continuity_memory.reasoning_chain import get_reasoning_chain


def assess_investigative_continuity_runtime(
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any]:
    """Phase 11.7.8 — investigative continuity realism."""
    chains: dict[str, list[dict[str, Any]]] = {}
    for artifact in _all_agent_names(session_id):
        chain = get_reasoning_chain(session_id=session_id, agent_name=artifact)
        if chain:
            chains[artifact] = chain

    qualified = bool(chains)
    return {
        "ok": True,
        "phase": "11.7.8",
        "converged": qualified,
        "reasoning_chains": chains,
        "chain_count": sum(len(c) for c in chains.values()),
        "summary": (
            "Investigative continuity active — cumulative reasoning chains preserved."
            if qualified
            else "Investigative continuity ready — awaiting progression prompts."
        ),
    }


def _all_agent_names(session_id: str) -> list[str]:
    from aethos_core.operational_entity_runtime.lightweight_agent_registry import list_active_entities

    return [str(e.get("name") or "") for e in list_active_entities(session_id=session_id) if e.get("name")]
