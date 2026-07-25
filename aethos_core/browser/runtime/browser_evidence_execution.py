# SPDX-License-Identifier: Apache-2.0
"""Browser evidence job execution."""

from __future__ import annotations

from typing import Any

from aethos_core.browser.deployment_url_resolution import (
    is_deployment_evidence_prompt,
    resolve_deployment_evidence_target,
)
from aethos_core.browser.runtime.browser_artifacts import list_artifacts
from aethos_core.browser.runtime.browser_runtime import (
    extract_url_from_request,
    run_browser_evidence_capture,
    run_deployment_evidence_capture,
)


def execute_browser_evidence_job(job: Any) -> dict[str, Any]:
    params = job.params or {}
    user_request = str(params.get("user_request") or "")
    session_id = str(getattr(job, "session_id", "") or "default")
    operation = str(params.get("operation_type") or "")

    if operation == "browser_evidence_list":
        items = list_artifacts(limit=20)
        lines = ["**Browser evidence artifacts**", ""]
        if not items:
            lines.append("(no browser evidence artifacts yet)")
        else:
            for row in items[:10]:
                lines.append(
                    f"- `{row.get('artifact_id')}` · {row.get('artifact_type')} · "
                    f"{row.get('source_url') or '—'} · {row.get('capture_type')}"
                )
        summary = f"Browser evidence index — {len(items)} artifact(s)."
        return {"ok": True, "summary": summary, "full_result": "\n".join(lines), "artifacts": items}

    capture_type = str(params.get("capture_type") or "screenshot")
    approved = bool(params.get("approved", True))

    if params.get("blocked_request"):
        result = run_browser_evidence_capture(
            url=str(params.get("target_url") or "https://blocked.local"),
            capture_type=capture_type,
            session_id=session_id,
            user_request=user_request,
            approved=approved,
        )
    elif params.get("deployment_evidence") or is_deployment_evidence_prompt(user_request):
        target_info = resolve_deployment_evidence_target(user_request)
        if not target_info:
            return {
                "ok": False,
                "summary": "Could not resolve deployment evidence target.",
                "full_result": "Specify a service/project name or clarify the provider.",
            }
        provider, target = target_info
        if provider != "unknown":
            from aethos_core.connections.credential_runtime_gate import check_provider_credential_gate

            gate = check_provider_credential_gate(provider, require_validated=True)
            if not gate.get("ok"):
                detail = str(gate.get("detail") or "Credential reconnect required.")
                return {
                    "ok": False,
                    "summary": detail,
                    "full_result": detail,
                    "credential_gate": gate,
                }
        result = run_deployment_evidence_capture(
            user_request=user_request,
            provider=provider,
            target=target,
            session_id=session_id,
            approved=approved,
            capture_type="full" if capture_type in ("full", "deployment_evidence", "evidence") else capture_type,
        )
    else:
        url = str(params.get("target_url") or "") or extract_url_from_request(user_request)
        if not url:
            return {
                "ok": False,
                "summary": "Browser capture needs a target URL or domain.",
                "full_result": "Could not resolve target URL. Example: `capture screenshot of useinvoicepilot.com`",
            }
        result = run_browser_evidence_capture(
            url=url,
            capture_type=capture_type,
            session_id=session_id,
            user_request=user_request,
            approved=approved,
        )

    if result.get("metadata_only"):
        resolution = result.get("url_resolution") or {}
        lines = [
            result.get("summary") or "Deployment metadata evidence captured.",
            "",
            f"- Provider: {resolution.get('provider') or '—'}",
            f"- Target: {resolution.get('target') or '—'}",
            f"- Public URL: (none — {resolution.get('failure_reason') or 'no_public_url'})",
            f"- Artifacts: {len(result.get('artifacts') or [])}",
        ]
        return {
            "ok": True,
            "summary": result.get("summary") or "Deployment metadata evidence captured.",
            "full_result": "\n".join(lines),
            "browser_evidence": result,
        }

    if not result.get("ok"):
        detail = result.get("error") or (result.get("policy") or {}).get("detail") or "Browser capture failed."
        resolution = result.get("url_resolution") or {}
        if resolution.get("public_url"):
            detail = f"{detail}\nResolved URL: {resolution.get('public_url')}"
        return {
            "ok": False,
            "summary": "Browser capture blocked or failed.",
            "full_result": str(detail),
            "browser_evidence": result,
        }

    meta = result.get("metadata") or {}
    resolution = result.get("url_resolution") or {}
    lines = [
        result.get("summary") or "Browser evidence captured.",
        "",
        f"- URL: {meta.get('url') or resolution.get('public_url') or '—'}",
        f"- Title: {meta.get('title') or '—'}",
        f"- Status: {meta.get('status_code') or '—'}",
    ]
    if resolution.get("resolution_source"):
        lines.append(f"- Resolution source: {resolution.get('resolution_source')}")
    lines.append(f"- Artifacts: {len(result.get('artifacts') or [])}")
    for art in result.get("artifacts") or []:
        lines.append(f"  - `{art.get('artifact_id')}` · {art.get('artifact_type')}")
    return {
        "ok": True,
        "summary": result.get("summary") or "Browser evidence captured.",
        "full_result": "\n".join(lines),
        "browser_evidence": result,
    }
