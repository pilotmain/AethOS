# SPDX-License-Identifier: Apache-2.0
"""Desired vs actual — infrastructure reconciliation."""

from __future__ import annotations

from typing import Any


def reconcile_desired_vs_actual(*, desired: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    desired_services = set(desired.get("services") or [])
    observed_services = set(observed.get("services") or [])
    if not desired_services and observed.get("containers"):
        observed_services = {c.get("name") for c in observed.get("containers") or [] if isinstance(c, dict)}
    if not desired_services:
        desired_services = observed_services
    missing = sorted(desired_services - observed_services)
    extra = sorted(observed_services - desired_services)
    aligned = not missing and not extra
    return {
        "aligned": aligned,
        "missing": missing,
        "extra": extra,
        "summary": "Infrastructure desired and observed state aligned." if aligned else f"Drift: {len(missing)} missing, {len(extra)} extra.",
    }
