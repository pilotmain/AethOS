# SPDX-License-Identifier: Apache-2.0
"""Provider-wide health summary prioritization tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.operational_planner.adapters.railway_wide_health import (
    compose_provider_wide_health_followup,
    compose_railway_provider_wide_health_reply,
    format_health_report_body,
    summarize_health_rows,
)
from aethos_core.operational_planner.planner_router import compose_planned_operational_reply
from aethos_core.operational_planner.provider_wide_health_store import (
    clear_provider_wide_health_for_tests,
    get_provider_wide_health_report,
    save_provider_wide_health_report,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    yield
    clear_provider_wide_health_for_tests()


def _rows() -> list[dict]:
    return [
        {"service": "pilotos-api", "project": "pilotos", "environment": "production", "status": "running", "health": "healthy"},
        {"service": "pilotcore-finance-engine", "project": "pilotcore-finance-engine", "environment": "production", "status": "failed", "health": "failed"},
        {"service": "MongoDB", "project": "pilotcore-sales-engine", "environment": "production", "status": "failed", "health": "failed"},
        {"service": "SpeakGlobal AI", "project": "confident-wholeness", "environment": "production", "status": "unknown", "health": "unknown"},
        {"service": "api", "project": "atlas-trader", "environment": "production", "status": "running", "health": "healthy"},
    ]


def test_summary_counts_correct():
    summary = summarize_health_rows(_rows())
    assert summary["total"] == 5
    assert summary["healthy"] == 2
    assert summary["failed"] == 2
    assert summary["unknown"] == 1


def test_failed_and_unknown_listed_before_full_table():
    body = format_health_report_body(_rows())
    summary_idx = body.index("Summary:")
    needs_idx = body.index("Needs attention:")
    table_idx = body.index("Full inventory:")
    assert summary_idx < needs_idx < table_idx
    assert "pilotcore-finance-engine / production / pilotcore-finance-engine — failed" in body
    assert "confident-wholeness / production / SpeakGlobal AI — unknown" in body
    assert body.index("Needs attention:") < body.index("| pilotos-api |")


def test_compose_report_saves_cache():
    with patch(
        "aethos_core.providers.railway.discovery.discover_railway_inventory",
    ) as discover:
        from aethos_core.provider_discovery.provider_inventory import ProviderInventory

        discover.return_value = ProviderInventory(provider="railway", projects=[], freshness="fresh")
        with patch(
            "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
            return_value=(_rows(), None),
        ):
            compose_railway_provider_wide_health_reply(session_id="summary-cache")
    cached = get_provider_wide_health_report(session_id="summary-cache")
    assert cached is not None
    assert cached["summary"]["failed"] == 2


def test_followup_show_failed_only_uses_last_report_without_refresh():
    save_provider_wide_health_report(
        session_id="followup-failed",
        provider="railway",
        rows=_rows(),
        summary={"total": 5, "healthy": 2, "failed": 2, "unknown": 1},
    )
    with patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
    ) as collect:
        body, intent, meta = compose_provider_wide_health_followup("show only failed", session_id="followup-failed")
        collect.assert_not_called()
    assert meta["from_cache"] == "true"
    assert intent.startswith("operational_response")
    assert "MongoDB" in body
    assert "pilotcore-finance-engine" in body
    assert "pilotos-api" not in body.split("Failed services:")[-1] if "Failed services:" in body else True


def test_followup_which_services_failed_uses_cache():
    save_provider_wide_health_report(
        session_id="followup-which",
        provider="railway",
        rows=_rows(),
        summary={"total": 5, "healthy": 2, "failed": 2, "unknown": 1},
    )
    body, intent, meta = compose_planned_operational_reply("which services failed?", session_id="followup-which")
    assert body is not None
    assert meta.get("from_cache") == "true"
    assert "Failed services:" in body or "failed" in body.lower()


def test_followup_fix_first_ranks_failed_services():
    save_provider_wide_health_report(
        session_id="followup-fix",
        provider="railway",
        rows=_rows(),
        summary={"total": 5, "healthy": 2, "failed": 2, "unknown": 1},
    )
    body, intent, meta = compose_provider_wide_health_followup(
        "what should I fix first?",
        session_id="followup-fix",
    )
    assert intent == "operational_response_fix_priority"
    assert meta["from_cache"] == "true"
    assert "Fix priority:" in body
    failed_pos = body.index("pilotcore-finance-engine")
    unknown_pos = body.index("SpeakGlobal AI")
    assert failed_pos < unknown_pos
