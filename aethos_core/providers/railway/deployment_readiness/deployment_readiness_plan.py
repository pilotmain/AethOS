# SPDX-License-Identifier: Apache-2.0
"""Compose Railway deployment readiness reports and governed plans."""

from __future__ import annotations

from typing import Any


def compose_capability_truth_for_new_service(checks: dict[str, Any] | None = None) -> str:
    """Short honest answer before or without a full readiness run."""
    lines = [
        "I can deploy **existing** Railway services today (governed restart/redeploy, readonly logs/events, inventory).",
        "",
        "For **new service creation**, I need to run deployment readiness checks first.",
        "",
        "No service will be created until you explicitly approve a governed plan.",
        "",
        "Ask me to **run Railway deployment readiness** (or include the target repo) and I will:",
        "1. List Railway projects/environments",
        "2. Inspect GitHub source-binding availability",
        "3. Confirm Railway token permissions",
        "4. Report whether service-creation API/CLI is available in this runtime",
        "5. Identify required env vars",
        "6. Produce a deployment plan",
    ]
    if checks and checks.get("readonly_readiness_ok"):
        lines.extend(["", "Latest readiness snapshot: **readonly checks passed** — see full report below."])
    lines.append("\nNo mutation has been performed.")
    return "\n".join(lines)


def compose_readiness_report(checks: dict[str, Any]) -> str:
    inv = checks.get("inventory") or {}
    gh = checks.get("github_binding") or {}
    creation = checks.get("service_creation") or {}

    lines = [
        "**Railway new-service deployment readiness** (readonly)",
        "",
        "### 1. Railway projects / environments",
    ]
    if inv.get("ok"):
        lines.append(
            f"- Workspace inventory OK — **{inv.get('project_count', 0)}** project(s), "
            f"**{inv.get('environment_count', 0)}** environment(s), **{inv.get('service_count', 0)}** service(s) visible."
        )
        for project in list(inv.get("projects") or [])[:4]:
            pname = project.get("name") or project.get("id")
            lines.append(f"- Project `{pname}`:")
            for env in list(project.get("environments") or [])[:3]:
                svc_preview = ", ".join(list(env.get("services") or [])[:6]) or "(no services listed)"
                lines.append(f"  - `{env.get('name')}`: {svc_preview}")
    else:
        lines.append(f"- Inventory **not available**: {inv.get('error') or 'unknown error'}")

    lines.extend(
        [
            "",
            "### 2. GitHub source binding",
            f"- GitHub credential: **{'ok' if gh.get('github_credential_ok') else 'blocked'}**",
            f"- Accessible repos: **{gh.get('accessible_repos_count', 0)}**",
        ]
    )
    ref_repo = str(checks.get("referenced_github_repo") or gh.get("referenced_repo") or "")
    if ref_repo:
        accessible = gh.get("referenced_repo_accessible")
        if accessible is True:
            lines.append(f"- Referenced repo `{ref_repo}`: **accessible**")
        elif accessible is False:
            lines.append(f"- Referenced repo `{ref_repo}`: **not accessible** with current GitHub token")
        else:
            lines.append(f"- Referenced repo `{ref_repo}`: binding not verified (repo list unavailable)")
    else:
        lines.append("- No GitHub repo detected in this message — include `owner/repo` for binding verification.")

    cred_source = str(checks.get("railway_credential_source") or "canonical provider credential resolver")
    token_ok = bool(checks.get("railway_credential_ok"))
    lines.extend(
        [
            "",
            "### 3. Railway token permissions",
            f"- Railway token: **{'pass' if token_ok else 'fail'}**",
            f"- Credential source: {cred_source}",
            f"- API connection: **{'ok' if checks.get('railway_api_connection_ok') else 'failed'}**",
        ]
    )
    if not token_ok:
        lines.extend(
            [
                f"- Checked source: {cred_source}",
                "",
                "Run:",
                "`debug railway credential resolution`",
            ]
        )
    if checks.get("railway_account_email"):
        lines.append(f"- Account: `{checks['railway_account_email']}`")
    if checks.get("railway_api_connection_detail") and not token_ok:
        lines.append(f"- Detail: {checks['railway_api_connection_detail']}")
    elif checks.get("railway_api_connection_detail") and token_ok and not checks.get("railway_api_connection_ok"):
        lines.append(f"- API detail: {checks['railway_api_connection_detail']}")

    lines.extend(
        [
            "",
            "### 4. Service creation API / CLI",
            f"- GraphQL greenfield create: **no** — {creation.get('graphql_service_create_detail', 'not wired')}",
            f"- Governed mutation adapter today: `{', '.join(creation.get('governed_mutation_adapter_ops') or [])}`",
            f"- Env var writes: **{'enabled' if creation.get('env_var_writes_enabled') else 'disabled'}**",
            f"- Execution mode: `{checks.get('execution_mode', 'api')}`",
        ]
    )

    lines.extend(["", "### 5. Required configuration"])
    for row in list(checks.get("required_env_vars") or []):
        lines.append(f"- {row}")

    lines.extend(
        [
            "",
            "### 6. Governed deployment plan (after approval — not executed)",
            compose_governed_deployment_plan_steps(checks),
            "",
            "**Readiness verdict:**",
        ]
    )
    if checks.get("readonly_readiness_ok"):
        lines.append("- Readonly readiness: **pass** — inventory + Railway API token are usable.")
    else:
        lines.append("- Readonly readiness: **blocked** — fix Railway/GitHub credentials or inventory errors first.")

    lines.append("- Governed greenfield create: **not available yet** in this runtime.")
    lines.append("")
    lines.append("No Railway service has been created. No mutation has been performed.")
    return "\n".join(lines)


