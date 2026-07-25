# SPDX-License-Identifier: Apache-2.0
"""Railway restart transition verification tests."""

from __future__ import annotations

from aethos_core.providers.railway.hardening.restart_transition import (
    RESTART_REQUESTED,
    RESTART_TRANSITION_DETECTED,
    RESTART_UNVERIFIED,
    SERVICE_ONLINE_BUT_RESTART_UNPROVEN,
    STABILIZING,
    VERIFICATION_FAILED,
    verify_railway_restart_transition,
)
from aethos_core.providers.railway.hardening.restart_runtime import verify_railway_restart
from aethos_core.verification.orchestration.resolve import _railway_verification_evidence


APPROVED_AT = "2026-01-15T12:00:00+00:00"
SERVICE_ID = "svc-123"


def _before(dep_id: str = "dep-old", created_at: str = "2026-01-01T00:00:00+00:00") -> dict:
    return {
        "service_id": SERVICE_ID,
        "active_deployment_id": dep_id,
        "active_deployment_created_at": created_at,
        "latest_deployment_id": dep_id,
        "latest_deployment_status": "running",
        "captured_at": APPROVED_AT,
    }


def _after(
    dep_id: str = "dep-new",
    created_at: str = "2026-01-15T12:05:00+00:00",
    status: str = "success",
) -> dict:
    return {
        "service_id": SERVICE_ID,
        "active_deployment_id": dep_id,
        "active_deployment_created_at": created_at,
        "latest_deployment_id": dep_id,
        "latest_deployment_status": status,
        "captured_at": "2026-01-15T12:06:00+00:00",
    }


def test_same_deployment_id_after_approval_is_restart_unverified():
    before = _before()
    after = _after(dep_id="dep-old", created_at="2026-01-01T00:00:00+00:00")
    result = verify_railway_restart_transition(
        service_id=SERVICE_ID,
        before_snapshot=before,
        approved_at=APPROVED_AT,
        after_snapshot=after,
        provider_result={
            "restart_command_submitted": True,
            "ok": True,
            "service_id": SERVICE_ID,
        },
        readonly_artifact={},
        provider_request_accepted=True,
    )
    assert result.state == RESTART_UNVERIFIED
    assert result.verified is False
    assert result.transition_detected is False


def test_deployment_timestamp_older_than_approval_is_restart_unverified():
    before = _before()
    after = _after(dep_id="dep-old", created_at="2026-01-01T00:00:00+00:00")
    result = verify_railway_restart_transition(
        service_id=SERVICE_ID,
        before_snapshot=before,
        approved_at=APPROVED_AT,
        after_snapshot=after,
        provider_result={"ok": True},
        readonly_artifact={},
        provider_request_accepted=True,
    )
    assert result.state == RESTART_UNVERIFIED
    assert result.final_verification == "unverified"


def test_new_deployment_id_after_approval_is_verified_when_online():
    before = _before()
    after = _after(dep_id="dep-new", created_at="2026-01-15T12:05:00+00:00")
    result = verify_railway_restart_transition(
        service_id=SERVICE_ID,
        before_snapshot=before,
        approved_at=APPROVED_AT,
        after_snapshot=after,
        provider_result={
            "restart_command_submitted": True,
            "ok": True,
            "service_id": SERVICE_ID,
        },
        readonly_artifact={"summary": "Deployment running and healthy"},
        provider_request_accepted=True,
    )
    assert result.state == RESTART_TRANSITION_DETECTED
    assert result.verified is True
    assert result.transition_detected is True
    assert result.final_verification == "verified"


def test_service_online_but_no_transition_is_unproven():
    before = _before()
    after = _after(dep_id="dep-old", created_at="2026-01-01T00:00:00+00:00", status="running")
    result = verify_railway_restart_transition(
        service_id=SERVICE_ID,
        before_snapshot=before,
        approved_at=APPROVED_AT,
        after_snapshot=after,
        provider_result={"ok": True},
        readonly_artifact={"summary": "Deployment running and healthy"},
        provider_request_accepted=True,
    )
    assert result.state == SERVICE_ONLINE_BUT_RESTART_UNPROVEN
    assert result.verified is False
    assert result.service_online is True
    assert result.restart_transition == "not_detected"


