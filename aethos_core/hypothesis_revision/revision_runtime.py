# SPDX-License-Identifier: Apache-2.0
"""Hypothesis revision — evolving strategic assumptions across stages."""

from __future__ import annotations

from typing import Any

from aethos_core.investigative_continuity_memory.reasoning_chain import get_reasoning_chain


def assess_hypothesis_revision(
    *,
    session_id: str = "default",
    agent_name: str,
    current_hypothesis: str,
) -> dict[str, Any]:
    chain = get_reasoning_chain(session_id=session_id, agent_name=agent_name)
    if len(chain) < 2:
        return {"revised": False, "summary": "Initial hypothesis forming."}
    prior = chain[1]
    prior_hyp = str(prior.get("hypothesis") or "")
    if prior_hyp and prior_hyp != current_hypothesis:
        return {
            "revised": True,
            "prior_hypothesis": prior_hyp,
            "current_hypothesis": current_hypothesis,
            "summary": "Hypothesis refined as investigation progressed.",
        }
    return {
        "revised": False,
        "prior_hypothesis": prior_hyp,
        "current_hypothesis": current_hypothesis,
        "summary": "Hypothesis strengthening — not yet revised.",
    }
