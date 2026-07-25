# SPDX-License-Identifier: Apache-2.0
"""Provider-aware preflight chat copy and missing-information questions."""

from __future__ import annotations

import re

from aethos_core.connections.adapters import auth_method_label_for_provider
from aethos_core.operations.operation_models import OperationPreflight
from aethos_core.operations.preflight_status import preflight_status_label


def _env_var_name_from_request(user_request: str) -> str | None:
    m = re.search(r"\b([A-Z][A-Z0-9_]{2,})\b", user_request or "")
    return m.group(1) if m else None


def missing_info_questions(preflight: OperationPreflight, *, user_request: str = "") -> list[str]:
    questions: list[str] = []
    missing = set(preflight.missing_information or [])

    if (
        preflight.operation_type == "set_env_var"
        or "exact_env_value_confirmation" in missing
        or "environment_target" in missing
    ):
        var = _env_var_name_from_request(user_request)
        var_label = f"`{var}`" if var else "the variable"
        questions.append(f"What value should {var_label} be set to?")
        questions.append(
            "Which environment: Production, Preview, Development, or all?"
        )

    if "explicit_repo_path" in missing and preflight.provider == "local":
        questions.append(
            "Confirm repo path, or permission to use the canonical AethOS workspace."
        )

    if "confirm_root_cause_before_redeploy" in missing:
        questions.append("Confirm root cause before redeploy if the latest deployment failed.")

    if "target_project" in missing:
        questions.append("Which target project should this operation apply to?")

    if "fresh_inventory" in missing and preflight.target_status != "blocked_by_browser_runtime":
        questions.append("Run `show my Vercel apps` to refresh inventory first.")

    if "production_url_not_in_memory" in missing:
        questions.append("Production URL is not confirmed — verify live dashboard state.")

    if "live_dashboard_confirmation" in missing:
        questions.append("Confirm live dashboard state before treating the app as down.")

    return questions


def chat_summary_for_preflight(preflight: OperationPreflight, *, user_request: str = "") -> str:
    if preflight.provider == "local":
        return _local_summary(preflight, user_request=user_request)
    if preflight.provider == "vercel":
        return _vercel_summary(preflight, user_request=user_request)
    if preflight.provider == "railway":
        return _railway_summary(preflight, user_request=user_request)
    if preflight.provider == "github":
        return _github_summary(preflight, user_request=user_request)
    return _generic_summary(preflight)


def _auth_path_phrase(preflight: OperationPreflight) -> str:
    cap = preflight.current_state or {}
    if cap.get("api_capable"):
        method = str(cap.get("auth_method") or "api_token")
        label = str(cap.get("auth_method_label") or "") or auth_method_label_for_provider(
            preflight.provider, method
        )
        return f" · **Auth path:** {label} · **Browser required:** no"
    if cap.get("browser_fallback_available") and not cap.get("browser_runtime_required"):
        return " · **Browser fallback:** optional (API-first)"
    return ""


def _status_footer(preflight: OperationPreflight) -> str:
    status = preflight_status_label(preflight.preflight_status)
    auth_path = _auth_path_phrase(preflight)
    if preflight.preflight_status == "blocked":
        return (
            f"**Status:** {status} · **Risk:** {preflight.risk_level} · "
            "Execution is currently blocked until browser runtime is healthy."
        )
    return (
        f"**Status:** {status} · **Risk:** {preflight.risk_level}{auth_path} · "
        "**Approval required** for read-only execution. Mutations remain disabled."
    )


def _local_summary(preflight: OperationPreflight, *, user_request: str = "") -> str:
    root = str(preflight.current_state.get("workspace_root") or preflight.target_name or "")
    lines = [
        f"I prepared a **read-only local workspace preflight** for `{root}`.",
        "",
        "**Preflight will check:**",
    ]
    for step in preflight.proposed_steps[:5]:
        lines.append(f"- {step}")
    questions = missing_info_questions(preflight, user_request=user_request)
    if questions:
        lines.extend(["", "**I still need:**"])
        for q in questions:
            lines.append(f"- {q}")
    lines.extend(["", _status_footer(preflight)])
    return "\n".join(lines)


def _down_diagnostic_intro(preflight: OperationPreflight) -> str:
    target = preflight.target_name or "(unresolved)"
    state = preflight.current_state or {}
    evidence = list(state.get("evidence") or [])
    prod_health = str(state.get("production_health") or "")
    op_status = str(state.get("operator_status") or "")
    deploy_state = str(state.get("latest_deployment_state") or "")
    prod_url = state.get("production_url")

    if prod_health == "down" and "scope_detected: production" in evidence:
        return (
            f"**Production failure detected** for `{target}` in the latest inventory."
        )
    if deploy_state == "failed":
        if "scope_detected: production" in evidence:
            return f"**Latest deployment failure detected** for `{target}` (production scope)."
        return (
            f"I found `{target}`, but **production impact is unclear** — "
            "latest deployment failed without confirmed production scope."
        )
    if op_status == "unknown" or prod_health == "unknown" or not prod_url:
        return (
            f"I do **not yet have enough evidence** that `{target}` is down. "
            "I'll run a diagnostic preflight to inspect latest deployment, production URL, and logs."
        )
    if op_status == "healthy" or prod_health == "healthy":
        return (
            f"Latest inventory does **not** show `{target}` as down — "
            "I'll verify live state before assuming an outage."
        )
    return f"I prepared a **read-only diagnostic preflight** for `{target}`."


