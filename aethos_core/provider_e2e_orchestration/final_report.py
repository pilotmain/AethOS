# SPDX-License-Identifier: Apache-2.0
"""Final user-facing provider E2E report."""

from __future__ import annotations

from typing import Any

from aethos_core.security.secret_redaction import redact_text, redact_value


def compose_provider_e2e_final_report(
    *,
    provider: str,
    evidence: dict[str, Any],
    execution_status: str,
    completion_advisory_text: str = "",
) -> str:
    lines = [
        f"# {provider.title()} E2E orchestration — final report",
        "",
        f"**Status:** `{execution_status}`",
        "",
        "## Applied",
    ]
    applied = list(evidence.get("env_applied_names") or [])
    if applied:
        lines.append(f"- Env var names applied: {', '.join(f'`{n}`' for n in applied)}")
    else:
        lines.append("- No env vars applied (skipped or none configured).")

    lines.extend(["", "## Deployed"])
    dep_id = evidence.get("deployment_id")
    if dep_id:
        lines.append(f"- Deployment ID: `{dep_id}`")
    poll_state = evidence.get("final_poll_state")
    if poll_state:
        lines.append(f"- Poll result: **{poll_state}**")

    lines.extend(["", "## Verified"])
    verification = evidence.get("verification") or {}
    if verification.get("url"):
        lines.append(f"- Health URL: {verification['url']}")
    if verification.get("status_code") is not None:
        lines.append(f"- HTTP status: `{verification['status_code']}`")
    lines.append(f"- Verification: **{'pass' if verification.get('ok') else 'fail or skipped'}**")

    final_url = evidence.get("deployment_url") or verification.get("url")
    if final_url:
        lines.extend(["", f"**Final URL:** {final_url}"])

    errors = list(evidence.get("errors") or [])
    if errors:
        lines.extend(["", "## Failures", ""])
        for err in errors[:6]:
            lines.append(f"- {err}")

    if completion_advisory_text:
        lines.extend(["", "---", "", completion_advisory_text])
    elif errors:
        lines.extend(["", "**Next action:** Review Mission Control → Jobs, fix blockers, and re-run with approval."])
    elif execution_status == "completed":
        lines.extend(["", "Governed E2E chain finished. No secret values are included in this report."])

    return redact_text("\n".join(lines))


def build_final_report_payload(
    *,
    full_report: str,
    evidence: dict[str, Any],
    execution_status: str,
) -> dict[str, Any]:
    return {
        "execution_status": execution_status,
        "evidence": redact_value(evidence),
        "full_report": redact_text(full_report),
        "summary": _summary_line(execution_status, evidence),
    }


def _summary_line(execution_status: str, evidence: dict[str, Any]) -> str:
    if execution_status == "completed":
        return f"E2E completed — deployment `{evidence.get('deployment_id') or 'n/a'}`."
    advisory = evidence.get("completion_advisory") if isinstance(evidence.get("completion_advisory"), dict) else {}
    root = str(advisory.get("root_cause") or "").strip()
    if root:
        return root[:240]
    return f"E2E {execution_status} — see final report for details."