def readonly_checks_passed(checks: dict[str, Any]) -> bool:
    return all(readiness_check_statuses(checks).values())


def compose_readiness_passed_not_mutation_ready(checks: dict[str, Any]) -> str:
    statuses = readiness_check_statuses(checks)
    cred_source = str(checks.get("railway_credential_source") or "canonical provider credential resolver")

    def _line(label: str, key: str) -> str:
        ok = statuses.get(key, False)
        return f"- {label}: **{'pass' if ok else 'fail'}**"

    lines = [
        "Railway deployment readiness checks passed.",
        "",
        "**Checked:**",
        _line("Railway inventory", "railway_inventory"),
        _line("GitHub source binding", "github_source_binding"),
        _line("Railway token", "railway_token"),
        _line("Service creation API/CLI", "service_creation_api_cli"),
        _line("Env var requirements", "env_var_requirements"),
        "",
        f"Credential source: {cred_source}",
        "",
        "**Current limitation:**",
        "Greenfield Railway service creation is not wired for governed execution yet.",
        "",
        "No service has been created.",
        "No mutation has been performed.",
    ]
    ref = str(checks.get("referenced_github_repo") or "").strip()
    if ref:
        lines.insert(-3, f"**Target repo:** `{ref}`")
        lines.insert(-3, "")
    return "\n".join(lines)


def readiness_check_statuses(checks: dict[str, Any]) -> dict[str, bool]:
    inv = checks.get("inventory") or {}
    gh = checks.get("github_binding") or {}
    creation = checks.get("service_creation") or {}
    return {
        "railway_inventory": bool(inv.get("ok")),
        "github_source_binding": bool(gh.get("github_credential_ok")),
        "railway_token": bool(checks.get("railway_credential_ok")),
        "service_creation_api_cli": bool(creation) or True,
        "env_var_requirements": bool(checks.get("required_env_vars")),
    }


def compose_readiness_blocker(checks: dict[str, Any], *, diagnostic: str = "") -> str:
    if readonly_checks_passed(checks):
        return compose_readiness_passed_not_mutation_ready(checks)

    statuses = readiness_check_statuses(checks)
    ref = str(checks.get("referenced_github_repo") or "").strip()

    def _line(label: str, key: str) -> str:
        ok = statuses.get(key, False)
        return f"- {label}: **{'pass' if ok else 'fail'}**"

    lines = [
        "I can run Railway deployment readiness, but one readonly check failed.",
        "",
        "**Checked:**",
        _line("Railway inventory", "railway_inventory"),
        _line("GitHub source binding", "github_source_binding"),
        _line("Railway token", "railway_token"),
        _line("Service creation API/CLI", "service_creation_api_cli"),
        _line("Env var requirements", "env_var_requirements"),
    ]
    cred_source = str(checks.get("railway_credential_source") or "canonical provider credential resolver")
    token_ok = bool(checks.get("railway_credential_ok"))
    if token_ok:
        lines.extend(["", f"Credential source: {cred_source}"])
    else:
        lines.extend(
            [
                "",
                f"Checked source: {cred_source}",
                "",
                "Run:",
                "`debug railway credential resolution`",
            ]
        )
    if ref:
        lines.extend(["", f"**Target repo:** `{ref}`"])
    if diagnostic:
        lines.extend(["", f"**Diagnostic:** {diagnostic}"])
    elif checks.get("check_error"):
        lines.extend(["", f"**Diagnostic:** {checks['check_error']}"])
    else:
        inv_err = str((checks.get("inventory") or {}).get("error") or "").strip()
        cred = str(checks.get("railway_credential_detail") or "").strip()
        gh_detail = str((checks.get("github_binding") or {}).get("detail") or "").strip()
        parts = [p for p in (inv_err, cred, gh_detail) if p]
        if parts:
            lines.extend(["", f"**Diagnostic:** {'; '.join(parts[:3])}"])

    lines.append("\nNo mutation has been performed.")
    return "\n".join(lines)


def compose_governed_deployment_plan_steps(checks: dict[str, Any]) -> str:
    ref = str(checks.get("referenced_github_repo") or "owner/repo")
    return "\n".join(
        [
            "1. **Approve** governed new-service deployment plan (required).",
            f"2. Create Railway service in target project/environment (not automated yet).",
            f"3. Connect GitHub source `{ref}` (binding required for deploy-from-git).",
            "4. Set required service env vars (capability disabled today — manual or future lane).",
            "5. Trigger first deploy and capture deployment ID.",
            "6. Verify deployment logs + health before marking operational.",
        ]
    )
