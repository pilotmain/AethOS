# SPDX-License-Identifier: Apache-2.0
"""Cross-provider correlation chat routing."""

from __future__ import annotations

from aethos_core.cross_provider_correlation.correlation_intent_classifier import classify_correlation_intent
from aethos_core.cross_provider_correlation.correlation_runtime import run_correlation_analysis


def route_cross_provider_correlation_question(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = classify_correlation_intent(text)
    if intent is None:
        return None
    reply, meta, _, _ = run_correlation_analysis(
        session_id=session_id,
        intent=intent.kind,
        repository=intent.repository,
        project=intent.project,
    )
    return reply, f"cross_provider_{intent.kind}", meta
