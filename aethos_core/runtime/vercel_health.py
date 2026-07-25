# SPDX-License-Identifier: Apache-2.0
"""Read-only Vercel health sources — public status and CLI availability (no login)."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from time import time
from typing import Any

from aethos_core.runtime.authority import authority

VERCEL_STATUS_PAGE = "https://www.vercel-status.com/"
VERCEL_STATUS_API = "https://www.vercel-status.com/api/v2/status.json"


@dataclass
class HealthSource:
    type: str
    label: str
    available: bool
    checked_at: float
    detail: str = ""
    version: str = ""
    approval_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "type": self.type,
            "label": self.label,
            "available": self.available,
            "checked_at": self.checked_at,
        }
        if self.detail:
            out["detail"] = self.detail
        if self.version:
            out["version"] = self.version
        if self.approval_required:
            out["approval_required"] = True
        return out


@dataclass
class VercelHealthReport:
    full_result: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "public"


def _check_public_status() -> HealthSource:
    now = time()
    try:
        import httpx

        with httpx.Client(timeout=8.0, follow_redirects=True) as client:
            resp = client.get(VERCEL_STATUS_API)
        if resp.status_code != 200:
            return HealthSource(
                type="public_status",
                label="Vercel Status",
                available=False,
                checked_at=now,
                detail=f"HTTP {resp.status_code} from status API",
            )
        data = resp.json()
        indicator = str(data.get("status", {}).get("indicator", "unknown"))
        description = str(data.get("status", {}).get("description", "")).strip()
        detail = f"{indicator}: {description}" if description else indicator
        return HealthSource(
            type="public_status",
            label="Vercel Status",
            available=True,
            checked_at=now,
            detail=detail or "status API reachable",
        )
    except Exception as exc:
        return HealthSource(
            type="public_status",
            label="Vercel Status",
            available=False,
            checked_at=now,
            detail=(
                "Live public status fetch unavailable in this runtime. "
                f"Use the official page: {VERCEL_STATUS_PAGE} ({exc.__class__.__name__})."
            ),
        )


def _check_cli_availability(*, include_cli: bool) -> HealthSource:
    now = time()
    caps = authority.capabilities
    on_path = bool(caps.get("vercel_cli_on_path"))
    host = bool(caps.get("host_executor_enabled"))

    if not include_cli:
        return HealthSource(
            type="cli",
            label="Vercel CLI",
            available=on_path,
            checked_at=now,
            detail="CLI section skipped (public-only mode).",
        )

    if not on_path:
        return HealthSource(
            type="cli",
            label="Vercel CLI",
            available=False,
            checked_at=now,
            detail="Vercel CLI not found on PATH. Install: npm i -g vercel",
        )

    if not host:
        return HealthSource(
            type="cli",
            label="Vercel CLI",
            available=True,
            checked_at=now,
            detail="CLI detected on PATH; host executor disabled — enable for approved probes.",
            approval_required=True,
        )

    return HealthSource(
        type="cli",
        label="Vercel CLI",
        available=True,
        checked_at=now,
        detail=(
            "CLI detected. Read-only `vercel --version` / `which vercel` require "
            "**Mission Control approval** (vercel_cli_probe action)."
        ),
        approval_required=True,
    )


def _browser_source(*, requested: bool) -> HealthSource:
    now = time()
    caps = authority.capabilities
    enabled = bool(caps.get("browser_automation_enabled"))
    if not requested:
        return HealthSource(
            type="browser",
            label="Browser / dashboard",
            available=False,
            checked_at=now,
            detail="Not requested for this report.",
        )
    if enabled:
        return HealthSource(
            type="browser",
            label="Browser / dashboard",
            available=False,
            checked_at=now,
            detail=(
                "Browser automation is enabled, but authenticated dashboard review "
                "is not supported in Phase 6. Use public status or approved CLI checks."
            ),
            approval_required=True,
        )
    return HealthSource(
        type="browser",
        label="Browser / dashboard",
        available=False,
        checked_at=now,
        detail=(
            "Browser automation is not enabled. Authenticated dashboard login is not "
            "supported in this phase."
        ),
    )


def build_vercel_health_report(
    *,
    mode: str = "public",
    user_request: str = "",
    browser_requested: bool = False,
) -> VercelHealthReport:
    """Assemble a completed external health artifact (no credentials)."""
    include_cli = mode in {"cli", "public+cli", "full"}
    sources = [
        _check_public_status(),
        _check_cli_availability(include_cli=include_cli),
        _browser_source(requested=browser_requested),
    ]

    lines = [
        "# Vercel external health report",
        "",
        f"**Mode:** {mode}",
        f"**Checked at:** {time():.0f}",
        "",
    ]
    if user_request.strip():
        lines.append(f"**Request:** {user_request.strip()[:300]}")
        lines.append("")

    if browser_requested:
        lines.extend(
            [
                "## Authenticated dashboard",
                "",
                "Authenticated dashboard review is **not enabled** in this build. "
                "I can report public platform status and optional **approved** CLI probes.",
                "",
            ]
        )

    lines.append("## Sources")
    lines.append("")
    for src in sources:
        flag = "available" if src.available else "unavailable"
        lines.append(f"- **{src.label}** ({src.type}) — {flag}")
        if src.detail:
            lines.append(f"  - {src.detail}")
        if src.approval_required:
            lines.append("  - Approval required before running CLI commands.")
        lines.append("")

    lines.extend(
        [
            "## Manual links",
            "",
            f"- Public status: {VERCEL_STATUS_PAGE}",
            "- CLI setup: `npm i -g vercel` then `vercel login` (operator machine only)",
            "",
            "## Notes",
            "",
            "- No credentials were accessed.",
            "- No deployment commands were run.",
            "- Full artifact is stored in Mission Control → Jobs.",
        ]
    )

    if not shutil.which("vercel") and include_cli:
        lines.append("- Install the Vercel CLI for local project checks after approval.")

    return VercelHealthReport(
        full_result="\n".join(lines),
        sources=[s.to_dict() for s in sources],
        mode=mode,
    )
