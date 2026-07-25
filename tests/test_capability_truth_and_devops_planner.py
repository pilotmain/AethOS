# SPDX-License-Identifier: Apache-2.0
"""Fix 57 — capability truthfulness and DevOps plan-first routing."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from aethos_core.chat.explicit_mutation_intent import compose_explicit_mutation_preflight_reply
from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.devops_intent_planner.devops_capability_router import route_devops_capability_question
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    job_store.clear_for_tests()
    yield
    job_store.clear_for_tests()


@contextmanager
def _resolved_railway_gate(*, service: str = "pilotos-api", project: str = "pilotos"):
    def _gate(text, params, operation_type):
        enriched = {
            **params,
            "target_name": service,
            "target_resolved": True,
            "target": {
                "project_name": project,
                "environment": "production",
                "service_name": service,
                "resolved": True,
            },
        }
        return enriched, None

    binding = type("Binding", (), {"ok": True, "stored_github_repo": "", "referenced_github_repo": ""})()
    # Patch the consumer's namespace too: mutation_preflight_prompts imports the gate
    # by value (`from ... import gate_railway_mutation_preflight`), so patching only
    # the source module would leave the real gate running in that path.
    # The preflight flow has a second resolution step after the gate
    # (apply_target_resolution_to_params); with the target already resolved there's
    # nothing more to clarify, so pass params through with no resolution issue.
    with patch("aethos_core.chat.mutation_target_chat.gate_railway_mutation_preflight", side_effect=_gate), patch(
        "aethos_core.chat.mutation_preflight_prompts.gate_railway_mutation_preflight", side_effect=_gate
    ), patch(
        "aethos_core.deployment_targets.mutation_resolver.apply_target_resolution_to_params",
        side_effect=lambda params, **_kw: (params, None),
    ), patch(
        "aethos_core.provider_topology.binding_verifier.verify_source_binding",
        return_value=binding,
    ):
        yield


def test_capability_question_does_not_overclaim_aws_azure_gcp() -> None:
    result = route_devops_capability_question("which cloud env can you work end to end today?")
    assert result is not None
    body = result.reply
    assert "Railway is the most complete" in body
    assert "stub" in body.lower() or "planned" in body.lower()
    assert "AWS" in body
    assert "GCP" in body
    assert "Azure" in body
    assert "full end-to-end AWS" not in body
    assert "No mutation has been performed." in body


def test_end_to_end_devops_request_returns_plan_first() -> None:
    prompt = "can you push to github, deploy, create env vars, and check E2E?"
    result = route_devops_capability_question(prompt, session_id="fix57-plan")
    assert result is not None
    assert result.intent == "devops_end_to_end_plan"
    body = result.reply
    assert "governed" in body.lower()
    assert "GitHub" in body
    assert "Identify the local repo path" in body
    assert "Execute only after explicit approval" in body
    assert "No mutation has been performed." in body


def test_no_mutation_preflight_until_target_provider_clarified() -> None:
    prompt = "can you push to github, deploy, create env vars, and check E2E?"
    blocked = create_mutation_preflight_job_reply(prompt, session_id="fix57-block")
    assert blocked is None
    explicit = compose_explicit_mutation_preflight_reply(prompt, session_id="fix57-block")
    assert explicit is None

    result = resolve_chat_turn(prompt, session_id="fix57-block", apply_relational_layer=False)
    assert result.meta.get("route_id") == "devops_capability"
    jobs = [job for job in job_store.list_all() if job.session_id == "fix57-block"]
    assert not any(job.job_type == "mutation_preflight" for job in jobs)


def test_configured_railway_path_can_proceed_to_governed_preflight() -> None:
    with _resolved_railway_gate():
        reply = compose_explicit_mutation_preflight_reply(
            "restart the railway pilotos-api",
            session_id="fix57-railway",
        )
    assert reply is not None
    body, intent, meta = reply
    assert intent == "mutation_preflight_job_created"
    assert "preflight" in body.lower()
    assert meta.get("proposed_job_id") or meta.get("operation_type") == "restart"


def test_unimplemented_provider_returns_honest_capability_gap() -> None:
    prompt = "can you deploy this repo to AWS end to end?"
    result = route_devops_capability_question(prompt, session_id="fix57-aws")
    assert result is not None
    body = result.reply
    assert "AWS" in body
    assert "not a fully wired execution path" in body.lower() or "stub" in body.lower()
    assert "No mutation has been performed." in body
    assert create_mutation_preflight_job_reply(prompt, session_id="fix57-aws") is None
