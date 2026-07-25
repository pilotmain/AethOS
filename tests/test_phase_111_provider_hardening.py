# SPDX-License-Identifier: Apache-2.0
"""Phase 11.1 — Tier 1 provider hardening tests."""

from __future__ import annotations

from aethos_core.provider_hardening.verify import tier1_provider_reliability, verify_provider_mutation
from aethos_core.providers.github.hardening.rerun_integrity import verify_github_rerun
from aethos_core.providers.railway.hardening.restart_runtime import verify_railway_restart
from aethos_core.providers.vercel.hardening.deployment_verification import verify_vercel_deployment
from aethos_core.recovery_runtime.recovery_storytelling import build_recovery_story
from aethos_core.reality_harness.scenarios import list_reality_scenarios


def test_railway_restart_verification_full():
    approved_at = "2026-01-15T12:00:00+00:00"
    before = {
        "service_id": "svc-1",
        "active_deployment_id": "dep-old",
        "active_deployment_created_at": "2026-01-01T00:00:00+00:00",
        "latest_deployment_id": "dep-old",
        "latest_deployment_status": "running",
        "captured_at": approved_at,
    }
    after = {
        "service_id": "svc-1",
        "active_deployment_id": "dep-new",
        "active_deployment_created_at": "2026-01-15T12:05:00+00:00",
        "latest_deployment_id": "dep-new",
        "latest_deployment_status": "success",
        "captured_at": "2026-01-15T12:06:00+00:00",
    }
    result = verify_railway_restart(
        provider_result={
            "restart_command_submitted": True,
            "ok": True,
            "service_id": "svc-1",
            "deployment_state_before": "running",
            "deployment_state_after": "success",
            "deployment_id": "dep-new",
            "rollback_metadata": {
                "deployment_snapshot_before": before,
                "deployment_snapshot_after": after,
                "approved_at": approved_at,
            },
        },
        readonly_artifact={"summary": "Deployment running and healthy", "browser_evidence": True},
        before_snapshot=before,
        approved_at=approved_at,
    )
    assert result["verified"] is True
    assert result["transition_detected"] is True
    assert result["maturity"] == "stable"
    assert "transition" in result["summary"].lower()
    assert "Extended monitoring" in result["summary"]


def test_github_rerun_verification():
    result = verify_github_rerun(
        provider_result={"conclusion": "success", "run_id": "123"},
        readonly_artifact={"summary": "Workflow completed successfully"},
    )
    assert result["verified"] is True
    assert result["maturity"] == "stable"
    assert "Workflow rerun completed successfully" in result["summary"]


def test_vercel_deployment_verification():
    result = verify_vercel_deployment(
        provider_result={"ok": True, "url": "https://example.vercel.app", "browser_verified": True},
        readonly_artifact={"summary": "Production ready", "browser_evidence": True},
    )
    assert result["verified"] is True
    assert "production endpoint reachable" in result["summary"].lower()


def test_provider_hardening_dispatch():
    railway = verify_provider_mutation(
        provider="railway",
        operation_type="restart",
        provider_result={"deployment_state_after": "success", "rollback_metadata": {}},
        readonly_artifact={"summary": "running healthy"},
    )
    assert railway["provider"] == "railway"
    github = verify_provider_mutation(provider="github", operation_type="workflow_rerun", provider_result={"conclusion": "success"})
    assert github["provider"] == "github"


def test_tier1_provider_reliability():
    providers = tier1_provider_reliability()
    assert len(providers) == 3
    assert all(p["maturity"] == "stable" for p in providers)
    assert providers[0]["verification_coverage_pct"] >= 84


def test_recovery_storytelling_no_premature_resolution():
    story = build_recovery_story(resolved=False, extended_monitoring=True, recovery_confidence=0.72)
    assert "extended monitoring remains active" in story
    assert "Issue resolved" not in story


def test_reality_harness_v2_scenarios():
    scenarios = list_reality_scenarios()
    assert any(s["id"] == "mutation_timeout" for s in scenarios)
    assert any(s["harness_version"] == "2.0" for s in scenarios)
    railway = next(s for s in scenarios if s["id"] == "railway_restart")
    assert railway["coverage_pct"] >= 84


def test_mutation_reconciliation():
    from aethos_core.reconciliation.mutation_reconciliation import reconcile_mutation
    from aethos_core.runtime.jobs import job_store

    job_store._jobs.clear()
    job_store._events.clear()
    job = job_store.create(
        title="Railway restart mutation",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "mutation_execution": {
                "provider_result": {
                    "deployment_state_after": "success",
                    "rollback_metadata": {"deployment_state_before": "running", "deployment_state_after": "success"},
                }
            },
        },
    )
    result = reconcile_mutation(
        mutation_job_id=job.id,
        readonly_artifact={"summary": "healthy", "browser_evidence": True},
    )
    assert result["ok"] is True
    assert result["provider"] == "railway"
    assert "principle" in result


def test_assess_recovery_state():
    from aethos_core.recovery_runtime.runtime import assess_recovery_state
    from aethos_core.runtime.jobs import job_store

    job_store._jobs.clear()
    job_store._events.clear()
    job = job_store.create(
        title="GitHub rerun mutation",
        job_type="mutation_execution",
        params={
            "provider": "github",
            "operation_type": "workflow_rerun",
            "mutation_execution": {"provider_result": {"conclusion": "success"}},
        },
    )
    state = assess_recovery_state(mutation_job_id=job.id)
    assert state["ok"] is True
    assert "extended monitoring remains active" in state["narrative"].lower()
    assert "Issue resolved" not in state["narrative"]
