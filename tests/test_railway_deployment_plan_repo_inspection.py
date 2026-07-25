# SPDX-License-Identifier: Apache-2.0
"""FIX 94 — Railway deployment plan repo inspection and completion."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests,
    get_deployment_plan_context,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.plan_completion import (
    assess_plan_completion,
    merge_inspection_into_plan,
    render_plan_completion_artifact,
)
from aethos_core.providers.railway.deployment_plan.repo_inspection import (
    extract_env_var_names_from_text,
    infer_deployment_fields_from_files,
    inspect_github_repo_for_deployment,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_router import (
    route_railway_new_service_plan,
)


def setup_function() -> None:
    clear_for_tests()


def test_python_repo_inferred() -> None:
    fields = infer_deployment_fields_from_files(
        root_files=["requirements.txt", "Procfile", "README.md"],
        file_contents={
            "requirements.txt": "fastapi\nuvicorn\n",
            "Procfile": "web: uvicorn main:app --host 0.0.0.0 --port $PORT",
        },
    )
    assert fields["runtime"] == "Python"
    assert "pip install" in fields["build_command"]
    assert "uvicorn" in fields["start_command"]
    assert fields["start_command"] != "unknown"


def test_node_repo_inferred() -> None:
    fields = infer_deployment_fields_from_files(
        root_files=["package.json"],
        file_contents={
            "package.json": '{"name":"aethos-api","scripts":{"build":"tsc","start":"node dist/index.js"}}',
        },
    )
    assert fields["runtime"] == "Node"
    assert "npm" in fields["build_command"]
    assert fields["start_command"] == "npm start"
    assert fields["service_name_confidence"] == "medium"


def test_dockerfile_inferred() -> None:
    fields = infer_deployment_fields_from_files(
        root_files=["Dockerfile"],
        file_contents={"Dockerfile": "FROM python:3.12\nCMD uvicorn app:app --host 0.0.0.0 --port 8000\n"},
    )
    assert fields["runtime"] == "Docker"
    assert fields["build_command"] == "docker build ."
    assert "uvicorn" in fields["start_command"]


def test_env_var_names_extracted_without_values() -> None:
    names = extract_env_var_names_from_text(
        "# example\nDATABASE_URL=postgres://secret\nRAILWAY_API_TOKEN=abc\nPORT=8080\n"
    )
    assert "DATABASE_URL" in names
    assert "RAILWAY_API_TOKEN" in names
    assert "PORT" in names
    assert not any("postgres" in name for name in names)
    artifact = render_plan_completion_artifact(
        {"deployment_readiness": "incomplete", "missing_fields": ["Runtime"]},
        inspection={
            "ok": True,
            "fields": {"required_env_var_names": names, "runtime": "Python"},
        },
    )
    assert "DATABASE_URL" in artifact
    assert "postgres://" not in artifact


def test_unknown_remains_explicit() -> None:
    fields = infer_deployment_fields_from_files(root_files=["README.md"], file_contents={"README.md": "# hello"})
    assert fields["runtime"] == "unknown"
    assert fields["build_command"] == "unknown"
    assert fields["start_command"] == "unknown"


def test_merge_inspection_updates_plan() -> None:
    plan = {
        "repo": "pilotmain/aethos",
        "branch": "main",
        "project": "pilotos",
        "environment": "production",
        "service_name": "aethos-api",
    }
    inspection = {
        "ok": True,
        "repository": "pilotmain/aethos",
        "branch": "main",
        "fields": {
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/health",
            "required_env_var_names": ["PORT"],
            "service_name_confidence": "low",
        },
    }
    updated = merge_inspection_into_plan(plan, inspection=inspection)
    assert updated["runtime"] == "Python"
    assert updated["required_env_var_names"] == ["PORT"]
    status, missing = assess_plan_completion(updated)
    assert status == "complete"
    assert missing == []


@patch("aethos_core.providers.railway.deployment_plan.plan_completion.inspect_github_repo_for_deployment")
def test_complete_plan_route(mock_inspect) -> None:
    mock_inspect.return_value = {
        "ok": True,
        "repository": "pilotmain/aethos",
        "branch": "main",
        "fields": {
            "runtime": "Node",
            "build_command": "npm ci",
            "start_command": "npm start",
            "health_check_path": "/healthz",
            "required_env_var_names": ["PORT"],
            "service_name_confidence": "medium",
        },
    }
    save_deployment_plan_context(
        session_id="fix-94",
        plan={
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "production",
            "service_name": "aethos-api",
        },
    )
    result = route_railway_new_service_plan(
        "complete the railway deployment plan",
        session_id="fix-94",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_deployment_plan_complete"
    assert "# Railway Deployment Plan Completion" in body
    assert "Runtime: Node" in body
    assert "No mutation has been performed." in body
    assert meta.get("mutation_performed") == "false"
    stored = get_deployment_plan_context(session_id="fix-94")
    assert stored is not None
    assert stored.get("runtime") == "Node"
    mock_inspect.assert_called_once()


@patch("aethos_core.providers.railway.deployment_plan.repo_inspection.request_github")
@patch("aethos_core.credentials.get_provider_api_token")
def test_inspect_github_repo_lists_root(mock_token, mock_github) -> None:
    mock_token.return_value = "gh-test"

    def _github(_token: str, method: str, path: str, **kwargs: object) -> dict:
        if path.endswith("/contents/"):
            return {
                "ok": True,
                "data": [{"type": "file", "name": "package.json"}],
            }
        if path.endswith("/contents/package.json"):
            return {
                "ok": True,
                "data": {"type": "file", "content": "eyJuYW1lIjoiYSJ9", "encoding": "base64"},
            }
        return {"ok": False}

    mock_github.side_effect = _github
    out = inspect_github_repo_for_deployment(repository="pilotmain/aethos", branch="main")
    assert out.get("ok") is True
    assert "package.json" in (out.get("files_inspected") or [])
