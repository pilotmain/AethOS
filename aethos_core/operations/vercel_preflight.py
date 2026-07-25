# SPDX-License-Identifier: Apache-2.0
"""Vercel-specific read-only operation preflight builders."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.execution.execution_permissions import is_mutating_operation
from aethos_core.operations.execution_status import execution_status_lines, safety_footer
from aethos_core.operations.orchestration.registry_runtime import preflight_capability_metadata
from aethos_core.operations.vercel_operation_capabilities import (
    browser_fallback_only,
    is_api_capable,
)
from aethos_core.operations.operation_models import OperationPreflight
from aethos_core.operations.target_resolution import TargetResolution
from aethos_core.runtime.latest_inventory_store import merge_project_state


def _vercel_api_token_available() -> bool:
    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    resolved = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
    return resolved.get("method") == "api_token"


def build_vercel_preflight(
    *,
    operation_type: str,
    resolution: TargetResolution,
    user_request: str,
) -> OperationPreflight:
    target = resolution.target_name
    state = merge_project_state(project_name=target, memory=resolution.memory)

    op = operation_type
    risk = "medium"
    steps: list[str] = []
    blockers: list[str] = []
    if is_mutating_operation(op):
        blockers.append("Mutating operations remain disabled until a later phase.")
    missing: list[str] = []
    target_status = resolution.status

    if resolution.status == "ambiguous":
        return OperationPreflight(
            provider="vercel",
            operation_type=op,
            target_name=None,
            target_status="ambiguous",
            risk_level="low",
            mutation_required=False,
            required_approval=False,
            current_state={"matches": resolution.matches},
            proposed_steps=["Clarify which Vercel project you mean."],
            blockers=[],
            missing_information=["target_project"],
            next_action="clarify_target",
        )

    if resolution.status == "blocked_by_browser_runtime":
        cap = preflight_capability_metadata("vercel", op)
        if cap.get("api_capable"):
            return OperationPreflight(
                provider="vercel",
                operation_type=op,
                target_name=resolution.target_name,
                target_status="missing" if not resolution.target_name else "resolved",
                risk_level="low",
                mutation_required=False,
                required_approval=True,
                current_state={**cap, "resolution_message": resolution.message},
                proposed_steps=[
                    "Resolve target project via Vercel API.",
                    "Re-run with an explicit project name if needed.",
                ],
                blockers=[resolution.message or "Target could not be resolved."],
                missing_information=["target_project"],
                next_action="refresh_inventory",
            )
        return OperationPreflight(
            provider="vercel",
            operation_type=op,
            target_name=None,
            target_status="blocked_by_browser_runtime",
            risk_level="low",
            mutation_required=False,
            required_approval=False,
            current_state={},
            proposed_steps=[
                "Fix AethOS browser runtime (Playwright sync/async boundary).",
                "Restart the API, then run `show my Vercel apps` to refresh inventory.",
            ],
            blockers=[resolution.message or "Browser execution blocked by AethOS runtime issue."],
            missing_information=["browser_runtime", "fresh_inventory"],
            next_action="fix_browser_runtime",
        )

    if resolution.status == "missing":
        cap = preflight_capability_metadata("vercel", op)
        msg = resolution.message or "Target not found."
        steps = (
            ["Project was not found via Vercel API.", "Verify the project name and try again."]
            if resolution.source == "provider_api"
            else [
                "Run `show my Vercel apps` to refresh inventory.",
                "Re-run this operation with an explicit project name.",
            ]
        )
        return OperationPreflight(
            provider="vercel",
            operation_type=op,
            target_name=None,
            target_status="missing",
            risk_level="low",
            mutation_required=False,
            required_approval=False,
            current_state={**cap, "resolution_source": resolution.source},
            proposed_steps=steps,
            blockers=[msg],
            missing_information=["target_project"] if resolution.source != "provider_api" else ["target_project"],
            next_action="refresh_inventory",
        )

    health = str(state.get("last_health") or state.get("health_confidence") or "unknown")
    prod_url = state.get("production_url")
    evidence = list(state.get("evidence") or [])
    deploy_state = str(state.get("latest_deployment_state") or "unknown")
    prod_health = str(state.get("production_health") or "unknown")

    if op == "redeploy":
        risk = "medium"
        steps = [
            "Confirm latest deployment state (production vs preview).",
            "Verify linked Git repository and branch.",
            "Review recent build/runtime errors if available.",
            "Prepare redeploy proposal — mutating execution remains disabled in Phase 9.3B.",
        ]
        if health in ("failed", "likely_degraded") or deploy_state == "failed":
            missing.append("confirm_root_cause_before_redeploy")
        if str(state.get("latest_deployment_scope") or "") == "unknown":
            missing.append("target_environment_or_branch")

    elif op == "restart":
        risk = "medium"
        steps = [
            "Confirm production URL and latest deployment scope.",
            "Identify whether restart means production redeploy or runtime recycle.",
            "Prepare restart proposal — mutating execution remains disabled in Phase 9.3B.",
        ]

    elif op == "check_logs":
        risk = "low"
        steps = [
            "Resolve project in Vercel inventory (done).",
            "Fetch recent deployment metadata via Vercel API.",
            "Extract build/runtime log excerpts from deployment events when available.",
            "Use browser dashboard fallback only if API logs are insufficient.",
        ]
        cap = preflight_capability_metadata("vercel", op)
        if not cap.get("api_capable"):
            blockers.append(
                "Vercel API token not configured — log extraction may require browser runtime."
            )
        elif cap.get("browser_runtime_required") is False:
            from aethos_core.runtime.browser_runtime import browser_inventory_refresh_blocked_reason

            blocked, _reason = browser_inventory_refresh_blocked_reason(probe_launch=False)
            if blocked and browser_fallback_only(op):
                steps.append(
                    "Browser log fallback is currently unavailable; API-backed log inspection will still run."
                )

    elif op == "list_deployments":
        risk = "low"
        steps = [
            "Query recent deployments via Vercel API.",
            "Summarize state, branch, commit, target, and failure reason when available.",
        ]

    elif op == "list_domains":
        risk = "low"
        steps = [
            "Query project domains via Vercel API.",
            "Summarize custom domains, vercel.app aliases, verification, and production mapping.",
        ]

    elif op == "project_details":
        risk = "low"
        steps = [
            "Fetch project metadata via Vercel API.",
            "Summarize framework, repo, environments, and build settings.",
        ]

    elif op in ("why_down", "inspect_failed_deployment"):
        risk = "low"
        steps = [
            "Inspect latest deployment failures via Vercel API.",
            "Review deployment events and failure reasons when available.",
            "Check production URL reachability if known.",
            "Use browser dashboard fallback only if API evidence is insufficient.",
            "Summarize likely failure reason without claiming certainty.",
        ]
        if prod_health == "down" and "scope_detected: production" in evidence:
            state["signal"] = "production_failure_detected"
        elif health == "failed" or deploy_state == "failed":
            if "scope_detected: production" in evidence:
                state["signal"] = "latest_deployment_failed_production_scope"
            else:
                state["signal"] = "latest_deployment_failed_production_impact_unclear"
        elif prod_health in ("healthy", "unknown") and health in ("healthy", "likely_healthy", "unknown"):
            state["signal"] = "insufficient_evidence_app_is_down"
            missing.append("live_dashboard_confirmation")

    elif op == "set_env_var":
        risk = "high"
        steps = [
            "Confirm target project and environment (production vs preview).",
            "Record requested variable name and value.",
            "Validate impact on dependent services.",
            "Prepare env change proposal — no write until mutating execution is enabled.",
        ]
        missing.extend(["exact_env_value_confirmation", "environment_target"])

    elif op == "deploy_from_git":
        risk = "medium"
        steps = [
            "Confirm Git repository and branch from project metadata.",
            "Verify latest deployment and production URL.",
            "Prepare deploy-from-Git proposal — mutating execution remains disabled in Phase 9.3B.",
        ]

    else:
        steps = [
            "Gather current project state from latest inventory and operational memory.",
            "Plan read-only checks before any mutation.",
        ]

    if not prod_url and not is_api_capable(op):
        missing.append("production_url_not_in_memory")

    cap_meta = preflight_capability_metadata("vercel", op)
    state = {**state, **cap_meta, "resolution_source": resolution.source}

    return OperationPreflight(
        provider="vercel",
        operation_type=op,
        target_name=target,
        target_status=target_status,
        risk_level=risk,
        read_only=True,
        mutation_required=op not in ("why_down", "inspect_failed_deployment", "check_logs"),
        required_approval=True,
        current_state=state,
        proposed_steps=steps,
        blockers=blockers,
        missing_information=missing,
        next_action="approval_required_before_execution",
    )


def format_preflight_report(preflight: OperationPreflight, *, user_request: str) -> str:
    lines = [
        "# Operation preflight",
        "",
        f"- **Provider:** {preflight.provider}",
        f"- **Operation:** {preflight.operation_type}",
        f"- **Target:** `{preflight.target_name or '(unresolved)'}`",
        f"- **Target status:** {preflight.target_status}",
        f"- **Risk:** {preflight.risk_level}",
        f"- **Read-only preflight:** yes",
        *execution_status_lines(preflight),
        "",
        "## User request",
        "",
        user_request,
        "",
        "## Current state",
        "",
    ]
    if preflight.current_state:
        for k, v in preflight.current_state.items():
            lines.append(f"- **{k}:** {v}")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Proposed steps", ""])
    for step in preflight.proposed_steps:
        lines.append(f"- {step}")
    if preflight.blockers:
        lines.extend(["", "## Blockers", ""])
        for b in preflight.blockers:
            lines.append(f"- {b}")
    if preflight.missing_information:
        lines.extend(["", "## Missing information", ""])
        for m in preflight.missing_information:
            lines.append(f"- {m}")
    lines.extend(
        [
            "",
            "## Next action",
            "",
            preflight.next_action,
            "",
            "## Safety",
            "",
            safety_footer(preflight),
        ]
    )
    return "\n".join(lines)
