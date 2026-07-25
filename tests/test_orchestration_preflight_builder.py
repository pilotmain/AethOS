# SPDX-License-Identifier: Apache-2.0

import aethos_core.providers  # noqa: F401
from aethos_core.operations.github_preflight import build_github_preflight
from aethos_core.operations.orchestration.preflight_builder import (
    GITHUB_PREFLIGHT_PROFILE,
    RAILWAY_PREFLIGHT_PROFILE,
    build_ambiguous_target_preflight,
)
from aethos_core.operations.railway_preflight import build_railway_preflight
from aethos_core.operations.target_resolution import TargetResolution


def test_shared_ambiguous_preflight_preserves_provider_semantics():
    resolution = TargetResolution(status="ambiguous", matches=["a", "b"])
    railway = build_ambiguous_target_preflight(
        RAILWAY_PREFLIGHT_PROFILE, operation_type="list_deployments", resolution=resolution
    )
    github = build_ambiguous_target_preflight(
        GITHUB_PREFLIGHT_PROFILE, operation_type="workflow_runs", resolution=resolution
    )
    assert railway.provider == "railway"
    assert github.provider == "github"
    assert "Railway service" in railway.proposed_steps[0]
    assert "GitHub repository" in github.proposed_steps[0]


def test_railway_preflight_uses_shared_builder_for_resolved_target():
    preflight = build_railway_preflight(
        operation_type="list_deployments",
        resolution=TargetResolution(status="resolved", target_name="speakglobal-ai"),
        user_request="show railway deployments for speakglobal-ai",
    )
    assert preflight.provider == "railway"
    assert preflight.target_name == "speakglobal-ai"
    assert preflight.next_action == "approve_readonly_execution"
    assert any("Railway API" in step for step in preflight.proposed_steps)


def test_github_workflow_diagnostic_steps_preserved():
    preflight = build_github_preflight(
        operation_type="workflow_diagnostic",
        resolution=TargetResolution(status="resolved", target_name="pilotmain/AethOS"),
        user_request="why did the AethOS workflow fail",
    )
    assert preflight.provider == "github"
    assert any("failed workflow runs" in step.lower() for step in preflight.proposed_steps)
    assert any("diagnostic" in step.lower() for step in preflight.proposed_steps)
