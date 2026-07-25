# SPDX-License-Identifier: Apache-2.0
"""Live narrative composer — grounded follow-up narratives from live signals."""

from __future__ import annotations

from typing import Any


def _stale_uncertainty(*, live: dict[str, Any]) -> str:
    freshness = live.get("freshness") or {}
    cross = live.get("cross_surface") or {}
    if cross.get("drift_detected"):
        return (
            "I see a mismatch between the latest runtime signal and the earlier thread, "
            "so I'm treating this as not fully confirmed yet.\n\n"
        )
    if freshness.get("stale"):
        stale = ", ".join(freshness.get("stale_sources") or ["memory"])
        return (
            f"The latest provider check is current, but some continuity sources look stale ({stale}). "
            "I'll stay honest about that boundary.\n\n"
        )
    return ""


def compose_live_stability_reply(
    *,
    subject: str,
    live: dict[str, Any],
    closing: str,
    intent: str = "did_it_hold",
) -> str:
    """Calm, grounded stability narrative — never premature 'fully stable'."""
    lead = _stale_uncertainty(live=live)
    binding = live.get("provider_binding") or {}
    signals = binding.get("runtime_signals") or {}
    provider = binding.get("provider") or "Railway"
    stabilized = binding.get("stabilized", False)
    windows = live.get("verification_windows") or {}
    window_hint = windows.get("next_verification") or "the next sustained verification window"

    if intent == "did_it_hold":
        if stabilized and not windows.get("fully_proven"):
            body = (
                f"The **{provider}** restart appears to be holding so far.\n\n"
                f"The latest runtime signal and **{subject}** state look aligned, "
                "and I don't currently see a fresh recovery regression. "
                f"I'd still treat this as **stabilizing** rather than fully proven until {window_hint} completes."
            )
        elif windows.get("fully_proven"):
            body = (
                f"The **{provider}** restart has held through sustained verification windows.\n\n"
                f"**{subject}** reads stable across current checks — still keeping observation active."
            )
        else:
            body = (
                f"**{subject}** is still in an active stabilization window.\n\n"
                f"Latest {provider} signals haven't fully converged yet — "
                "I'm not calling this fully held until sustained verification completes."
            )
    elif intent == "what_changed":
        summary = signals.get("summary") or f"focus remained on {subject}"
        body = f"Since our last thread, {summary}"
    elif intent == "monitoring_advice":
        body = (
            f"I'd watch **{subject}**, downstream dependency persistence, and any late regression "
            "after stabilization before adding generic monitors."
        )
    else:
        body = (
            f"**{subject}** reads as stabilizing from the latest provider and runtime checks.\n\n"
            "Recovery signals look healthy so far, but I'm keeping extended observation active."
        )

    return f"{lead}{body}\n\n{closing}"


def compose_live_risk_reply(*, subject: str, live: dict[str, Any]) -> str:
    lead = _stale_uncertainty(live=live)
    cross = live.get("cross_surface") or {}
    if cross.get("drift_detected"):
        return (
            f"{lead}There's still active risk around **{subject}** because surfaces aren't fully aligned. "
            "I'd verify runtime truth before assuming recovery is durable."
        )
    return (
        f"{lead}I still see bounded risk on **{subject}** — nothing catastrophic accelerating, "
        "but sustained verification hasn't fully cleared yet."
    )
