# SPDX-License-Identifier: Apache-2.0
"""Provider operational repair loop — observe, diagnose, propose fix."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_topology.binding_verifier import verify_source_binding
from aethos_core.provider_topology.provider_relationships import extract_github_repo_references
from aethos_core.provider_topology.topology_refresh import refresh_service_topology


def compose_repair_proposal(
    *,
    provider: str,
    project: str,
    environment: str,
    service_name: str,
    user_text: str = "",
    failure_reason: str | None = None,
    accessible_repos: list[str] | None = None,
    operation_type: str | None = None,
) -> dict[str, Any]:
    path = f"{project} / {environment} / {service_name}"
    binding = verify_source_binding(
        provider=provider,
        project=project,
        environment=environment,
        service_name=service_name,
        user_text=user_text,
        accessible_repos=accessible_repos,
        operation_type=operation_type or "restart",
    )
    refs = extract_github_repo_references(user_text)
    proposed_repo = refs[0] if refs else binding.referenced_github_repo

    likely_causes = []
    if failure_reason and "installation" in failure_reason.lower():
        likely_causes.extend(["stale repository mapping", "project transferred", "installation removed"])
    if binding.ambiguity and binding.ambiguity.kind == "repo_mismatch":
        likely_causes.append("stored GitHub repo differs from referenced repository")

    steps = [
        "refresh provider topology",
    ]
    if proposed_repo and proposed_repo != binding.stored_github_repo:
        steps.append(f"update GitHub source binding to **{proposed_repo}**")
    elif binding.stored_github_repo:
        steps.append(f"verify GitHub installation for **{binding.stored_github_repo}**")
    steps.append("re-run governed restart")
    steps.append("verify restart evidence")

    cause_text = ", ".join(likely_causes) if likely_causes else "provider source binding or installation issue"
    reply = (
        f"The Railway operation for **{path}** failed because the GitHub installation for the currently stored repository binding does not exist or is stale.\n\n"
        f"Likely cause:\n- {cause_text}\n\n"
        "Proposed repair:\n"
        + "\n".join(f"- {step}" for step in steps)
        + "\n\n**Approval is required before any binding update or mutation.**"
    )
    return {
        "reply": reply,
        "meta": {
            "provider": provider,
            "service": service_name,
            "proposed_repo": str(proposed_repo or ""),
            "stored_repo": str(binding.stored_github_repo or ""),
        },
        "steps": steps,
    }


def execute_topology_repair(
    *,
    provider: str,
    project: str,
    environment: str,
    service_name: str,
    github_repo: str | None = None,
) -> dict[str, Any]:
    graph = refresh_service_topology(
        provider=provider,
        project=project,
        environment=environment,
        service_name=service_name,
        github_repo=github_repo,
        force=True,
    )
    if graph is None:
        return {"ok": False, "error": "Could not refresh topology for service."}
    return {"ok": True, "topology": graph.to_dict()}
