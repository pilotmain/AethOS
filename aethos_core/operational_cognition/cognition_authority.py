# SPDX-License-Identifier: Apache-2.0
"""Cognition authority gate — legacy routers may not create operational jobs."""

from __future__ import annotations

import logging

_log = logging.getLogger(__name__)

LEGACY_OPERATIONAL_JOB_ROUTES = frozenset(
    {
        "operation_preflight",
        "vercel_why_down",
        "vercel_readonly",
        "browser_diagnostic",
        "browser_vercel_diagnostics",
        "mutation_preflight",
        "external_health_job",
        "browser_intent_job",
        "provider_job",
        "tracked_job",
        "continuity_reconstruction",
    }
)


def cognition_authority_blocks_legacy_job(*, attempted_route: str, text: str, session_id: str = "default") -> bool:
    """True when a legacy module must not create operational jobs for this turn."""
    from aethos_core.config import get_settings

    if getattr(get_settings(), "chat_single_loop_enabled", False):
        return False

    from aethos_core.failed_service_investigation.global_preemption import (
        classify_failed_service_intent,
        is_cognition_owned_failure_investigation,
    )

    if attempted_route not in LEGACY_OPERATIONAL_JOB_ROUTES:
        return False

    if is_cognition_owned_failure_investigation(text, session_id=session_id):
        _log.info(
            "Cognition authority blocked legacy job route=%s session=%s intent=%s",
            attempted_route,
            session_id,
            classify_failed_service_intent(text),
        )
        return True

    from aethos_core.chat.operational_master_router import master_router_has_priority_route

    if master_router_has_priority_route(text, session_id=session_id):
        return True

    return False
