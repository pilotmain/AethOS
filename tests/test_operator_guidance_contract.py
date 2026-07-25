# SPDX-License-Identifier: Apache-2.0
"""Standard blocked-state response contract: opinionated I-do/you-do + verified nav paths."""

from __future__ import annotations

from aethos_core.mission_control.visible_navigation_registry import operator_surface
from aethos_core.operator_guidance import OperatorStep, compose_operator_guidance


def test_operator_surface_resolves_to_real_labels():
    assert operator_surface("credentials") == "Mission Control → Advanced settings → Credentials"
    assert operator_surface("connections") == "Mission Control → Advanced settings → Credentials"
    assert operator_surface("approvals") == "Mission Control → Approvals"
    assert operator_surface("jobs") == "Mission Control → Jobs"
    assert operator_surface("providers") == "Mission Control → Providers"
    assert operator_surface("canvas") == "Canvas tab"


def test_operator_surface_sanitizes_unknown_freeform():
    # A free-form wrong label still gets rewritten (defense-in-depth) to the real Flat label.
    assert "Credentials" in operator_surface("Mission Control → Connections")
    assert "Jobs" in operator_surface("Mission Control → Tracked Work")


def test_contract_has_all_four_parts():
    out = compose_operator_guidance(
        headline="Deploy blocked — secrets needed",
        what_happened="I resolved 11 of 13 env vars; 2 are secrets I can't see.",
        aethos_can_do=["Create the service and deploy automatically once values are in."],
        you_must_do=[
            OperatorStep(action="Paste the 2 missing values", surface="credentials", why="only you hold them")
        ],
        safe_next_command="deploy to Railway staging",
    )
    assert "**Deploy blocked — secrets needed**" in out
    assert "What I can do for you:" in out
    assert "What needs you (only you can do this):" in out
    assert "Mission Control → Advanced settings → Credentials" in out  # resolved from key, not hand-typed
    assert "only you hold them" in out
    assert "**Safe next command:** `deploy to Railway staging`" in out


def test_contract_omits_empty_sections():
    out = compose_operator_guidance(
        headline="Rate limited",
        what_happened="Railway is throttling; your token is fine.",
        safe_next_command="retry shortly",
    )
    assert "What I can do for you:" not in out
    assert "What needs you" not in out
    assert "Rate limited" in out


def test_env_var_blocker_uses_contract():
    from aethos_core.providers.railway.env_value_readiness.deployment_env_guidance import (
        DeploymentEnvAssessment,
        DeploymentEnvVarStatus,
        compose_deployment_env_block_report,
    )

    assessment = DeploymentEnvAssessment(
        target_key="pilotos/staging/killit-api",
        repo="pilotmain/killit",
        project="pilotos",
        environment="staging",
        service_name="killit-api",
        required=[DeploymentEnvVarStatus(name="STRIPE_SECRET_KEY", purpose="Stripe", resolved=False)],
        missing_names=["STRIPE_SECRET_KEY"],
        resolved_names=["ANTHROPIC_API_KEY"],
        credential_center_path="Mission Control → Advanced settings → Credentials",
    )
    summary, _full = compose_deployment_env_block_report(assessment)
    assert "What needs you" in summary
    assert "Mission Control → Advanced settings → Credentials" in summary
    assert "What I can do for you:" in summary
