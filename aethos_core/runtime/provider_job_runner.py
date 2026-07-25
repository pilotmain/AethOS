# SPDX-License-Identifier: Apache-2.0
"""Provider-backed tracked job execution with timeout and fallback."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass

from aethos_core.config import get_settings
from aethos_core.provider.completion import ProviderResult, complete_chat, provider_configured
from aethos_core.runtime.job_artifacts import build_artifact_bundle
from aethos_core.runtime.jobs import TrackedJob

EMPTY_PROVIDER_RESPONSE = "Provider returned an empty response."


class ProviderJobTimeoutError(TimeoutError):
    """Provider call exceeded JOB_PROVIDER_TIMEOUT_SEC."""


class ProviderJobFailure(Exception):
    """Provider is configured but did not return usable output."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass
class ProviderJobResult:
    full_result: str
    summary: str
    preview: str
    provider: str
    model: str
    used_llm: bool
    fallback: bool

    @property
    def text(self) -> str:
        """Backward-compatible alias for full artifact body."""
        return self.full_result


def progress_message_for(job: TrackedJob) -> str:
    jt = job.job_type
    title = job.title
    if jt == "comparison_brief":
        return f"🧠 Researching competitors — {title}…"
    if jt == "research_plan":
        return f"🧠 Researching — {title}…"
    if jt == "roadmap_generation":
        return "🧠 Organizing roadmap…"
    if jt == "architecture_summary":
        return "🧠 Drafting architecture summary…"
    if jt == "planning_document":
        return "🧠 Drafting planning document…"
    return f"🧠 Working on {title}…"


def build_provider_prompt(job: TrackedJob) -> str:
    topic = str(job.params.get("topic") or job.title)
    user_request = str(job.params.get("user_request") or topic)
    jt = job.job_type
    if jt == "comparison_brief":
        return (
            "You are AethOS. Produce a concise competitor comparison brief for the operator.\n"
            f"Request: {user_request}\n\n"
            "Include: named competitors (if known), positioning, strengths/weaknesses, "
            "and relevance to AethOS. Use markdown headings and bullets. Stay factual and calm."
        )
    if jt == "research_plan":
        return (
            "You are AethOS. Produce a structured research plan the operator can execute.\n"
            f"Topic: {topic}\n\n"
            "Sections: goal, scope, sources, steps, risks, verification. Markdown only."
        )
    if jt == "roadmap_generation":
        return (
            "You are AethOS. Draft an MVP roadmap for the AethOS rebuild.\n"
            f"Context: {user_request}\n\n"
            "Phases should be small, test-gated, chat-first. Markdown headings and bullets."
        )
    if jt == "architecture_summary":
        return (
            "You are AethOS. Summarize the current AethOS architecture for an operator.\n"
            f"Focus: {user_request}\n\n"
            "Cover: chat, runtime authority, Mission Control, actions, tracked jobs. Markdown."
        )
    if jt == "planning_document":
        return (
            "You are AethOS. Draft a short planning document.\n"
            f"Request: {user_request}\n\n"
            "Include objective, constraints, milestones, and verification. Markdown."
        )
    return f"You are AethOS. Complete this tracked work request:\n{user_request}"