def _vercel_summary(preflight: OperationPreflight, *, user_request: str = "") -> str:
    target = preflight.target_name or "(unresolved)"

    if preflight.target_status == "ambiguous":
        return (
            "I found multiple possible Vercel project matches. "
            "Please specify the target project."
        )
    if preflight.target_status == "blocked_by_browser_runtime":
        cap = preflight.current_state or {}
        if cap.get("api_capable"):
            lines = [
                "Browser automation is unavailable, but this operation can run through your **Vercel API token**.",
                "",
                "**Preflight will check:**",
            ]
            for step in preflight.proposed_steps[:5]:
                lines.append(f"- {step}")
            lines.extend(["", _status_footer(preflight)])
            return "\n".join(lines)
        headline = (
            preflight.blockers[0]
            if preflight.blockers
            else (
                "I have a saved Vercel session, but I cannot refresh inventory because "
                "browser execution is blocked by an AethOS runtime issue."
            )
        )
        lines = [headline, "", "**Blocked until browser runtime is fixed:**"]
        for step in preflight.proposed_steps[:4]:
            lines.append(f"- {step}")
        lines.extend(["", _status_footer(preflight)])
        return "\n".join(lines)

    if preflight.target_status == "missing":
        return (
            "I could not find that project in saved Vercel inventory. "
            "Run `show my Vercel apps` first."
        )

    op = preflight.operation_type
    cap = preflight.current_state or {}
    lines: list[str]
    if op in ("why_down", "inspect_failed_deployment"):
        lines = [_down_diagnostic_intro(preflight), ""]
        if cap.get("browser_fallback_available") and not cap.get("browser_runtime_required"):
            lines.append(
                "I can run the API-backed portion now. Browser log fallback may be unavailable if Playwright is blocked."
            )
            lines.append("")
    else:
        op_label = op.replace("_", " ")
        source = cap.get("resolution_source") or "inventory"
        source_label = "Vercel API" if source == "provider_api" else "saved inventory"
        lines = [
            f"I found `{target}` via your **{source_label}**.",
            "",
            f"Created a **read-only preflight** before any {op_label}.",
            "",
        ]
        if cap.get("api_capable"):
            lines.append("**Auth path:** Vercel API token · **Browser required:** no")
            lines.append("")

    lines.append("**Preflight will check:**")
    for step in preflight.proposed_steps[:5]:
        lines.append(f"- {step}")

    questions = missing_info_questions(preflight, user_request=user_request)
    if questions:
        lines.extend(["", "**I still need:**"])
        for q in questions:
            lines.append(f"- {q}")

    lines.extend(["", _status_footer(preflight)])
    return "\n".join(lines)


def _railway_summary(preflight: OperationPreflight, *, user_request: str = "") -> str:
    target = preflight.target_name or "(unresolved)"
    op_label = preflight.operation_type.replace("_", " ")

    if preflight.target_status == "ambiguous":
        return (
            "I found multiple possible Railway service matches. "
            "Please specify the target service and project."
        )
    if preflight.target_status == "missing":
        return (
            "I could not find that service in Railway inventory. "
            "Run `show my Railway apps` first or use an explicit service name."
        )

    lines = [
        f"Created a **read-only preflight** for `{target}` (railway).",
        "",
        f"**Operation:** {op_label}",
        "",
    ]
    cap = preflight.current_state or {}
    if cap.get("api_capable"):
        method = str(cap.get("auth_method") or "api_token")
        label = str(cap.get("auth_method_label") or "") or auth_method_label_for_provider("railway", method)
        lines.extend([f"**Auth path:** {label} · **Browser required:** no", ""])

    lines.append("**Preflight will check:**")
    for step in preflight.proposed_steps[:5]:
        lines.append(f"- {step}")

    questions = missing_info_questions(preflight, user_request=user_request)
    if questions:
        lines.extend(["", "**I still need:**"])
        for q in questions:
            lines.append(f"- {q}")

    lines.extend(["", _status_footer(preflight)])
    return "\n".join(lines)


def _github_summary(preflight: OperationPreflight, *, user_request: str = "") -> str:
    target = preflight.target_name or "(unresolved)"
    op_label = preflight.operation_type.replace("_", " ")

    if preflight.target_status == "ambiguous":
        return (
            "I found multiple possible GitHub repository matches. "
            "Please specify the target repository as owner/repo or a unique name."
        )
    if preflight.target_status == "missing":
        return (
            "I could not find that repository in GitHub inventory. "
            "Run `show my github repositories` first or use an explicit repository name."
        )

    lines = [
        f"Created a **read-only preflight** for `{target}` (github).",
        "",
        f"**Operation:** {op_label}",
        "",
    ]
    cap = preflight.current_state or {}
    if cap.get("api_capable"):
        method = str(cap.get("auth_method") or "api_token")
        label = str(cap.get("auth_method_label") or "") or auth_method_label_for_provider("github", method)
        lines.extend([f"**Auth path:** {label} · **Browser required:** no", ""])

    lines.append("**Preflight will check:**")
    for step in preflight.proposed_steps[:5]:
        lines.append(f"- {step}")

    questions = missing_info_questions(preflight, user_request=user_request)
    if questions:
        lines.extend(["", "**I still need:**"])
        for q in questions:
            lines.append(f"- {q}")

    lines.extend(["", _status_footer(preflight)])
    return "\n".join(lines)


def _generic_summary(preflight: OperationPreflight) -> str:
    target = preflight.target_name or "(unresolved)"
    op_label = preflight.operation_type.replace("_", " ")
    lines = [
        f"Created a **read-only preflight** for `{target}` ({preflight.provider}).",
        "",
        f"**Operation:** {op_label}",
        "",
        _status_footer(preflight),
    ]
    return "\n".join(lines)
