# SPDX-License-Identifier: Apache-2.0
"""Causality engine — root-cause chain inference."""

from __future__ import annotations

from typing import Any

_CAUSAL_CHAINS = (
    ("github_workflow_failure", "deployment_skipped", "railway_restart", "browser_verification_failed"),
    ("deployment_instability", "stale_telemetry", "operational_drift"),
    ("flaky_workflow", "deployment_delay", "stale_browser_evidence"),
)


def infer_causal_chain(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Infer causal chains from operational events."""
    text_blob = " ".join(
        f"{e.get('source', '')} {e.get('summary', '')} {e.get('category', '')} {e.get('detail', '')}".lower()
        for e in events
    )
    chains: list[dict[str, Any]] = []

    if any(k in text_blob for k in ("workflow", "github", "rerun")):
        steps = []
        if "workflow" in text_blob or "github" in text_blob:
            steps.append("GitHub workflow failure")
        if "deployment" in text_blob or "skipped" in text_blob:
            steps.append("deployment skipped")
        if "railway" in text_blob or "restart" in text_blob:
            steps.append("Railway restart attempted")
        if "browser" in text_blob:
            steps.append("browser verification failed")
        if "stale" in text_blob or "telemetry" in text_blob:
            steps.append("telemetry became stale")
        if "drift" in text_blob:
            steps.append("operational drift anomaly triggered")
        if len(steps) >= 2:
            chains.append({"chain_id": "causal-primary", "steps": steps, "confidence": min(0.45 + len(steps) * 0.1, 0.88)})

    for seed, *rest in _CAUSAL_CHAINS:
        if seed.replace("_", " ") in text_blob or seed in text_blob:
            matched = [seed.replace("_", " ")]
            for step in rest:
                if step.replace("_", " ") in text_blob or any(w in text_blob for w in step.split("_")):
                    matched.append(step.replace("_", " "))
            if len(matched) >= 2:
                chains.append({"chain_id": f"causal-{seed[:8]}", "steps": matched, "confidence": 0.55 + len(matched) * 0.08})

    return chains[:3]
