# SPDX-License-Identifier: Apache-2.0
"""Crash-isolated Railway deployment readiness routing."""

from __future__ import annotations

import logging
from typing import Any

_log = logging.getLogger(__name__)


def safe_route_railway_deployment_readiness(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Never raises — returns structured blocker on failure or exception."""
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_intent import (
        is_railway_deployment_readiness_intent,
    )

    raw = (text or "").strip()
    if not is_railway_deployment_readiness_intent(raw):
        return None

    try:
        from aethos_core.providers.railway.deployment_readiness.deployment_readiness_router import (
            route_railway_deployment_readiness,
        )

        result = route_railway_deployment_readiness(raw, session_id=session_id)
        if result is not None:
            return result
        return _blocker_from_exception(
            session_id=session_id,
            diagnostic="route returned no result for a matched readiness intent",
            checks=_empty_checks(),
        )
    except Exception as exc:
        _log.exception("Railway deployment readiness crashed for session=%s", session_id)
        checks = _empty_checks()
        try:
            from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
                safe_run_deployment_readiness_checks,
            )

            checks = safe_run_deployment_readiness_checks(user_text=raw, session_id=session_id)
        except Exception:
            pass
        return _blocker_from_exception(session_id=session_id, diagnostic=str(exc), checks=checks)


def _empty_checks() -> dict[str, Any]:
    return {
        "inventory": {"ok": False, "error": "not run"},
        "github_binding": {"github_credential_ok": False, "accessible_repos_count": 0},
        "railway_credential_ok": False,
        "railway_api_connection_ok": False,
        "required_env_vars": [],
        "service_creation": {},
        "referenced_github_repo": "",
    }


def _blocker_from_exception(
    *,
    session_id: str,
    diagnostic: str,
    checks: dict[str, Any],
) -> tuple[str, str, dict[str, str]]:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
        compose_readiness_blocker,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_router import _meta

    body = compose_readiness_blocker(checks, diagnostic=diagnostic)
    return body, "railway_deployment_readiness_blocked", _meta(
        session_id,
        stage="blocked",
        checks=checks,
        diagnostic=diagnostic,
    )
