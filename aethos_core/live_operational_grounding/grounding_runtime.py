# SPDX-License-Identifier: Apache-2.0
"""Live grounding runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.live_operational_grounding.live_operation_harness import list_live_operation_flows
from aethos_core.live_operational_grounding.live_reality_convergence import assess_live_reality_convergence
from aethos_core.live_operational_grounding.provider_signal_binding import bind_provider_signals
from aethos_core.live_operational_grounding.recovery_verification_windows import assess_recovery_verification_windows
from aethos_core.live_operational_grounding.regression_guardrails import assess_regression_guardrails
from aethos_core.live_operational_grounding.signal_freshness_tracking import track_signal_freshness


def orchestrate_live_grounding(
    *,
    session_id: str = "default",
    channel: str = "chat",
    primary_subject: str | None = None,
    category: str | None = None,
    reply: str = "",
) -> dict[str, Any]:
    binding = bind_provider_signals(primary_subject=primary_subject, category=category)
    freshness = track_signal_freshness(
        session_id=session_id,
        channel=channel,
        provider_checked_at=binding.get("checked_at"),
    )
    live_reality = assess_live_reality_convergence(
        session_id=session_id,
        channel=channel,
        primary_subject=primary_subject,
        category=category,
    )
    verification_windows = assess_recovery_verification_windows(
        session_id=session_id,
        provider_converged=bool((binding.get("provider_truth") or {}).get("converged")),
    )
    guardrails = assess_regression_guardrails(reply=reply, grounded=True) if reply else {"guardrails_qualified": True}

    live_grounding_qualified = (
        binding.get("bound")
        and binding.get("subject_aligned", False)
        and freshness.get("signals_fresh", False)
        and live_reality.get("live_converged", False)
        and guardrails.get("guardrails_qualified", True)
    )

    return {
        "provider_binding": binding,
        "freshness": freshness,
        "live_reality": live_reality,
        "verification_windows": verification_windows,
        "live_flows": list_live_operation_flows(),
        "regression_guardrails": guardrails,
        "runtime_signals": binding.get("runtime_signals") or {},
        "live_grounding_qualified": live_grounding_qualified,
        "summary": (
            "Live operational grounding qualified — provider truth, freshness, and cross-surface convergence aligned."
            if live_grounding_qualified
            else "Live operational grounding active — stabilizing signals present, full qualification pending."
        ),
    }