def _fallback_body(job: TrackedJob) -> str:
    topic = str(job.params.get("topic") or job.title)
    user_request = str(job.params.get("user_request") or topic)
    jt = job.job_type
    if jt == "comparison_brief":
        return (
            f"# Competitor brief (fallback): {topic}\n\n"
            "- **Tool-loop agents** — runtime with governed tool use; primary AethOS Phase 1 pattern.\n"
            "- **LangGraph / agent frameworks** — graph orchestration; heavier than MVP scope.\n"
            "- **PI / personal agents** — consumer UX; less operator-control focus.\n\n"
            f"Original request: {user_request}"
        )
    if jt == "roadmap_generation":
        return (
            "# MVP roadmap (fallback)\n\n"
            "1. Chat MVP + deterministic lane\n"
            "2. Mission Control observational panels\n"
            "3. Approved runtime actions + lifecycle feedback\n"
            "4. Tracked jobs + provider-backed work\n"
            "5. Browser jobs (later)\n"
        )
    if jt == "architecture_summary":
        return (
            "# Architecture summary (fallback)\n\n"
            "- **Chat** — primary UX, non-blocking\n"
            "- **Runtime authority** — health, capabilities, actions, jobs\n"
            "- **Mission Control** — observational Jobs/Runtime/Settings\n"
            "- **Event polling** — chat lifecycle bridge (MVP)\n"
        )
    if jt == "planning_document":
        return (
            f"# Planning document (fallback): {topic}\n\n"
            "**Objective** — Ship reliable operator-facing milestones.\n"
            "**Constraints** — No hidden workers; test-gated phases.\n"
            "**Verification** — Manual gate + pytest per phase.\n"
        )
    return (
        f"# Research plan (fallback): {topic}\n\n"
        "1. Define outcome\n2. List constraints\n3. Break into test-gated slices\n"
        "4. Report in chat + Mission Control\n"
    )


def fallback_result(job: TrackedJob) -> ProviderJobResult:
    header = "⚠️ Provider unavailable — generated fallback planning template instead.\n\n"
    full = header + _fallback_body(job)
    bundle = build_artifact_bundle(full, job_type=job.job_type, title=job.title)
    return ProviderJobResult(
        full_result=bundle.full_result,
        summary=bundle.summary,
        preview=bundle.preview,
        provider="none",
        model="template",
        used_llm=False,
        fallback=True,
    )


def _friendly_provider_failure(raw: str) -> str:
    lower = raw.lower()
    if "401" in lower or "authentication" in lower or "invalid api key" in lower:
        return "Invalid Anthropic API key."
    if "403" in lower:
        return "Anthropic API access denied."
    if "429" in lower:
        return "Anthropic rate limit exceeded."
    line = raw.strip().splitlines()[0] if raw.strip() else "Provider request failed."
    return line[:200]


def _bundle_from_text(text: str, job: TrackedJob, *, fallback: bool, provider: str, model: str, used_llm: bool) -> ProviderJobResult:
    bundle = build_artifact_bundle(text, job_type=job.job_type, title=job.title)
    return ProviderJobResult(
        full_result=bundle.full_result,
        summary=bundle.summary,
        preview=bundle.preview,
        provider=provider,
        model=model,
        used_llm=used_llm,
        fallback=fallback,
    )


def _result_from_provider_response(prov: ProviderResult, job: TrackedJob) -> ProviderJobResult:
    text = (prov.text or "").strip()
    if text.startswith("Provider request failed"):
        raise ProviderJobFailure(_friendly_provider_failure(text))
    if prov.used_llm and text:
        if text == EMPTY_PROVIDER_RESPONSE:
            raise ProviderJobFailure("Provider returned an empty response.")
        return _bundle_from_text(
            text, job, fallback=False, provider=prov.provider, model=prov.model, used_llm=True
        )
    raise ProviderJobFailure("Provider did not return a valid response.")


def _call_provider(prompt: str) -> ProviderResult:
    return complete_chat(prompt, session_id="job-worker")


def run_provider_job(job: TrackedJob, *, timeout_sec: float) -> ProviderJobResult:
    if not provider_configured():
        return fallback_result(job)

    _ = get_settings()
    prompt = build_provider_prompt(job)
    timeout = max(1.0, float(timeout_sec))

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_call_provider, prompt)
        try:
            prov = future.result(timeout=timeout)
        except FuturesTimeoutError as exc:
            raise ProviderJobTimeoutError("Provider request timed out.") from exc
        except ProviderJobFailure:
            raise
        except Exception as exc:
            raise ProviderJobFailure(f"Provider error: {exc}") from exc

    return _result_from_provider_response(prov, job)
