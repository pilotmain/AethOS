# SPDX-License-Identifier: Apache-2.0
"""Telegram soak validation API — Phase 11.8.2."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(tags=["telegram-soak"])


@router.get("/telegram-soak/state")
def get_telegram_soak_state_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.telegram_soak.runtime import assess_telegram_soak_runtime

    return assess_telegram_soak_runtime(session_id=session_id, channel="api")


@router.get("/telegram-soak/scenarios")
def get_telegram_soak_scenarios_api() -> dict[str, Any]:
    from aethos_core.telegram_soak.soak_scenarios import list_soak_scenarios

    return {"ok": True, "phase": "11.8.2", "scenarios": list_soak_scenarios()}


@router.get("/telegram-soak/ledger")
def get_telegram_soak_ledger_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.telegram_soak.session_truth_ledger import summarize_ledger

    return summarize_ledger(session_id=session_id)


@router.post("/telegram-soak/run/{scenario_id}")
def post_run_soak_scenario_api(
    scenario_id: str,
    session_id: str = "default",
    mode: str = "compressed",
) -> dict[str, Any]:
    from aethos_core.telegram_soak.soak_runner import run_soak_scenario

    return run_soak_scenario(scenario_id=scenario_id, session_id=session_id, mode=mode)


@router.post("/telegram-soak/run-compressed")
def post_run_all_compressed_soak_api(session_prefix: str = "soak-1182") -> dict[str, Any]:
    from aethos_core.telegram_soak.soak_runner import run_all_compressed

    return run_all_compressed(session_prefix=session_prefix)
