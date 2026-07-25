# SPDX-License-Identifier: Apache-2.0
"""Execution recovery engine — translate failures into recovery paths."""

from __future__ import annotations

from dataclasses import dataclass

from aethos_core.provider_e2e_readiness.blocker_mapping import ReadinessBlocker


@dataclass(frozen=True)
class RecoveryPath:
    blocker_code: str
    headline: str
    cause: str
    next_action: str
    recovery_steps: tuple[str, ...]
    safe_next_command: str
    can_continue_after_fix: bool = True
    post_recovery_steps: tuple[str, ...] = ()


_RECOVERY_CATALOG: dict[str, RecoveryPath] = {
    "RAILWAY_TOKEN_MISSING": RecoveryPath(
        blocker_code="RAILWAY_TOKEN_MISSING",
        headline="Railway token is not configured.",
        cause="AethOS could not resolve a Railway API token from provider connections.",
        next_action="Connect or configure a Railway API token in Mission Control → Advanced settings → Credentials.",
        recovery_steps=(
            "Open Mission Control → Advanced settings → Credentials",
            "Add Railway API token",
            "Run `validate Railway connection`",
        ),
        safe_next_command="show Railway connection status",
        post_recovery_steps=(
            "discover Railway project",
            "discover target service",
            "validate env readiness",
            "create deploy preflight",
        ),
    ),
    "RAILWAY_TOKEN_INVALID": RecoveryPath(
        blocker_code="RAILWAY_TOKEN_INVALID",
        headline="Railway token validation failed.",
        cause="The configured token was rejected by Railway.",
        next_action="Reconnect or replace the Railway token, then validate the connection.",
        recovery_steps=(
            "Reconnect Railway in Mission Control → Advanced settings → Credentials",
            "Validate Railway connection",
            "Retry deployment readiness",
        ),
        safe_next_command="validate Railway connection",
        post_recovery_steps=(
            "discover project",
            "discover service",
            "validate env vars",
            "create deploy preflight",
        ),
    ),
    "RAILWAY_RATE_LIMITED": RecoveryPath(
        blocker_code="RAILWAY_RATE_LIMITED",
        headline="Railway API is temporarily rate-limiting requests.",
        cause="Railway returned a rate-limit (HTTP 429). This is transient — the token is valid and configured.",
        next_action="Wait for the rate-limit window to clear, then retry. No credential change is needed.",
        recovery_steps=(
            "Wait for the Railway rate-limit window to clear",
            "Retry the deployment command",
        ),
        safe_next_command="show railway credential diagnostics",
        post_recovery_steps=(
            "discover Railway project",
            "discover target service",
            "validate env readiness",
            "create deploy preflight",
        ),
    ),
    "RAILWAY_API_CONNECTION_FAILED": RecoveryPath(
        blocker_code="RAILWAY_API_CONNECTION_FAILED",
        headline="Railway API connection could not be established.",
        cause="The Railway API connection failed for a reason other than auth or rate-limiting.",
        next_action="Verify network/API availability and retry. If it persists, revalidate the token.",
        recovery_steps=("Retry the readiness probe", "Check Railway status", "Validate Railway connection"),
        safe_next_command="show railway credential diagnostics",
    ),
    "RAILWAY_TARGET_SERVICE_MISSING": RecoveryPath(
        blocker_code="RAILWAY_TARGET_SERVICE_MISSING",
        headline="Railway target service could not be resolved.",
        cause="Multiple or zero services match the AethOS deployment target.",
        next_action="Specify the Railway project/environment/service explicitly.",
        recovery_steps=(
            "Run `show Railway projects`",
            "Identify the AethOS service name",
            "Retry with an explicit service target",
        ),
        safe_next_command="show Railway projects",
        post_recovery_steps=("validate env readiness", "create deploy preflight"),
    ),
    "RAILWAY_INVENTORY_UNAVAILABLE": RecoveryPath(
        blocker_code="RAILWAY_INVENTORY_UNAVAILABLE",
        headline="Railway inventory is unavailable.",
        cause="Project/service listing failed with the current token.",
        next_action="Verify token scopes and retry inventory.",
        recovery_steps=("Validate Railway connection", "Confirm project read access", "Retry discovery"),
        safe_next_command="show Railway projects",
    ),
    "MUTATION_EXECUTION_DISABLED": RecoveryPath(
        blocker_code="MUTATION_EXECUTION_DISABLED",
        headline="Governed mutations are disabled in this runtime.",
        cause="MUTATION_EXECUTION_ENABLED is false.",
        next_action="Enable mutation execution only in an approved environment.",
        recovery_steps=("Review runtime mutation policy", "Enable MUTATION_EXECUTION_ENABLED in approved env"),
        safe_next_command="show provider mutation readiness",
        can_continue_after_fix=True,
        post_recovery_steps=("create deploy preflight", "await Mission Control approval", "execute deployment"),
    ),
    "ENV_VAR_REFERENCE_MISSING": RecoveryPath(
        blocker_code="ENV_VAR_REFERENCE_MISSING",
        headline="Required environment variables are not ready.",
        cause="Secure store or env value readiness checks found missing keys.",
        next_action="Configure required env var keys through governed env readiness.",
        recovery_steps=("Run env value readiness", "Apply missing keys via approved preflight"),
        safe_next_command="show Railway env readiness",
        post_recovery_steps=("create deploy preflight", "execute deployment", "verify health"),
    ),
    "DEPLOYMENT_FAILED": RecoveryPath(
        blocker_code="DEPLOYMENT_FAILED",
        headline="Deployment did not succeed.",
        cause="The governed redeploy returned a failure state.",
        next_action="Inspect deployment logs and events before retrying.",
        recovery_steps=("Fetch deployment logs", "Review failure classifier output", "Retry after fix"),
        safe_next_command="show Railway deployment logs",
        post_recovery_steps=("redeploy after approval", "verify deployment"),
    ),
    "HEALTH_CHECK_FAILED": RecoveryPath(
        blocker_code="HEALTH_CHECK_FAILED",
        headline="Deployment verification failed.",
        cause="Health URL or deployment status check did not pass.",
        next_action="Inspect endpoint response and deployment events.",
        recovery_steps=("Check health URL", "Review deployment status", "Inspect recent logs"),
        safe_next_command="verify Railway deployment",
    ),
    "VERCEL_TOKEN_MISSING": RecoveryPath(
        blocker_code="VERCEL_TOKEN_MISSING",
        headline="Vercel token is not configured.",
        cause="No validated Vercel API token is available.",
        next_action="Connect Vercel in Mission Control → Advanced settings → Credentials.",
        recovery_steps=("Add Vercel token", "Validate connection"),
        safe_next_command="show Vercel connection status",
    ),
    "VERCEL_TOKEN_INVALID": RecoveryPath(
        blocker_code="VERCEL_TOKEN_INVALID",
        headline="Vercel token validation failed.",
        cause="Vercel API rejected the configured token.",
        next_action="Reconnect Vercel token and validate connection.",
        recovery_steps=("Reconnect token", "Validate connection"),
        safe_next_command="validate Vercel connection",
    ),
    "VERCEL_RATE_LIMITED": RecoveryPath(
        blocker_code="VERCEL_RATE_LIMITED",
        headline="Vercel API is temporarily rate-limiting requests.",
        cause="Vercel returned a rate-limit (HTTP 429). This is transient — the token is valid.",
        next_action="Wait for the rate-limit window to clear, then retry. No credential change is needed.",
        recovery_steps=("Wait for the Vercel rate-limit window to clear", "Retry the deployment command"),
        safe_next_command="validate Vercel connection",
    ),
}


