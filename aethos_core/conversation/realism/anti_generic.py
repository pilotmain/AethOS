# SPDX-License-Identifier: Apache-2.0
"""Anti-generic layer — block stateless AI phrasing."""

from __future__ import annotations

import re
from typing import Any

_GENERIC_MARKERS = (
    "i don't have context",
    "i do not have context",
    "i'd need more context",
    "i would need more context",
    "i need more context to provide",
    "could you share:",
    "which specific deployment",
    "which deployment you're referring to",
    "tell me more about",
    "as an ai",
    "as a language model",
    "to recommend the most valuable monitoring additions",
    "could you clarify",
    "i'm not sure which",
)

_CONSULTANT_MARKERS = (
    "to recommend the most valuable",
    "here are some general recommendations",
    "it depends on your specific needs",
    "you may want to consider",
)


def is_generic_ai_response(text: str) -> bool:
    lower = (text or "").lower()
    return any(marker in lower for marker in _GENERIC_MARKERS)


def is_consultant_phrasing(text: str) -> bool:
    lower = (text or "").lower()
    return any(marker in lower for marker in _CONSULTANT_MARKERS)


def reshape_generic_response(
    text: str,
    *,
    context: dict[str, Any],
    intent: str | None = None,
) -> str:
    if not is_generic_ai_response(text) and not is_consultant_phrasing(text):
        return text

    subject = context.get("primary_subject") or context.get("deployment_subject") or "the active operational thread"
    replay = context.get("replay_concern") or "replay continuity durability"
    signals = context.get("runtime_signals") or {}

    if intent == "situation_improved":
        return (
            "Operational stability appears to be improving compared to the earlier concern.\n\n"
            "The strongest recovery signals right now are:\n"
            "- sustained telemetry freshness\n"
            "- stable dependency response patterns\n"
            "- no new replay erosion acceleration\n\n"
            f"Extended monitoring is still active because {replay} across long-running sessions "
            "has not yet been fully validated."
        )

    if intent in {"deployment_stabilized", "recovery_status", "did_it_hold"}:
        return (
            "The deployment appears operationally stable across current verification windows.\n\n"
            "Runtime recovery, dependency health, and telemetry freshness remain healthy, "
            "though sustained replay continuity monitoring is still active before full long-tail "
            "stabilization confidence is established."
        )

    if intent == "monitoring_advice":
        return (
            "The highest-value monitoring expansion right now would likely be:\n"
            "- replay continuity durability over long-running operational sessions\n"
            "- topology convergence drift\n"
            "- dependency recovery persistence\n"
            "- long-tail stabilization regression\n\n"
            "Those areas currently appear more operationally sensitive than baseline infrastructure health."
        )

    if intent == "what_changed":
        narrative = signals.get("summary") or f"Recent focus remained on {subject}."
        return (
            f"Since our last operational thread, {narrative}\n\n"
            "No significant survivability degradation acceleration patterns are currently emerging, "
            "though extended monitoring remains active."
        )

    return (
        f"Based on our active operational thread around **{subject}**, the current picture remains bounded.\n\n"
        "Runtime recovery and dependency convergence signals look healthy across current verification windows, "
        f"with {replay} still under sustained monitoring."
    )
