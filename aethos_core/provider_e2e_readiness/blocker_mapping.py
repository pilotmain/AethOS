# SPDX-License-Identifier: Apache-2.0
"""Map provider readiness failures to actionable blocker codes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

ProviderKind = Literal["railway", "vercel"]

_NOT_AUTHORIZED_RX = re.compile(
    r"\b(not\s+authorized|unauthorized|invalid\s+token|authentication\s+failed|forbidden|401|403)\b",
    re.I,
)

# Transient throttling — the token is fine, the API is rate-limiting us. Must never be
# misclassified as an invalid/missing credential (see providers/cloud/validators.py:
# "on a network blip we accept the stored key so a transient outage never blocks a valid key").
_RATE_LIMITED_RX = re.compile(
    r"(rate[\s_-]*limit|too\s+many\s+requests|try\s+again\s+in|throttl|\b429\b)",
    re.I,
)


def is_rate_limited_detail(detail: str, *, status_code: int | None = None) -> bool:
    """True when a provider failure is a transient rate-limit/throttle, not a bad credential."""
    if status_code == 429:
        return True
    return bool(_RATE_LIMITED_RX.search(str(detail or "")))


def is_auth_rejection_detail(detail: str, *, status_code: int | None = None) -> bool:
    """True only for a clean auth rejection (bad/expired token), never for a rate-limit."""
    if is_rate_limited_detail(detail, status_code=status_code):
        return False
    if status_code in (401, 403):
        return True
    return bool(_NOT_AUTHORIZED_RX.search(str(detail or "")))


@dataclass(frozen=True)
class ReadinessBlocker:
    code: str
    meaning: str
    required_action: str
    safe_next_command: str
    authorization_type: str = ""
    failed_check: str = ""
    likely_cause: str = ""


def format_blocker_entry(blocker: ReadinessBlocker, *, index: int | None = None) -> str:
    prefix = f"{index}. " if index is not None else "- "
    lines = [
        f"{prefix}**{blocker.code}**",
        f"   {blocker.meaning}",
        f"   Required action: {blocker.required_action}",
        f"   Safe next command: `{blocker.safe_next_command}`",
    ]
    if blocker.authorization_type:
        lines.insert(2, f"   Authorization type: {blocker.authorization_type}")
    if blocker.failed_check:
        lines.insert(3 if blocker.authorization_type else 2, f"   Failed check: {blocker.failed_check}")
    if blocker.likely_cause:
        lines.insert(-2, f"   Likely cause: {blocker.likely_cause}")
    return "\n".join(lines)


def collect_safe_next_commands(blockers: list[ReadinessBlocker], *, extra: list[str] | None = None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for blocker in blockers:
        cmd = blocker.safe_next_command.strip()
        if cmd and cmd not in seen:
            seen.add(cmd)
            out.append(cmd)
    for cmd in extra or []:
        normalized = cmd.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out


def map_railway_blockers(
    checks: dict[str, Any],
    *,
    settings: Any,
    target_resolved: bool | None = None,
    include_mutation_gates: bool = True,
) -> list[ReadinessBlocker]:
    blockers: list[ReadinessBlocker] = []

    if not checks.get("railway_credential_ok"):
        blockers.append(
            ReadinessBlocker(
                code="RAILWAY_TOKEN_MISSING",
                meaning="Railway API token is not configured.",
                required_action=(
                    "Add Railway token through provider connection settings or secure runtime configuration."
                ),
                safe_next_command="show Railway connection status",
                authorization_type="provider_api_token",
                failed_check="railway_credential_resolver",
                likely_cause=str(checks.get("railway_credential_detail") or "No token resolved."),
            )
        )
        return blockers

    if not checks.get("railway_api_connection_ok"):
        detail = str(checks.get("railway_api_connection_detail") or "Railway API connection failed.")
        status_code = checks.get("railway_api_connection_status_code")
        rate_limited = is_rate_limited_detail(detail, status_code=status_code)
        invalid = is_auth_rejection_detail(detail, status_code=status_code)
        if rate_limited:
            blockers.append(
                ReadinessBlocker(
                    code="RAILWAY_RATE_LIMITED",
                    meaning="Railway API is rate-limiting requests — this is transient and the token is still valid.",
                    required_action=(
                        "Wait for the Railway rate-limit window to clear, then retry. "
                        "No need to replace or reconnect the token."
                    ),
                    safe_next_command="show railway credential diagnostics",
                    authorization_type="provider_api_token",
                    failed_check="railway_api_connection",
                    likely_cause=detail,
                )
            )
        else:
            trust_note = ""
            if invalid and str(checks.get("railway_credential_source") or "") in {"validated_vault", "explicit_credential"}:
                trust_note = (
                    " Connections shows validated but live probe failed — token may have changed, been revoked, or expired."
                )
            blockers.append(
                ReadinessBlocker(
                    code="RAILWAY_TOKEN_INVALID" if invalid else "RAILWAY_API_CONNECTION_FAILED",
                    meaning=(
                        "Railway API rejected the configured token."
                        if invalid
                        else "Railway API connection could not be established with the configured token."
                    ),
                    required_action=(
                        ("Replace or reconnect Railway token in Connections." if invalid else "Verify Railway token and retry connection.")
                        + trust_note
                    ),
                    safe_next_command="show railway credential diagnostics",
                    authorization_type="provider_api_token",
                    failed_check="railway_api_connection",
                    likely_cause=(
                        "Railway GraphQL authorization failed (ProjectsAndServices probe)."
                        if invalid
                        else detail
                    ),
                )
            )

    inv = checks.get("inventory") or {}
    if checks.get("railway_credential_ok") and checks.get("railway_api_connection_ok") and not inv.get("ok"):
        inv_err = str(inv.get("error") or "Railway project/service discovery failed.").strip()
        cred_source = checks.get("railway_credential_source_label") or checks.get("railway_credential_source") or "unknown"
        validation_probe = checks.get("railway_validation_probe") or "ProjectsAndServices"
        inventory_probe = inv.get("inventory_probe") or "ProjectsEnvironmentsServices"
        blockers.append(
            ReadinessBlocker(
                code="RAILWAY_INVENTORY_UNAVAILABLE",
                meaning="Railway project/service discovery failed.",
                required_action=(
                    f"Credential source: {cred_source}. "
                    f"Validation probe ({validation_probe}): "
                    f"{'pass' if checks.get('railway_api_connection_ok') else 'fail'}. "
                    f"Inventory probe ({inventory_probe}): fail. "
                    f"Detail: {inv_err[:180]}"
                ),
                safe_next_command="show railway credential diagnostics",
                failed_check="railway_inventory",
                likely_cause=inv_err[:240] or "inventory probe failed",
            )
        )

    if target_resolved is False:
        blockers.append(
            ReadinessBlocker(
                code="RAILWAY_TARGET_SERVICE_MISSING",
                meaning="AethOS could not resolve the Railway project/service/environment target.",
                required_action="Configure target project/service/environment mapping.",
                safe_next_command="show Railway projects",
                failed_check="target_resolution",
                likely_cause=f"Inventory shows {inv.get('service_count', 0)} service(s).",
            )
        )

    if include_mutation_gates and settings is not None and not getattr(settings, "mutation_execution_enabled", False):
        blockers.append(
            ReadinessBlocker(
                code="MUTATION_EXECUTION_DISABLED",
                meaning="Provider mutations are disabled by runtime configuration.",
                required_action="Enable MUTATION_EXECUTION_ENABLED only in an approved environment.",
                safe_next_command="show provider mutation readiness",
                authorization_type="runtime_mutation_gate",
                failed_check="mutation_execution_enabled",
                likely_cause="MUTATION_EXECUTION_ENABLED is false.",
            )
        )

    return blockers


def map_vercel_blockers(
    *,
    credential_ok: bool,
    credential_detail: str = "",
    connection_ok: bool = True,
    connection_detail: str = "",
    project_resolved: bool | None = None,
    project_count: int = 0,
    settings: Any = None,
    include_mutation_gates: bool = True,
) -> list[ReadinessBlocker]:
    blockers: list[ReadinessBlocker] = []

    if not credential_ok:
        blockers.append(
            ReadinessBlocker(
                code="VERCEL_TOKEN_MISSING",
                meaning="Vercel API token is not configured or validated.",
                required_action="Connect Vercel through provider connection settings or secure runtime configuration.",
                safe_next_command="show Vercel connection status",
                authorization_type="provider_api_token",
                failed_check="vercel_credential_resolver",
                likely_cause=credential_detail or "No validated Vercel token resolved.",
            )
        )
        return blockers

    if not connection_ok:
        if is_rate_limited_detail(connection_detail):
            blockers.append(
                ReadinessBlocker(
                    code="VERCEL_RATE_LIMITED",
                    meaning="Vercel API is rate-limiting requests — this is transient and the token is still valid.",
                    required_action="Wait for the Vercel rate-limit window to clear, then retry. No need to replace the token.",
                    safe_next_command="validate Vercel connection",
                    authorization_type="provider_api_token",
                    failed_check="vercel_api_connection",
                    likely_cause=connection_detail or "rate limited",
                )
            )
        else:
            invalid = is_auth_rejection_detail(connection_detail)
            blockers.append(
                ReadinessBlocker(
                    code="VERCEL_TOKEN_INVALID" if invalid else "VERCEL_API_CONNECTION_FAILED",
                    meaning=(
                        "Vercel API rejected the configured token."
                        if invalid
                        else "Vercel API connection could not be established."
                    ),
                    required_action="Replace or reconnect Vercel token." if invalid else "Verify Vercel token scopes and retry.",
                    safe_next_command="validate Vercel connection",
                    authorization_type="provider_api_token",
                    failed_check="vercel_api_connection",
                    likely_cause=connection_detail or "project listing failed",
                )
            )

    if connection_ok and project_count == 0:
        blockers.append(
            ReadinessBlocker(
                code="VERCEL_TARGET_PROJECT_MISSING",
                meaning="No Vercel projects are visible for the configured token.",
                required_action="Link or create a Vercel project for AethOS deployment.",
                safe_next_command="show Vercel projects",
                failed_check="vercel_project_inventory",
                likely_cause="Token has no accessible projects.",
            )
        )
    elif project_resolved is False:
        blockers.append(
            ReadinessBlocker(
                code="VERCEL_TARGET_PROJECT_AMBIGUOUS",
                meaning="Multiple Vercel projects found — AethOS could not auto-select a deployment target.",
                required_action="Specify the target Vercel project name explicitly.",
                safe_next_command="show Vercel deployment readiness",
                failed_check="target_resolution",
                likely_cause=f"{project_count} project(s) visible.",
            )
        )

    if include_mutation_gates and settings is not None and not getattr(settings, "mutation_execution_enabled", False):
        blockers.append(
            ReadinessBlocker(
                code="MUTATION_EXECUTION_DISABLED",
                meaning="Provider mutations are disabled by runtime configuration.",
                required_action="Enable MUTATION_EXECUTION_ENABLED only in an approved environment.",
                safe_next_command="show provider mutation readiness",
                authorization_type="runtime_mutation_gate",
                failed_check="mutation_execution_enabled",
            )
        )

    return blockers


def map_plain_text_blocker(text: str, *, provider: ProviderKind) -> ReadinessBlocker:
    """Fallback when only a legacy plain-string blocker is available."""
    raw = (text or "").strip()
    if is_rate_limited_detail(raw):
        prefix = provider.upper()
        return ReadinessBlocker(
            code=f"{prefix}_RATE_LIMITED",
            meaning=f"{provider.title()} API is rate-limiting requests — transient, the token is still valid.",
            required_action="Wait for the rate-limit window to clear, then retry. No need to replace the token.",
            safe_next_command=f"show {provider.title()} deployment readiness",
            authorization_type="provider_api_token",
            failed_check=f"{provider}_api_connection",
            likely_cause=raw,
        )
    if is_auth_rejection_detail(raw):
        if provider == "railway":
            return ReadinessBlocker(
                code="RAILWAY_TOKEN_INVALID",
                meaning="Railway API rejected the configured token.",
                required_action="Replace or reconnect Railway token.",
                safe_next_command="validate Railway connection",
                authorization_type="provider_api_token",
                failed_check="railway_api_connection",
                likely_cause=raw,
            )
        return ReadinessBlocker(
            code="VERCEL_TOKEN_INVALID",
            meaning="Vercel API rejected the configured token.",
            required_action="Replace or reconnect Vercel token.",
            safe_next_command="validate Vercel connection",
            authorization_type="provider_api_token",
            failed_check="vercel_api_connection",
            likely_cause=raw,
        )
    prefix = provider.upper()
    return ReadinessBlocker(
        code=f"{prefix}_CONFIGURATION_BLOCKED",
        meaning=raw or "Provider configuration is incomplete.",
        required_action="Resolve the reported configuration issue before retrying.",
        safe_next_command=f"show {provider.title()} deployment readiness",
        failed_check="configuration",
        likely_cause=raw,
    )
