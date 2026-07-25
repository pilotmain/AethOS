# SPDX-License-Identifier: Apache-2.0
"""Telegram soak runner — Phase 11.8.2."""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.external_execution_truth.execution_store import upsert_execution_meta
from aethos_core.jobs.job_state import create_job_record, list_jobs, update_job
from aethos_core.telegram_soak.soak_scenarios import get_soak_scenario, list_soak_scenarios
from aethos_core.telegram_soak.transcript_capture import capture_turn


def _prepare_step_context(
    *,
    session_id: str,
    step: dict[str, Any],
) -> None:
    if step.get("backdate_job_sec"):
        jobs = list_jobs(session_id=session_id, limit=5)
        if jobs:
            back = time.time() - float(step["backdate_job_sec"])
            update_job(str(jobs[0]["job_id"]), status="completed", completed_at=back, updated_at=back)
    if step.get("awaiting_external_callback"):
        job = create_job_record(job_type="gtm_synthesis", session_id=session_id, entity_name="QA")
        update_job(job["job_id"], status="awaiting_callback")
        upsert_execution_meta(
            job["job_id"],
            session_id=session_id,
            runner_mode="external",
            dispatch_status="awaiting_callback",
            dispatched_at=time.time() - 1200,
        )
    if step.get("inject_retries"):
        jobs = list_jobs(session_id=session_id, limit=10)
        for job in jobs[: int(step["inject_retries"])]:
            update_job(str(job["job_id"]), status="retrying", retries=int(step["inject_retries"]))


def run_soak_scenario(
    *,
    scenario_id: str,
    session_id: str,
    mode: str = "compressed",
) -> dict[str, Any]:
    scenario = get_soak_scenario(scenario_id)
    if not scenario:
        return {"ok": False, "reason": "scenario_not_found"}

    turns: list[dict[str, Any]] = []
    with patch.dict("os.environ", {"TRIGGER_ENABLED": "false"}, clear=False):
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        for step in scenario.get("steps") or []:
            delay = float(step.get("simulate_delay_sec") or 0)
            if delay > 0 and mode == "compressed":
                time.sleep(min(delay, 2.0))
            elif delay > 0:
                time.sleep(delay)
            _prepare_step_context(session_id=session_id, step=step)
            user_text = str(step.get("text") or "")
            result = resolve_chat_turn(user_text, session_id=session_id, channel="telegram")
            captured = capture_turn(
                session_id=session_id,
                scenario_id=scenario_id,
                user_text=user_text,
                reply=result.reply,
                mode=mode,
            )
            turns.append(captured)

    scores = [float(t["scores"].get("operational_realism_score") or 0) for t in turns]
    avg = round(sum(scores) / max(len(scores), 1), 3)
    qualified = avg >= 0.45 and all(t["scores"].get("hallucination_risk") != "high" for t in turns)
    return {
        "ok": True,
        "scenario_id": scenario_id,
        "scenario_name": scenario.get("name"),
        "mode": mode,
        "turn_count": len(turns),
        "average_realism_score": avg,
        "qualified": qualified,
        "turns": turns,
    }


def run_all_compressed(*, session_prefix: str = "soak-1182") -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for scenario in list_soak_scenarios():
        sid = f"{session_prefix}-{scenario['id']}"
        results.append(run_soak_scenario(scenario_id=str(scenario["id"]), session_id=sid, mode="compressed"))
    qualified = sum(1 for r in results if r.get("qualified"))
    return {
        "ok": True,
        "phase": "11.8.2",
        "mode": "compressed",
        "scenario_count": len(results),
        "qualified_count": qualified,
        "results": results,
        "summary": f"Telegram soak compressed: {qualified}/{len(results)} scenarios qualified.",
    }
