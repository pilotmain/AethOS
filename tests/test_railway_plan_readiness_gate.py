# SPDX-License-Identifier: Apache-2.0
"""FIX 95 — Railway plan readiness gate and start-command inference."""

from __future__ import annotations

from aethos_core.providers.railway.deployment_plan.env_var_summary import (
    categorize_env_var_names,
    format_env_var_section_lines,
)
from aethos_core.providers.railway.deployment_plan.plan_completion import merge_inspection_into_plan
from aethos_core.providers.railway.deployment_plan.plan_readiness_gate import assess_mutation_readiness_gate
from aethos_core.providers.railway.deployment_plan.repo_inspection import (
    infer_deployment_fields_from_files,
    is_health_probe_command,
)


def test_health_probe_not_used_as_start_command() -> None:
    probe = "curl -f http://127.0.0.1:8010/api/v1/health || exit 1"
    assert is_health_probe_command(probe)
    fields = infer_deployment_fields_from_files(
        root_files=["Dockerfile"],
        file_contents={
            "Dockerfile": (
                "FROM python:3.12\n"
                "HEALTHCHECK CMD curl -f http://127.0.0.1:8010/api/v1/health || exit 1\n"
                "CMD uvicorn app.main:app --host 0.0.0.0 --port 8010\n"
            ),
        },
    )
    assert fields["start_command"] == "uvicorn app.main:app --host 0.0.0.0 --port 8010"
    assert "/api/v1/health" in str(fields["health_check_path"])


def test_uvicorn_inferred_correctly() -> None:
    fields = infer_deployment_fields_from_files(
        root_files=["requirements.txt"],
        file_contents={"requirements.txt": "fastapi\nuvicorn\n"},
    )
    assert fields["runtime"] == "Python"
    assert "uvicorn" in fields["start_command"]


def test_procfile_inferred_correctly() -> None:
    fields = infer_deployment_fields_from_files(
        root_files=["Procfile"],
        file_contents={"Procfile": "web: gunicorn wsgi:app --bind 0.0.0.0:$PORT"},
    )
    assert fields["start_command"] == "gunicorn wsgi:app --bind 0.0.0.0:$PORT"


def test_docker_cmd_inferred_correctly() -> None:
    fields = infer_deployment_fields_from_files(
        root_files=["Dockerfile"],
        file_contents={"Dockerfile": 'FROM node:20\nCMD ["node", "dist/server.js"]\n'},
    )
    assert fields["start_command"] == "node dist/server.js"


def test_readiness_incomplete_when_start_command_unknown() -> None:
    plan = {
        "repo": "pilotmain/aethos",
        "project": "pilotos",
        "environment": "production",
        "service_name": "aethos-api",
        "runtime": "Python",
        "build_command": "pip install -r requirements.txt",
        "start_command": "unknown",
        "health_check_path": "/health",
    }
    gate = assess_mutation_readiness_gate(plan)
    assert gate["mutation_ready"] is False
    assert "start_command" in gate["missing"]


def test_mutation_ready_requires_all_fields() -> None:
    plan = {
        "repo": "pilotmain/aethos",
        "project": "pilotos",
        "environment": "production",
        "service_name": "aethos-api",
        "runtime": "Python",
        "build_command": "pip install -r requirements.txt",
        "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
        "health_check_path": "/api/v1/health",
    }
    gate = assess_mutation_readiness_gate(plan)
    assert gate["mutation_ready"] is True
    assert gate["missing"] == []


def test_env_vars_grouped() -> None:
    names = [
        "APP_ENV",
        "API_PORT",
        "BROWSER_AUTOMATION_ENABLED",
        "ANTHROPIC_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "EXTRA_ONE",
        "EXTRA_TWO",
    ]
    summary = categorize_env_var_names(names)
    lines = format_env_var_section_lines(names, categorized=summary)
    body = "\n".join(lines)
    assert "Core runtime:" in body
    assert "Browser automation:" in body
    assert "AI providers:" in body
    assert "Integrations:" in body
    assert "Additional vars detected:" in body
    assert "APP_ENV" in body
    assert "postgres://" not in body


def test_merge_rejects_health_probe_start() -> None:
    plan = {
        "repo": "pilotmain/aethos",
        "project": "pilotos",
        "environment": "production",
        "service_name": "aethos-api",
    }
    updated = merge_inspection_into_plan(
        plan,
        inspection={
            "ok": True,
            "fields": {
                "runtime": "Docker",
                "build_command": "docker build .",
                "start_command": "curl -f http://127.0.0.1:8010/health || exit 1",
                "health_check_path": "/health",
                "required_env_var_names": [],
                "service_name_confidence": "low",
            },
        },
    )
    assert updated["start_command"] == "unknown"
    assert updated["mutation_ready"] is False
    assert "start_command" in updated["readiness_gate_missing"]
