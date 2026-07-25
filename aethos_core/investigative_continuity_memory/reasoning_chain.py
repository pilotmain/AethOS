# SPDX-License-Identifier: Apache-2.0
"""Investigative continuity memory — cumulative reasoning chains per agent."""

from __future__ import annotations

from typing import Any

from aethos_core.agent_progression_memory.progression_store import _load, _save


_CONFIDENCE_BY_STAGE = {1: "exploratory", 2: "preliminary", 3: "strengthening"}


def record_reasoning_step(
    *,
    session_id: str = "default",
    agent_name: str,
    stage: int,
    hypothesis: str,
    findings: list[str],
    conclusion: str,
) -> dict[str, Any]:
    data = _load(session_id)
    chains: dict[str, list[dict[str, Any]]] = dict(data.get("reasoning_chains") or {})
    history = list(chains.get(agent_name) or [])
    prior = history[0] if history else None
    revision_note = None
    if prior and prior.get("hypothesis") != hypothesis:
        revision_note = f"Revised from: {prior.get('hypothesis', '')[:120]}"
    row = {
        "stage": stage,
        "hypothesis": hypothesis[:240],
        "findings": findings[:6],
        "conclusion": conclusion[:400],
        "confidence": _CONFIDENCE_BY_STAGE.get(stage, "preliminary"),
        "revision_note": revision_note,
        "prior_hypothesis": prior.get("hypothesis") if prior else None,
    }
    history.insert(0, row)
    chains[agent_name] = history[:8]
    data["reasoning_chains"] = chains
    _save(session_id, data)
    return row


def get_reasoning_chain(*, session_id: str = "default", agent_name: str) -> list[dict[str, Any]]:
    data = _load(session_id)
    chains: dict[str, list[dict[str, Any]]] = dict(data.get("reasoning_chains") or {})
    return list(chains.get(agent_name) or [])


def get_latest_hypothesis(*, session_id: str = "default", agent_name: str) -> dict[str, Any] | None:
    chain = get_reasoning_chain(session_id=session_id, agent_name=agent_name)
    return chain[0] if chain else None
