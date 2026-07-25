# SPDX-License-Identifier: Apache-2.0
"""Railway credential resolution diagnostics — never print secret values."""

from __future__ import annotations

import re
from typing import Any

_CREDENTIAL_DEBUG_RX = re.compile(
    r"\b(?:debug|show)\s+railway\s+credential(?:\s+resolution|\s+diagnostics)?\b",
    re.I,
)


def is_railway_credential_debug_intent(text: str) -> bool:
    return bool(_CREDENTIAL_DEBUG_RX.search((text or "").strip()))


def diagnose_railway_credential_resolution() -> dict[str, Any]:
    from aethos_core.providers.railway.credential_truth import diagnose_railway_credential_truth

    return diagnose_railway_credential_truth()


def format_railway_credential_diagnostics_report(diag: dict[str, Any]) -> str:
    lines = [
        "**Railway Credential Diagnostics**",
        "",
        "### Resolution",
        f"- Credential source: **{diag.get('credential_source_label') or diag.get('credential_source') or 'none'}**",
        f"- Credential id: `{diag.get('credential_id') or '—'}`",
        f"- Masked identifier: `{diag.get('masked_identifier') or '—'}`",
        f"- Resolver: `{diag.get('resolver') or '—'}`",
        f"- Token resolved: **{'yes' if diag.get('token_resolved') else 'no'}**",
    ]
    if diag.get("resolution_detail") and diag.get("resolution_detail") != "ok":
        lines.append(f"- Resolution detail: {diag['resolution_detail']}")
    lines.extend(
        [
            "",
            "### Validation",
            f"- Validation probe: `{diag.get('validation_probe') or 'ProjectsAndServices'}`",
            f"- Readiness probe: `{diag.get('readiness_probe') or 'ProjectsAndServices'}`",
            f"- Endpoint: `{diag.get('validation_endpoint') or 'https://backboard.railway.app/graphql/v2'}`",
            f"- Live probe: **{'pass' if diag.get('connection_validation_ok') else 'fail'}**",
        ]
    )
    if diag.get("connection_validation_detail"):
        lines.append(f"- Probe detail: {diag['connection_validation_detail']}")
    lines.extend(
        [
            "",
            "### Trust alignment",
            f"- Connections gate validated: **{'yes' if diag.get('provider_gate_validated') else 'no'}**",
            f"- Gate state: `{diag.get('provider_gate_state') or 'unknown'}`",
            f"- UI/execution aligned: **{'yes' if diag.get('trust_aligned') else 'no'}**",
        ]
    )
    note = str(diag.get("trust_note") or "").strip()
    if note:
        lines.append(f"- Note: {note}")
    lines.extend(
        [
            "",
            "### Environment",
            f"- Environment token present: **{'yes' if diag.get('env_present') else 'no'}**",
            "",
            "No token value displayed.",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def route_railway_credential_diagnostics(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_railway_credential_debug_intent(text):
        return None
    diag = diagnose_railway_credential_resolution()
    body = format_railway_credential_diagnostics_report(diag)
    return body, "railway_credential_resolution_diagnostics", {
        "route_id": "railway_credential_diagnostics",
        "matched_module": "providers.railway.deployment_readiness.railway_credential_diagnostics",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "trust_aligned": "true" if diag.get("trust_aligned") else "false",
        "credential_source": str(diag.get("credential_source") or ""),
    }
