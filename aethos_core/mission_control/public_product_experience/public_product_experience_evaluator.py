# SPDX-License-Identifier: Apache-2.0
"""FIX 311 — public product experience evaluator."""

from __future__ import annotations

from typing import Any


def classify_capabilities(capabilities: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    proven: list[dict[str, Any]] = []
    experimental: list[dict[str, Any]] = []
    planned: list[dict[str, Any]] = []
    for cap in capabilities:
        status = str(cap.get("status") or "").upper()
        row = {
            "capability_id": cap.get("capability_id"),
            "label": cap.get("label"),
            "status": status,
            "domain": cap.get("domain"),
            "authority_boundary": cap.get("authority_boundary"),
            "read_only": True,
        }
        if status in {"PROVEN", "OPERATIONAL", "CONDITIONALLY_TRUSTED"}:
            proven.append(row)
        elif status in {"EXPERIMENTAL", "IMPLEMENTED"}:
            experimental.append(row)
        else:
            planned.append(row)
    return {"proven": proven, "experimental": experimental, "planned": planned}


def summarize_trust_baseline(
    *,
    fix: str,
    label: str,
    payload: dict[str, Any] | None,
    ok: bool,
) -> dict[str, Any]:
    if not ok or not payload:
        return {
            "baseline_id": fix.lower().replace(" ", "-"),
            "fix": fix,
            "label": label,
            "available": False,
            "trust_recommendation": "unavailable",
            "evidence_summary": "Trust baseline not composed in this session.",
            "read_only": True,
        }
    return {
        "baseline_id": fix.lower().replace(" ", "-"),
        "fix": fix,
        "label": label,
        "available": True,
        "trust_recommendation": payload.get("trust_recommendation")
        or payload.get("overall_trust_recommendation")
        or "evidence_composed",
        "pilot_outcome": payload.get("pilot_outcome"),
        "evidence_summary": payload.get("detail") or payload.get("invariant") or "Trust baseline composed.",
        "read_only": True,
    }