def test_provider_accepted_but_transition_pending_is_stabilizing():
    before = _before()
    result = verify_railway_restart_transition(
        service_id=SERVICE_ID,
        before_snapshot=before,
        approved_at=APPROVED_AT,
        after_snapshot=None,
        provider_result={"ok": True},
        readonly_artifact={},
        provider_request_accepted=True,
    )
    assert result.state == STABILIZING
    assert result.verified is False
    assert result.provider_request == "accepted"


def test_provider_api_unavailable_is_verification_failed():
    before = _before()
    result = verify_railway_restart_transition(
        service_id=SERVICE_ID,
        before_snapshot=before,
        approved_at=APPROVED_AT,
        after_snapshot=None,
        provider_result={"ok": False, "detail": "provider unavailable"},
        readonly_artifact={},
        provider_request_accepted=False,
    )
    assert result.state == VERIFICATION_FAILED
    assert result.final_verification == "failed"


def test_restart_runtime_never_verifies_from_health_alone():
    before = _before()
    after = _after(dep_id="dep-old", created_at="2026-01-01T00:00:00+00:00", status="running")
    result = verify_railway_restart(
        provider_result={
            "restart_command_submitted": True,
            "ok": True,
            "service_id": SERVICE_ID,
            "rollback_metadata": {
                "deployment_snapshot_before": before,
                "deployment_snapshot_after": after,
                "approved_at": APPROVED_AT,
            },
        },
        readonly_artifact={"summary": "Deployment running and healthy", "browser_evidence": True},
        before_snapshot=before,
        approved_at=APPROVED_AT,
    )
    assert result["verified"] is False
    assert result["transition_detected"] is False
    assert result["restart_verification"]["state"] == SERVICE_ONLINE_BUT_RESTART_UNPROVEN


def test_resolve_railway_verification_uses_transition_not_health():
    before = _before()
    after = _after(dep_id="dep-old", created_at="2026-01-01T00:00:00+00:00", status="running")
    verification_result, extra = _railway_verification_evidence(
        {"summary": "Deployment running and healthy"},
        source_exec={
            "provider_result": {
                "restart_command_submitted": True,
                "ok": True,
                "service_id": SERVICE_ID,
                "rollback_metadata": {
                    "deployment_snapshot_before": before,
                    "deployment_snapshot_after": after,
                    "approved_at": APPROVED_AT,
                },
            },
            "provider_mutation_requested": True,
        },
        mutation_params={
            "railway_before_snapshot": before,
            "mutation_execution_approved_at_iso": APPROVED_AT,
        },
    )
    assert verification_result == "inconclusive"
    assert extra["restart_verification_state"] == SERVICE_ONLINE_BUT_RESTART_UNPROVEN
    assert extra["verified"] is False
    assert extra["final_verification"] == "unverified"


def test_resolve_railway_verification_marks_verified_on_transition():
    before = _before()
    after = _after()
    verification_result, extra = _railway_verification_evidence(
        {"summary": "Deployment running and healthy"},
        source_exec={
            "provider_result": {
                "restart_command_submitted": True,
                "ok": True,
                "service_id": SERVICE_ID,
                "rollback_metadata": {
                    "deployment_snapshot_before": before,
                    "deployment_snapshot_after": after,
                    "approved_at": APPROVED_AT,
                },
            },
        },
        mutation_params={
            "railway_before_snapshot": before,
            "mutation_execution_approved_at_iso": APPROVED_AT,
        },
    )
    assert verification_result == "healthy"
    assert extra["restart_verification_state"] == RESTART_TRANSITION_DETECTED
    assert extra["verified"] is True


def test_provider_accepted_without_after_snapshot_maps_to_pending():
    before = _before()
    verification_result, extra = _railway_verification_evidence(
        {},
        source_exec={"provider_result": {"restart_command_submitted": True, "ok": True, "service_id": SERVICE_ID}},
        mutation_params={
            "railway_before_snapshot": before,
            "mutation_execution_approved_at_iso": APPROVED_AT,
        },
    )
    assert verification_result == "pending"
    assert extra["restart_verification_state"] in {STABILIZING, RESTART_REQUESTED}
