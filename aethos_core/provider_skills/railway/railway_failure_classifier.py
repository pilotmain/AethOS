# SPDX-License-Identifier: Apache-2.0
"""Classify Railway execution failures into operational stages."""

from __future__ import annotations

from typing import Any


def classify_railway_failure(
    *,
    reason: str,
    provider_result: dict[str, Any] | None = None,
    artifact: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> str:
    text = (reason or "").lower()
    provider_result = provider_result or {}
    artifact = artifact or {}
    params = params or {}

    if "github installation" in text or "source binding" in text:
        return "source_binding"
    if "service id" in text or "service_id" in text or "service not found" in text:
        return "target_resolution"
    if "environment id" in text or "environment not found" in text:
        return "target_resolution"
    if "project id" in text or "project not found" in text:
        return "target_resolution"
    if "credential" in text or "credentials" in text or "token missing" in text or "not authenticated" in text:
        return "credentials"
    if provider_result.get("graphql_errors"):
        return "railway_api"
    if provider_result.get("failure_type") == "provider_auth_failure":
        return "credentials"
    mode = str(provider_result.get("execution_mode") or artifact.get("execution_mode") or params.get("execution_mode") or "")
    if mode == "cli" or "command not found" in text or "railway:" in text:
        return "railway_cli"
    if "rejected" in text or "permission denied" in text or "graphql error" in text:
        return "provider_rejected"
    if artifact.get("restart_command_submitted") is False:
        return "command_submission"
    if "verification" in text or "evidence" in text:
        return "verification"
    if "logs" in text:
        return "evidence_collection"
    return "railway_api"
