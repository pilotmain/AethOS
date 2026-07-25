# SPDX-License-Identifier: Apache-2.0
"""Vercel adapter expansion registry — honest wired vs expanding operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OperationStatus = Literal["wired", "expanding", "planned"]
OperationCategory = Literal["readonly", "mutation", "verification"]


@dataclass(frozen=True)
class VercelOperationSpec:
    operation: str
    category: OperationCategory
    status: OperationStatus
    enabled: bool
    summary: str


VERCEL_EXPANSION_OPERATIONS: tuple[VercelOperationSpec, ...] = (
    VercelOperationSpec("list_projects", "readonly", "wired", True, "Project inventory via Vercel API"),
    VercelOperationSpec("list_deployments", "readonly", "wired", True, "Deployment listing"),
    VercelOperationSpec("project_details", "readonly", "wired", True, "Project configuration details"),
    VercelOperationSpec("list_domains", "readonly", "wired", True, "Domain inspection"),
    VercelOperationSpec("check_logs", "readonly", "wired", True, "Build/runtime logs (API partial, browser fallback)"),
    VercelOperationSpec("env_metadata", "readonly", "wired", True, "Env var key metadata only — never secret values"),
    VercelOperationSpec("live_diagnosis", "readonly", "wired", True, "Multi-source Vercel live readonly diagnostics"),
    VercelOperationSpec("failed_deployment", "readonly", "wired", True, "Failed deployment build/runtime diagnosis"),
    VercelOperationSpec("github_correlation", "readonly", "wired", True, "Correlate Vercel deploy source with GitHub CI evidence"),
    VercelOperationSpec("redeploy", "mutation", "wired", True, "Governed production redeploy"),
    VercelOperationSpec("rollback", "mutation", "expanding", False, "Governed rollback — wiring in progress"),
    VercelOperationSpec("set_env_var", "mutation", "expanding", False, "Governed env var set — wiring in progress"),
    VercelOperationSpec("remove_env_var", "mutation", "expanding", False, "Governed env var removal — wiring in progress"),
    VercelOperationSpec("promote_deployment", "mutation", "expanding", False, "Governed deployment promotion — wiring in progress"),
    VercelOperationSpec("deployment_status", "verification", "wired", True, "Post-deploy deployment state"),
    VercelOperationSpec("build_runtime_logs", "verification", "wired", True, "Build/runtime log verification"),
    VercelOperationSpec("domain_health", "verification", "expanding", True, "Domain reachability checks during live diagnostics"),
    VercelOperationSpec("env_availability", "verification", "expanding", False, "Env availability verification — wiring in progress"),
    VercelOperationSpec("post_deploy_health", "verification", "expanding", False, "Post-deploy health verification — wiring in progress"),
)


def vercel_operation_spec(operation: str) -> VercelOperationSpec | None:
    key = (operation or "").strip().lower()
    for spec in VERCEL_EXPANSION_OPERATIONS:
        if spec.operation == key:
            return spec
    return None


def vercel_expansion_summary() -> dict[str, list[str]]:
    return {
        "readonly_wired": [spec.operation for spec in VERCEL_EXPANSION_OPERATIONS if spec.category == "readonly" and spec.enabled],
        "mutations_wired": [spec.operation for spec in VERCEL_EXPANSION_OPERATIONS if spec.category == "mutation" and spec.status == "wired"],
        "expanding": [spec.operation for spec in VERCEL_EXPANSION_OPERATIONS if spec.status == "expanding"],
        "planned": [spec.operation for spec in VERCEL_EXPANSION_OPERATIONS if spec.status == "planned"],
    }
