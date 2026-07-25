# SPDX-License-Identifier: Apache-2.0
"""Phase 9.3C — contract tests for remaining read-only execution manual gates."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aethos_core.operations.intents import infer_operation_preflight_intent
from aethos_core.operations.preflight_execution import approve_preflight_readonly_execution
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import JobStatus, job_store


GATE_CASES = [
    {
        "prompt": "show domains for invoicepilot",
        "job_type": "operation_preflight",
        "operation_type": "list_domains",
        "target": "invoicepilot",
        "approved_actions": ["vercel_api_domains"],
        "adapter_method": "get_domains",
        "adapter_return": {
            "ok": True,
            "source": "provider_api",
            "domains": [
                {
                    "domain": "invoicepilot.com",
                    "verified": True,
                    "production": True,
                },
                {
                    "domain": "invoicepilot.vercel.app",
                    "verified": True,
                    "production": False,
                },
            ],
            "output": "Project: invoicepilot\nDomains (2):",
        },
        "report_contains": ["invoicepilot.com", "Provider API execution", "No mutation performed"],
        "evidence_type": "domain_record",
    },
    {
        "prompt": "show deployments for quotepilot",
        "job_type": "operation_preflight",
        "operation_type": "list_deployments",
        "target": "quotepilot",
        "approved_actions": ["vercel_api_deployments", "url_reachability"],
        "adapter_method": "get_deployments",
        "adapter_return": {
            "ok": True,
            "source": "provider_api",
            "project_id": "prj_q",
            "deployments": [
                {
                    "id": "dpl_ready1",
                    "state": "ready",
                    "target": "production",
                    "branch": "main",
                    "commit": "abc123",
                    "created_at": 1_714_000_000_000,
                },
                {
                    "id": "dpl_fail1",
                    "state": "error",
                    "target": "preview",
                    "branch": "feat/x",
                    "commit": "def456",
                    "error_message": "Build failed",
                    "created_at": 1_713_900_000_000,
                },
            ],
            "output": "Project: quotepilot",
        },
        "report_contains": ["dpl_ready1", "production", "Provider API execution"],
        "evidence_type": "deployment_state",
    },
    {
        "prompt": "show project details for lifeos",
        "job_type": "operation_preflight",
        "operation_type": "project_details",
        "target": "lifeos",
        "approved_actions": ["vercel_api_project_details"],
        "adapter_method": "get_project_details",
        "adapter_return": {
            "ok": True,
            "source": "provider_api",
            "details": {
                "framework": "nextjs",
                "repo_link": "org/lifeos",
                "production_url": "lifeos.vercel.app",
                "production_branch": "main",
                "build_command": "npm run build",
            },
            "output": "Project: lifeos\n- Framework: nextjs",
        },
        "report_contains": ["nextjs", "org/lifeos", "Vercel API token"],
        "evidence_type": "project_metadata",
    },
]


@pytest.mark.parametrize("gate", GATE_CASES, ids=[g["operation_type"] for g in GATE_CASES])
def test_gate_intent_routes_to_operational_preflight(gate):
    intent = infer_operation_preflight_intent(gate["prompt"])
    assert intent is not None
    _title, job_type, params = intent
    assert job_type == gate["job_type"]
    assert params["operation_type"] == gate["operation_type"]
    assert gate["target"] in params.get("target_hints", [])


@pytest.mark.parametrize("gate", GATE_CASES, ids=[g["operation_type"] for g in GATE_CASES])
def test_gate_approve_to_execution_produces_api_artifact(gate):
    adapter = MagicMock()
    getattr(adapter, gate["adapter_method"]).return_value = gate["adapter_return"]

    job_store.clear_for_tests()
    job_executor.drain_queue_for_tests()
    try:
        preflight = job_store.create(
            title=f"Preflight — {gate['operation_type']}",
            job_type=gate["job_type"],
            params={
                "user_request": gate["prompt"],
                "provider": "vercel",
                "operation_type": gate["operation_type"],
                "target_hints": [gate["target"]],
            },
            auto_run=False,
        )
        from aethos_core.operations.preflight import run_operation_preflight

        outcome = run_operation_preflight(job_type=preflight.job_type, params=preflight.params)
        pf_dict = outcome.preflight.to_dict()
        pf_dict["target_name"] = gate["target"]
        pf_dict["target_status"] = "resolved"
        pf_dict["preflight_status"] = "ready_for_approval"
        preflight.params["operation_preflight"] = pf_dict
        preflight.params["preflight_status"] = "ready_for_approval"
        preflight.params["is_current"] = True
        preflight.status = JobStatus.COMPLETED

        with patch(
            "aethos_core.providers.vercel.auth.VercelAuthAdapter.resolve_best_auth_method",
            return_value={"method": "api_token", "credential_id": "cred-1"},
        ), patch(
            "aethos_core.operations.execution.execution_runner._resolve_vercel_adapter",
            return_value=(adapter, "api_token", "Vercel API token", "cred-1"),
        ), patch(
            "aethos_core.operations.execution.execution_runner.merge_project_state",
            return_value={"production_url": f"https://{gate['target']}.vercel.app"},
        ), patch(
            "aethos_core.operations.execution.execution_runner._url_reachability",
            return_value={"url": f"https://{gate['target']}.vercel.app", "reachable": True, "summary": "HTTP 200"},
        ), patch(
            "aethos_core.operations.execution.execution_runner.should_attempt_browser_fallback",
            return_value=False,
        ):
            _, execution = approve_preflight_readonly_execution(preflight.id)
            assert execution.job_type == "readonly_execution"
            job_executor._execute_one(execution.id)

        done = job_store.get(execution.id)
        assert done is not None
        assert done.status == JobStatus.COMPLETED, done.failure_reason
        assert done.params.get("readonly_execution")
        assert done.params.get("data_source") == "provider_api"
        assert done.params.get("browser_used") is False

        report = done.full_result or ""
        for snippet in gate["report_contains"]:
            assert snippet in report, f"missing {snippet!r} in report"

        artifact = done.params["readonly_execution"]
        evidence = artifact.get("evidence") or []
        assert any(e.get("type") == gate["evidence_type"] for e in evidence if isinstance(e, dict))

        events = job_store.list_events(job_ids=[execution.id])
        assert "job_completed" in [e["event_type"] for e in events]
    finally:
        job_store.clear_for_tests()
        job_executor.drain_queue_for_tests()
