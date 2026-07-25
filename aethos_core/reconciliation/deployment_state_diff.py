# SPDX-License-Identifier: Apache-2.0
"""Deployment state diff — expected vs observed runtime."""

from __future__ import annotations

from typing import Any


def diff_deployment_state(
    *,
    expected: dict[str, Any],
    observed: dict[str, Any],
    readonly: dict[str, Any],
) -> dict[str, Any]:
    exp_state = str(expected.get("expected_state") or expected.get("deployment_state_after") or "")
    obs_state = str(observed.get("deployment_state_after") or observed.get("state") or "")
    summary = str(readonly.get("summary") or "").lower()
    aligned = (not exp_state or not obs_state or exp_state == obs_state) or any(
        w in summary for w in ("success", "running", "ready", "active", "completed")
    )
    return {
        "expected_state": exp_state or None,
        "observed_state": obs_state or None,
        "aligned": aligned,
        "drift_detected": bool(exp_state and obs_state and exp_state != obs_state and not aligned),
    }
