# SPDX-License-Identifier: Apache-2.0
"""Railway restart skill tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.provider_skills.railway.skill import RailwayProviderSkill
from aethos_core.provider_skills.types import ProviderEvidenceBundle
from aethos_core.providers.railway.target_resolver import ProviderTarget


def _target() -> ProviderTarget:
    return ProviderTarget(
        provider="railway",
        service_name="api",
        service_id="svc-api",
        project_name="atlas-trader",
        environment="production",
        resolved=True,
    )


def test_restart_plan_uses_cli_command_when_mode_cli():
    skill = RailwayProviderSkill()
    with patch.object(skill, "execution_mode", return_value="cli"), patch(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        return_value=("token", "env", None),
    ), patch(
        "aethos_core.providers.railway.restart_diagnostics.diagnose_railway_mutation_target",
        return_value=type(
            "D",
            (),
            {
                "ok": True,
                "issues": [],
                "to_dict": lambda self: {"service_id": "svc-api", "deployment_id": "dep-1"},
                "service_id": "svc-api",
                "deployment_id": "dep-1",
            },
        )(),
    ):
        plan = skill.plan(operation="restart", target=_target())
    assert "railway restart" in (plan.command or "")
    assert plan.execution_mode == "cli"


def test_restart_verified_by_log_activity_without_new_deployment():
    skill = RailwayProviderSkill()
    bundle = ProviderEvidenceBundle(
        operation="restart",
        provider="railway",
        target="api",
        approved_at="2026-01-15T12:00:00+00:00",
        command="railway restart --service 'api' --yes --json",
        command_submitted=True,
        execution_mode="cli",
        before={"service_id": "svc-api", "latest_deployment_id": "dep-old", "last_log_at": "2026-01-01T00:00:00+00:00"},
        after={"service_id": "svc-api", "latest_deployment_id": "dep-old", "last_log_at": "2026-01-15T12:05:00+00:00", "service_status": "online"},
        evidence={"log_activity_after_approval": True, "health_confirmed": True, "deployment_transition_detected": False},
    )
    with patch(
        "aethos_core.providers.railway.hardening.restart_transition.verify_railway_restart_transition",
    ) as verify_mock:
        from aethos_core.providers.railway.hardening.restart_transition import RestartVerificationResult, LOG_RESTART_DETECTED

        verify_mock.return_value = RestartVerificationResult(
            state=LOG_RESTART_DETECTED,
            verified=True,
            transition_detected=True,
            service_online=True,
            provider_request_accepted=True,
            summary="log activity",
            before_snapshot=bundle.before,
            after_snapshot=bundle.after,
            restart_command_submitted=True,
            transition_proof="logs",
        )
        result = skill.verify(
            operation="restart",
            before=bundle.before,
            after=bundle.after,
            evidence_bundle=bundle,
            approved_at=bundle.approved_at,
        )
    assert result.status == "verified_restart"
    assert result.verified is True


def test_online_only_does_not_verify_restart():
    skill = RailwayProviderSkill()
    bundle = ProviderEvidenceBundle(
        operation="restart",
        provider="railway",
        target="api",
        approved_at="2026-01-15T12:00:00+00:00",
        command="railway restart --service 'api' --yes --json",
        command_submitted=True,
        execution_mode="cli",
        before={"service_id": "svc-api", "latest_deployment_id": "dep-old"},
        after={"service_id": "svc-api", "latest_deployment_id": "dep-old", "service_status": "online"},
        evidence={"health_confirmed": True, "deployment_transition_detected": False, "log_activity_after_approval": False},
    )
    with patch("aethos_core.providers.railway.hardening.restart_transition.verify_railway_restart_transition") as verify_mock:
        from aethos_core.providers.railway.hardening.restart_transition import RestartVerificationResult, SERVICE_ONLINE_BUT_RESTART_UNPROVEN

        verify_mock.return_value = RestartVerificationResult(
            state=SERVICE_ONLINE_BUT_RESTART_UNPROVEN,
            verified=False,
            transition_detected=False,
            service_online=True,
            provider_request_accepted=True,
            summary="online only",
            before_snapshot=bundle.before,
            after_snapshot=bundle.after,
            restart_command_submitted=True,
        )
        result = skill.verify(operation="restart", before=bundle.before, after=bundle.after, evidence_bundle=bundle)
    assert result.verified is False


def test_cli_restart_submitted_via_executor():
    from aethos_core.providers.railway.cli_executor import cli_command_submitted

    assert cli_command_submitted({"ok": True, "stdout": '{"success": true}', "parsed": {"success": True}}) is True
    assert cli_command_submitted({"ok": True, "stdout": "", "parsed": None}) is False
