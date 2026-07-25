# SPDX-License-Identifier: Apache-2.0
"""Investigative narrative — cumulative reasoning continuity in replies."""

from __future__ import annotations

from typing import Any

from aethos_core.hypothesis_revision.revision_runtime import assess_hypothesis_revision
from aethos_core.investigative_continuity_memory.reasoning_chain import get_reasoning_chain, record_reasoning_step


def _hypothesis_from_deliverable(deliverable: dict[str, Any]) -> str:
    conclusion = str(deliverable.get("conclusion") or "")
    if conclusion:
        return conclusion[:240]
    findings = deliverable.get("findings") or []
    return str(findings[0]) if findings else str(deliverable.get("headline") or "")


def enrich_investigative_narrative(
    *,
    session_id: str = "default",
    agent_name: str,
    stage: int,
    base_reply: str,
    deliverable: dict[str, Any],
    record: bool = True,
) -> str:
    hypothesis = _hypothesis_from_deliverable(deliverable)
    findings = list(deliverable.get("findings") or [])
    conclusion = str(deliverable.get("conclusion") or "")

    if record:
        record_reasoning_step(
            session_id=session_id,
            agent_name=agent_name,
            stage=stage,
            hypothesis=hypothesis,
            findings=findings,
            conclusion=conclusion,
        )

    chain = get_reasoning_chain(session_id=session_id, agent_name=agent_name)
    revision = assess_hypothesis_revision(
        session_id=session_id,
        agent_name=agent_name,
        current_hypothesis=hypothesis,
    )

    parts = [base_reply]
    if len(chain) >= 2 and stage >= 2:
        earlier = chain[1]
        earlier_hyp = str(earlier.get("hypothesis") or earlier.get("conclusion") or "")
        if earlier_hyp:
            parts.append(
                f"\n\n**Investigative continuity:** Earlier read — {earlier_hyp[:180]}. "
                f"That framing is now {'refined' if revision.get('revised') else 'strengthening'} at stage {stage}."
            )
    if revision.get("revised") and revision.get("prior_hypothesis"):
        parts.append(
            f"\n\n**Hypothesis revision:** Shifted from earlier assumption toward the current strategic read."
        )

    confidence = {1: "exploratory", 2: "preliminary", 3: "strengthening"}.get(stage, "preliminary")
    if stage < 3:
        parts.append(f"\n\n_Strategic confidence: {confidence} — conclusions may evolve as research continues._")
    else:
        parts.append("\n\n_Strategic confidence: strengthening — conclusions are converging but remain open to revision._")

    return "".join(parts)
