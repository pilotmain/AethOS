# SPDX-License-Identifier: Apache-2.0
"""External capability jobs — read-only health checks (Phase 6)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from aethos_core.runtime.browser_jobs import should_preempt_external_health
from aethos_core.runtime.job_artifacts import build_artifact_bundle
from aethos_core.runtime.jobs import TrackedJob
from aethos_core.runtime.vercel_health import build_vercel_health_report

_EXTERNAL_HEALTH_RX = re.compile(
    r"\b(check|give me|is|run)\b.*\bvercel\b.*\b(health|status|services?)\b|"
    r"\bvercel\b.*\b(health|status)\s+(report|check)\b|"
    r"\bcheck\s+my\s+vercel\s+services\b|"
    r"\bis\s+vercel\s+healthy\b",
    re.I,
)

_LOGIN_VERCEL_RX = re.compile(
    r"\b(log\s*in\s+to|login\s+to|sign\s+in\s+to)\b.*\bvercel\b|"
    r"\bvercel\.com\b.*\b(login|sign\s*in|services?)\b|"
    r"\bvercel\b.*\b(login|sign\s*in)\b.*\b(service|dashboard)\b",
    re.I,
)

_CLI_STATUS_RX = re.compile(
    r"\b(check|probe|status)\b.*\bvercel\s+cli\b|"
    r"\bvercel\s+cli\b.*\b(status|check)\b",
    re.I,
)


@dataclass
class ExternalJobResult:
    full_result: str
    summary: str
    preview: str
    provider: str = "none"
    model: str = "external_health_report"
    tool_used: str = "external_health_report"
    sources: list[dict[str, Any]] | None = None
    mode: str = "public"

    @property
    def used_llm(self) -> bool:
        return False

    @property
    def fallback(self) -> bool:
        return False


def infer_external_health_mode(text: str, *, browser_requested: bool) -> str:
    lower = (text or "").lower()
    if _CLI_STATUS_RX.search(lower) and not _EXTERNAL_HEALTH_RX.search(lower):
        return "cli"
    if browser_requested:
        return "public"
    if "cli" in lower and "public" in lower:
        return "public+cli"
    if _CLI_STATUS_RX.search(lower):
        return "public+cli"
    return "public"


def infer_external_health_from_text(text: str) -> tuple[str, str, dict[str, Any]] | None:
    raw = (text or "").strip()
    lower = raw.lower()
    if not raw or "vercel" not in lower:
        return None
    from aethos_core.operational_session.railway_service_hints import should_defer_vercel_only_external_health

    if should_defer_vercel_only_external_health(raw):
        return None
    if should_preempt_external_health(raw):
        return None
    if re.search(r"\bdeploy\b", lower) and not re.search(r"\b(health|status)\b", lower):
        return None

    browser_requested = bool(_LOGIN_VERCEL_RX.search(raw))
    if _CLI_STATUS_RX.search(raw) and not browser_requested:
        return None
    health_intent = bool(_EXTERNAL_HEALTH_RX.search(raw)) or bool(
        re.search(r"\b(health|services?)\b", lower)
    ) or bool(re.search(r"\bvercel\b.*\bstatus\b", lower) and "cli" not in lower)
    if not browser_requested and not health_intent:
        return None

    mode = infer_external_health_mode(raw, browser_requested=browser_requested)
    title = "Vercel service health check"
    if browser_requested:
        title = "Vercel health (public sources; dashboard login not enabled)"
    return (
        title,
        "external_health_report",
        {
            "target": "vercel",
            "mode": mode,
            "user_request": raw,
            "browser_requested": browser_requested,
            "tool_used": "external_health_report",
        },
    )


def progress_message_for_external(job: TrackedJob) -> str:
    target = str(job.params.get("target") or "external")
    if target == "vercel":
        return "🌐 Checking public Vercel status…"
    return f"🌐 Running external health check — {job.title}…"


def run_external_health_job(job: TrackedJob) -> ExternalJobResult:
    target = str(job.params.get("target") or "vercel")
    mode = str(job.params.get("mode") or "public")
    user_request = str(job.params.get("user_request") or job.title)
    browser_requested = bool(job.params.get("browser_requested"))

    if target != "vercel":
        body = (
            f"# External health report\n\n"
            f"Target `{target}` is not supported yet. Phase 6 starts with **Vercel** only."
        )
        bundle = build_artifact_bundle(body, job_type=job.job_type, title=job.title)
        return ExternalJobResult(
            full_result=bundle.full_result,
            summary=bundle.summary,
            preview=bundle.preview,
            mode=mode,
        )

    report = build_vercel_health_report(
        mode=mode,
        user_request=user_request,
        browser_requested=browser_requested,
    )
    bundle = build_artifact_bundle(report.full_result, job_type=job.job_type, title=job.title)
    return ExternalJobResult(
        full_result=bundle.full_result,
        summary=bundle.summary,
        preview=bundle.preview,
        sources=report.sources,
        mode=report.mode,
    )