def recovery_path_for_blocker(blocker: ReadinessBlocker) -> RecoveryPath:
    catalog = _RECOVERY_CATALOG.get(blocker.code)
    if catalog is not None:
        return catalog
    return RecoveryPath(
        blocker_code=blocker.code,
        headline=blocker.meaning,
        cause=blocker.likely_cause or blocker.meaning,
        next_action=blocker.required_action,
        recovery_steps=(blocker.required_action,),
        safe_next_command=blocker.safe_next_command,
    )


def compose_recovery_narrative(
    *,
    recovery: RecoveryPath,
    provider: str,
    post_recovery_preview: tuple[str, ...] | None = None,
) -> str:
    preview = post_recovery_preview or recovery.post_recovery_steps
    lines = [
        f"**{recovery.headline}**",
        "",
        "**Cause:**",
        recovery.cause,
        "",
        "**Next action:**",
        recovery.next_action,
        "",
        "**To continue:**",
    ]
    for idx, step in enumerate(recovery.recovery_steps, start=1):
        lines.append(f"{idx}. {step}")
    if preview and recovery.can_continue_after_fix:
        lines.extend(["", f"After that succeeds I can:", ""])
        for idx, step in enumerate(preview, start=1):
            lines.append(f"{idx}. {step}")
        lines.extend(
            [
                "",
                "Would you like me to continue once this is fixed?",
                "",
                f"Safe next command: `{recovery.safe_next_command}`",
            ]
        )
    else:
        lines.append("")
        lines.append(f"Safe next command: `{recovery.safe_next_command}`")
    lines.append("")
    lines.append(f"No {provider.title()} mutation has been performed.")
    return "\n".join(lines)


def compose_blocked_execution_reply(
    *,
    blockers: list[ReadinessBlocker],
    provider: str,
    post_recovery_preview: tuple[str, ...] | None = None,
) -> str:
    if not blockers:
        return ""
    recovery = recovery_path_for_blocker(blockers[0])
    return compose_recovery_narrative(
        recovery=recovery,
        provider=provider,
        post_recovery_preview=post_recovery_preview or recovery.post_recovery_steps,
    )
