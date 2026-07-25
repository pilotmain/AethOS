# SPDX-License-Identifier: Apache-2.0
"""Active vs idle operational presence — Phase 11.8.0."""

from __future__ import annotations

from typing import Any

from aethos_core.job_truth.lifecycle_language import canonical_job_state, state_label


def assess_runtime_presence(*, jobs: list[dict[str, Any]], now: float | None = None) -> dict[str, Any]:
    if not jobs:
        return {
            "presence": "idle",
            "summary": "No durable background jobs are registered in this session.",
            "actively_executing": False,
        }

    canonical = [canonical_job_state(j, now=now) for j in jobs]
    active_states = {"queued", "running", "verifying", "stabilizing"}
    active = [j for j, state in zip(jobs, canonical) if state in active_states]
    stalled = [j for j, state in zip(jobs, canonical) if state == "stalled"]

    if active:
        types = ", ".join(sorted({str(j.get("job_type") or "job").replace("_", " ") for j in active[:3]}))
        states = ", ".join(sorted({state_label(s) for s in canonical if s in active_states}))
        return {
            "presence": "executing",
            "summary": f"{len(active)} background job(s) in {states} — {types}.",
            "actively_executing": True,
            "active_jobs": active[:6],
        }

    if stalled:
        return {
            "presence": "stalled",
            "summary": f"{len(stalled)} background job(s) appear stalled — not actively executing.",
            "actively_executing": False,
            "stalled_jobs": stalled[:4],
        }

    latest = jobs[0]
    entity = str(latest.get("entity_name") or "Operational agent")
    return {
        "presence": "idle",
        "summary": f"No jobs are currently executing. Latest activity involved **{entity}**.",
        "actively_executing": False,
        "latest_job": latest,
    }
