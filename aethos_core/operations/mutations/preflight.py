# SPDX-License-Identifier: Apache-2.0
"""Mutation preflight — plan + risk + blast radius + approval gate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.config import get_settings
from aethos_core.operations.execution.execution_permissions import is_mutating_operation
from aethos_core.operations.mutations.audit import build_audit_stub
from aethos_core.operations.mutations.blast_radius import analyze_blast_radius
from aethos_core.operations.mutations.blocked_actions import is_hard_blocked
from aethos_core.operations.mutations.rollback import rollback_plan_for_operation
from aethos_core.operations.mutations.risk import (
    MutationRiskTier,
    classify_mutation_risk,
    execution_allowed_for_tier,
    tier_label,
)
from aethos_core.operations.mutations.secrets import parse_env_var_from_request, redact_secrets_in_text
from aethos_core.operations.mutations.taxonomy import is_mutation_operation


from aethos_core.operations.orchestration.target_resolution import canonical_resolve_target


def _is_governed_mutation(operation_type: str) -> bool:
    return is_mutating_operation(operation_type) or is_mutation_operation(operation_type)


def compose_unresolved_deploy_repo_summary(provider: str, user_request: str) -> str:
    """Honest summary when a deploy-from-git target can't be resolved to a real repo.

    Names what the user asked for (or that it wasn't a valid reference) and asks for an
    owner/repo we can act on — instead of a generic "needs information".
    """
    import re

    from aethos_core.provider_topology.repo_reference_parser import parse_repo_reference

    provider_label = (provider or "the cloud").title()
    parsed = parse_repo_reference(user_request or "")
    if parsed and parsed.full_name and "/" in parsed.full_name:
        return (
            f"I couldn't confirm **{parsed.full_name}** is a repository I can access for a "
            f"{provider_label} deploy. Check the name and that I have access, or paste the GitHub URL. "
            "No deploy from git was performed."
        )
    _STOP = {
        "my", "the", "a", "an", "app", "application", "repo", "repository", "it", "this",
        "that", "from", "git", "github", "project", "service", "code", "some",
    }
    m = re.search(r"\brepo(?:sitory)?\s+(?:called|named)\s+([^\s,.]+)", user_request or "", re.I) or re.search(
        r"\bdeploy\s+(?:a\s+|the\s+)?(?:repo(?:sitory)?\s+)?([A-Za-z0-9._-]+)",
        user_request or "",
        re.I,
    )
    candidate = m.group(1) if m else ""
    named = f" **{candidate}**" if candidate and candidate.lower() not in _STOP else " that"
    return (
        f"I can't deploy{named} on {provider_label} — it isn't a repository reference I can resolve. "
        "Give me the full **owner/repo** (e.g. `pilotmain/AethOS`) or the GitHub URL and I'll prepare "
        "the deploy preflight. No deploy from git was performed."
    )


@dataclass
class MutationPreflightOutcome:
    provider: str
    operation_type: str
    target_name: str | None
    risk_tier: MutationRiskTier
    preflight_status: str
    mutation_execution_enabled: bool
    summary: str
    full_result: str
    audit: dict[str, Any]
    rollback_plan: dict[str, Any]
    required_future_steps: list[str]
    blast_radius: dict[str, Any] = field(default_factory=dict)
    workflow_resolution: dict[str, Any] | None = None
    workflow_resolution_debug: dict[str, Any] | None = None
    discovery_failure_reason: str | None = None
    target_resolved: bool = False
    target: dict[str, Any] | None = None
    credential_guidance: dict[str, Any] | None = None
    credential_requirements_reply: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out = {
            "provider": self.provider,
            "operation_type": self.operation_type,
            "target_name": self.target_name,
            "target_resolved": self.target_resolved,
            "target": dict(self.target) if self.target else None,
            "risk_tier": self.risk_tier.value,
            "risk_label": tier_label(self.risk_tier),
            "preflight_status": self.preflight_status,
            "mutation_execution_enabled": self.mutation_execution_enabled,
            "rollback_plan": self.rollback_plan,
            "required_future_steps": self.required_future_steps,
            "audit": self.audit,
            "blast_radius": self.blast_radius,
        }
        if self.workflow_resolution:
            out["workflow_resolution"] = self.workflow_resolution
        if self.workflow_resolution_debug:
            out["workflow_resolution_debug"] = self.workflow_resolution_debug
        if self.discovery_failure_reason:
            out["discovery_failure_reason"] = self.discovery_failure_reason
        return out


def _mutation_provider_auth_block(*, provider: str, operation_type: str) -> str | None:
    from aethos_core.connections.credential_runtime_gate import check_provider_credential_gate

    gate = check_provider_credential_gate(provider, require_validated=True)
    if gate.get("ok"):
        return None
    if gate.get("auth_source") == "metadata_only" or gate.get("credential_state") in (
        "reconnect_required",
        "persistence_failed",
        "secret_missing",
    ):
        return "needs_credential_repair"
    return "needs_credential"


def _discover_github_workflow_for_mutation(
    *,
    target_name: str,
    user_request: str = "",
    target_hints: list[str] | None = None,
    session_id: str = "default",
) -> dict[str, Any]:
    from aethos_core.providers.github.mutations.workflow_rerun_preflight import prepare_workflow_rerun_preflight

    return prepare_workflow_rerun_preflight(
        session_id=session_id,
        target_name=target_name,
        user_request=user_request,
        target_hints=target_hints,
    )


def run_mutation_preflight(*, job_type: str, params: dict[str, Any]) -> MutationPreflightOutcome:
    params = dict(params)
    provider = str(params.get("provider") or "unknown")
    if provider == "railway":
        from aethos_core.provider_topology.source_binding_resolver import refresh_params_source_binding

        params, _resolution, regression = refresh_params_source_binding(params, block_stale_regression=True)
        if regression is not None:
            from aethos_core.provider_topology.source_binding_resolver import compose_stale_binding_regression_reply

            return MutationPreflightOutcome(
                provider=provider,
                operation_type=str(params.get("operation_type") or "unknown"),
                target_name=params.get("target_name"),
                risk_tier=MutationRiskTier.T5_BLOCKED,
                preflight_status="blocked_stale_binding",
                mutation_execution_enabled=False,
                summary=compose_stale_binding_regression_reply(regression),
                full_result=compose_stale_binding_regression_reply(regression),
                audit=build_audit_stub(
                    request=str(params.get("user_request") or ""),
                    provider=provider,
                    operation_type=str(params.get("operation_type") or "unknown"),
                    target_name=params.get("target_name"),
                    risk_tier=MutationRiskTier.T5_BLOCKED.value,
                    result="blocked_stale_binding",
                ),
                rollback_plan=rollback_plan_for_operation(
                    provider=provider,
                    operation_type=str(params.get("operation_type") or "unknown"),
                ),
                required_future_steps=["Refresh source binding context and create a new governed preflight."],
            )

    user_request = str(params.get("user_request") or "")
    operation_type = str(params.get("operation_type") or "unknown")
    target_name = params.get("target_name")
    target_status = str(params.get("target_status") or "unknown")
    target_payload = dict(params.get("target") or {}) if isinstance(params.get("target"), dict) else {}
    target_resolved = bool(params.get("target_resolved")) or bool(target_payload.get("resolved"))

    if target_resolved and target_name is not None:
        target_name = str(target_name)
        target_status = "resolved"
    elif target_name is not None:
        target_name = str(target_name)
        if target_status == "unknown":
            target_status = "resolved"
    elif provider == "github" and operation_type == "workflow_rerun":
        from aethos_core.providers.github.context.github_context_store import resolve_rerun_repository

        repo_resolution = resolve_rerun_repository(
            session_id=str(params.get("session_id") or "default"),
            user_request=user_request,
            target_hints=list(params.get("target_hints") or []),
        )
        if repo_resolution.get("repo"):
            target_name = str(repo_resolution["repo"])
            target_status = "resolved"
            target_resolved = True
        else:
            target_status = "missing"
    else:
        resolution = canonical_resolve_target(
            provider=provider,
            user_request=user_request,
            target_hints=list(params.get("target_hints") or []),
            operation_type=operation_type,
        )
        target_name = resolution.target_name
        target_status = resolution.status
        if resolution.status == "resolved" and resolution.memory:
            target_payload = dict(resolution.memory)
            target_resolved = True

    blast = analyze_blast_radius(
        provider=provider,
        operation_type=operation_type,
        target_name=target_name,
        target_status=target_status,
    )

    discovery_failure_reason: str | None = None
    auth_block = (
        _mutation_provider_auth_block(provider=provider, operation_type=operation_type)
        if provider in ("railway", "github", "vercel") and operation_type not in ("workflow_rerun",)
        else None
    )
    if auth_block:
        discovery_failure_reason = "provider_auth_failure"

    if is_hard_blocked(operation_type):
        tier = MutationRiskTier.T5_BLOCKED
        status = "blocked"
    elif not _is_governed_mutation(operation_type):
        tier = MutationRiskTier.T5_BLOCKED
        status = "blocked"
    else:
        tier = classify_mutation_risk(
            operation_type=operation_type,
            provider=provider,
            target_status=target_status,
            production_impact=blast.production_impact,
        )
        settings = get_settings()
        execution_enabled = execution_allowed_for_tier(tier)
        if auth_block:
            status = auth_block
        elif not settings.mutation_execution_enabled or not execution_enabled:
            status = "design_only_blocked"
        elif tier in (MutationRiskTier.T4_IRREVERSIBLE, MutationRiskTier.T5_BLOCKED):
            status = "blocked"
        elif not target_name and operation_type not in ("workflow_rerun",):
            status = "needs_information"
        else:
            status = "ready_for_mutation_approval"

    execution_enabled = execution_allowed_for_tier(tier) and get_settings().mutation_execution_enabled
    rollback = rollback_plan_for_operation(provider=provider, operation_type=operation_type)
    future_steps = [
        "Human approval at correct risk tier",
        "Staged mutation_execution",
        "Post-mutation readonly verification",
        "Rollback/recovery plan acknowledgment",
        "Immutable audit record",
    ]
    audit = build_audit_stub(
        request=redact_secrets_in_text(user_request),
        provider=provider,
        operation_type=operation_type,
        target_name=target_name,
        risk_tier=tier.value,
        result="ready_for_approval" if status == "ready_for_mutation_approval" else status,
    )

    mode = "governed execution" if status == "ready_for_mutation_approval" else "design-only"
    lines = [
        f"# Mutation preflight ({mode})",
        "",
        f"**Provider:** {provider}",
        f"**Operation:** {operation_type.replace('_', ' ')}",
        f"**Target:** {target_name or '(unresolved)'}",
        f"**Risk tier:** {tier_label(tier)}",
        "",
        "**Blast radius:**",
        f"- Scope: {blast.scope}",
        f"- Reversibility: {blast.reversibility}",
        f"- Expected downtime: {blast.expected_downtime}",
        f"- Production impact: {blast.production_impact}",
        "",
    ]
    if blast.dependency_impact:
        lines.append("**Dependency impact:**")
        for dep in blast.dependency_impact:
            lines.append(f"- {dep}")
        lines.append("")

    if status == "ready_for_mutation_approval":
        lines.append("**Status:** ready for **Mission Control mutation approval**.")
    elif status == "needs_information":
        lines.append("**Status:** needs target resolution before approval.")
    elif status == "needs_credential_repair":
        lines.append("**Status:** credential repair required before approval.")
    elif status == "needs_credential":
        lines.append("**Status:** provider mutation credentials are **not configured** — approval blocked.")
    elif status == "design_only_blocked":
        lines.append("**Status:** mutation execution is **disabled** (design-only mode).")
    else:
        lines.append("**Status:** mutation execution **not enabled** or tier blocked.")

    lines.extend(["", "**Required steps:**"])
    for step in future_steps:
        lines.append(f"- {step}")
    lines.extend(
        [
            "",
            "**Rollback plan:**",
            f"- Reversible: {rollback.get('reversible')}",
            f"- Strategy: {rollback.get('strategy')}",
            f"- Verification: {rollback.get('verification')}",
            "",
            f"**Mutating execution:** {'enabled after approval' if execution_enabled else 'disabled'}",
        ]
    )
    if user_request:
        lines.extend(["", f"**Request:** {redact_secrets_in_text(user_request)}"])

    workflow_resolution: dict[str, Any] | None = None
    workflow_resolution_debug: dict[str, Any] | None = None
    discovery: dict[str, Any] | None = None
    if provider == "github" and operation_type == "workflow_rerun":
        discovery = _discover_github_workflow_for_mutation(
            target_name=str(target_name or ""),
            user_request=user_request,
            target_hints=list(params.get("target_hints") or []),
            session_id=str(params.get("session_id") or "default"),
        )
        workflow_resolution_debug = (
            (discovery.get("workflow_resolution_debug") or discovery.get("discovery_diagnostics"))
            if isinstance(discovery, dict)
            else None
        )
        discovery_failure_reason = (
            str(discovery.get("discovery_failure_reason") or "")
            if isinstance(discovery, dict) and not discovery.get("ok")
            else None
        ) or None
        if discovery.get("needs_repo"):
            status = "needs_information"
            lines.extend(["", str(discovery.get("error") or "No GitHub repository context available.")])
            workflow_resolution = discovery if isinstance(discovery, dict) else None
        elif discovery.get("preflight_blocked"):
            status = "blocked_correlation_boundary"
            lines.extend(["", str(discovery.get("error") or "Correlation boundary blocks GitHub workflow rerun.")])
            workflow_resolution = discovery if isinstance(discovery, dict) else None
        elif discovery.get("no_failed_workflow"):
            status = "no_action_available"
            discovery_failure_reason = "no_failed_workflow"
            if discovery.get("repository"):
                target_name = str(discovery["repository"])
                target_status = "resolved"
                target_resolved = True
            workflow_resolution = discovery if isinstance(discovery, dict) else None
        elif discovery and discovery.get("ok"):
            workflow_resolution = discovery
            if discovery.get("repository") and not target_name:
                target_name = str(discovery["repository"])
                target_status = "resolved"
                target_resolved = True
            deploy_risk = discovery.get("deploy_risk") if isinstance(discovery.get("deploy_risk"), dict) else None
            if deploy_risk and deploy_risk.get("risk_tier"):
                try:
                    tier = MutationRiskTier(str(deploy_risk["risk_tier"]))
                    audit["risk_tier"] = tier.value
                    execution_enabled = execution_allowed_for_tier(tier) and get_settings().mutation_execution_enabled
                    if (
                        status == "ready_for_mutation_approval"
                        and get_settings().mutation_execution_enabled
                        and not execution_allowed_for_tier(tier)
                    ):
                        status = "design_only_blocked"
                except ValueError:
                    pass
            sections = list(discovery.get("preflight_sections") or [])
            if sections:
                lines.extend(["", *sections])
            else:
                lines.extend(
                    [
                        "",
                        "**Workflow discovery (readonly substrate):**",
                        f"- Repository: {workflow_resolution.get('repository')}",
                        f"- Workflow: {workflow_resolution.get('workflow_name') or workflow_resolution.get('workflow_id')}",
                        f"- Selected run: #{workflow_resolution.get('source_run_number')} "
                        f"({workflow_resolution.get('source_status')}/{workflow_resolution.get('source_conclusion') or '—'})",
                        f"- Rerunnable candidates: {workflow_resolution.get('rerunnable_candidates_found', 1)}",
                    ]
                )
        elif status == "ready_for_mutation_approval":
            status = "needs_workflow_resolution"
            lines.append("")
            lines.append("**Status:** workflow discovery failed — needs workflow resolution.")
            if workflow_resolution_debug:
                diag = workflow_resolution_debug
                lines.extend(
                    [
                        "",
                        "**Discovery diagnostics:**",
                        f"- Candidates found: {diag.get('workflow_candidates_found', 0)}",
                        f"- Rerunnable candidates: {diag.get('rerunnable_candidates_found', 0)}",
                        f"- Candidate states: {', '.join(str(s) for s in (diag.get('candidate_states') or [])) or '—'}",
                        f"- Failure reason: {diag.get('discovery_failure_reason') or discovery_failure_reason or 'unknown'}",
                    ]
                )
            workflow_resolution = discovery if isinstance(discovery, dict) else None

    outcome_dict = {
        "provider": provider,
        "operation_type": operation_type,
        "target_name": target_name,
        "target_resolved": bool(target_resolved and target_name),
        "target": target_payload or None,
        "preflight_status": status,
        "user_request": user_request,
    }
    from aethos_core.credentials.credential_guidance import attach_credential_guidance_to_preflight

    credential_guidance: dict[str, Any] | None = None
    credential_requirements_reply: str | None = None
    if status in ("needs_credential", "needs_credential_repair"):
        enriched = attach_credential_guidance_to_preflight(outcome_dict)
        credential_guidance = enriched.get("credential_guidance")
        credential_requirements_reply = enriched.get("credential_requirements_reply")
        if credential_requirements_reply:
            lines.extend(["", credential_requirements_reply])

    workflow_discovery = None
    if isinstance(discovery, dict):
        workflow_discovery = discovery.get("workflow_discovery")
    if not workflow_discovery and isinstance(workflow_resolution_debug, dict):
        workflow_discovery = workflow_resolution_debug.get("workflow_discovery")
    if (
        provider == "github"
        and operation_type == "workflow_rerun"
        and isinstance(workflow_discovery, dict)
        and workflow_discovery
    ):
        from aethos_core.providers.github.workflow_discovery.workflow_discovery_reply import (
            compose_workflow_discovery_sections,
        )

        lines.extend(["", *compose_workflow_discovery_sections(workflow_discovery)])

    if status == "no_action_available" and not workflow_discovery:
        from aethos_core.providers.github.context.github_context_store import compose_no_failed_workflow_guidance

        repo_label = str(target_name or "the diagnosed repo")
        full = "\n".join(compose_no_failed_workflow_guidance(repository=repo_label))
    else:
        full = "\n".join(lines)
    if status == "ready_for_mutation_approval":
        summary = (
            f"Mutation preflight ({tier_label(tier)}): ready for approval. "
            f"No {operation_type.replace('_', ' ')} performed yet."
        )
    else:
        summary = (
            f"Mutation preflight ({tier_label(tier)}): {status.replace('_', ' ')}. "
            f"No {operation_type.replace('_', ' ')} was performed."
        )
    if status == "needs_workflow_resolution":
        reason = discovery_failure_reason or "discovery_failed"
        summary = (
            f"Mutation preflight ({tier_label(tier)}): discovery failed ({reason.replace('_', ' ')}). "
            f"No workflow rerun performed."
        )
    elif status == "no_action_available":
        repo_label = target_name or "the diagnosed repo"
        summary = (
            f"I inspected {repo_label}, but no failed workflow run is available to rerun. "
            "No mutation has been performed."
        )
    elif status == "needs_credential_repair":
        summary = (
            f"Mutation preflight ({tier_label(tier)}): credential repair required before approval. "
            f"No {operation_type.replace('_', ' ')} was performed."
        )
    elif status == "needs_credential":
        summary = (
            f"Mutation preflight ({tier_label(tier)}): provider mutation credentials missing — approval blocked. "
            f"No {operation_type.replace('_', ' ')} was performed."
        )
    elif status == "needs_information" and operation_type == "deploy_from_git" and not (
        target_resolved and target_name
    ):
        # Don't flatten an unresolved deploy target into a generic "needs information":
        # name what we couldn't resolve and ask for an owner/repo we can act on.
        summary = compose_unresolved_deploy_repo_summary(provider, user_request)

    return MutationPreflightOutcome(
        provider=provider,
        operation_type=operation_type,
        target_name=target_name,
        risk_tier=tier,
        preflight_status=status,
        mutation_execution_enabled=execution_enabled,
        summary=summary,
        full_result=full,
        audit=audit,
        rollback_plan=rollback,
        required_future_steps=future_steps,
        blast_radius=blast.to_dict(),
        workflow_resolution=workflow_resolution if (workflow_resolution and workflow_resolution.get("ok")) else None,
        workflow_resolution_debug=workflow_resolution_debug,
        discovery_failure_reason=discovery_failure_reason,
        target_resolved=bool(target_resolved and target_name),
        target=target_payload or None,
        credential_guidance=credential_guidance,
        credential_requirements_reply=credential_requirements_reply,
    )
