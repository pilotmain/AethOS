# SPDX-License-Identifier: Apache-2.0
"""Browser observation direct execution lane — readonly screenshot / inspect / open."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from aethos_core.browser.runtime.browser_policy import classify_user_request, normalize_capture_type

_BLOCKED_MUTATION_RX = re.compile(
    r"\b(click|submit|autofill|purchase|buy|checkout|form\s+submit)\b",
    re.I,
)

_SCREENSHOT_RX = re.compile(
    r"\b("
    r"take\s+(?:a\s+)?screenshot(?:\s+of)?"
    r"|capture(?:\s+a)?(?:\s+screenshot)?(?:\s+of)?"
    r"|snapshot(?:\s+of)?"
    r")\b",
    re.I,
)

_INSPECT_RX = re.compile(
    r"\b("
    r"inspect(?:\s+the)?(?:\s+homepage|\s+landing\s+page|\s+page)?"
    r"|check(?:\s+the)?\s+homepage"
    r"|inspect(?:\s+the)?\s+landing\s+page"
    r"|capture(?:\s+the)?\s+landing\s+page"
    r")\b",
    re.I,
)

_OPEN_RX = re.compile(
    r"^\s*open\s+(?:the\s+)?([a-z0-9][a-z0-9.-]*\.[a-z]{2,}|https?://\S+)\s*\.?\s*$"
    r"|\bopen\s+(?:the\s+)?([a-z0-9][a-z0-9.-]+\.[a-z]{2,})\b",
    re.I,
)

_HOMEPAGE_ONLY_RX = re.compile(
    r"^\s*(?:inspect|check|capture)\s+(?:the\s+)?(?:homepage|landing\s+page|home\s+page)\s*\.?\s*$",
    re.I,
)


def is_browser_observation_capture_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    from aethos_core.providers.railway.deployment_plan.creation_preflight_intent import (
        is_railway_service_creation_preflight_intent,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_intent import (
        is_railway_deployment_plan_intent,
    )
    from aethos_core.providers.railway.service_creation_simulator.simulator_intent import (
        is_railway_service_creation_simulator_intent,
    )

    if (
        is_railway_deployment_plan_intent(raw)
        or is_railway_service_creation_preflight_intent(raw)
        or is_railway_service_creation_simulator_intent(raw)
    ):
        return False
    from aethos_core.browser_observation.browser_observation_followup_router import (
        is_browser_observation_followup_intent,
    )

    if is_browser_observation_followup_intent(raw):
        return False
    if _BLOCKED_MUTATION_RX.search(raw):
        return False
    if _SCREENSHOT_RX.search(raw):
        return True
    if _INSPECT_RX.search(raw):
        return True
    if _OPEN_RX.search(raw):
        return True
    if _HOMEPAGE_ONLY_RX.match(raw):
        return True
    return False


def is_browser_observation_intent(text: str) -> bool:
    """Alias for capture intent (follow-ups use browser_observation_followup_router)."""
    return is_browser_observation_capture_intent(text)


def extract_target_url(text: str) -> str:
    from aethos_core.browser.runtime.browser_runtime import extract_url_from_request

    raw = (text or "").strip()
    url = extract_url_from_request(raw)
    if url:
        return url
    m = _OPEN_RX.search(raw)
    if m:
        token = next((g for g in m.groups() if g), None)
        if token:
            from aethos_core.browser.runtime.browser_runtime import normalize_target_url

            return normalize_target_url(token.strip())
    return ""


def _infer_capture_type(text: str) -> str:
    policy = classify_user_request(text)
    return normalize_capture_type(str(policy.get("capture_type") or "screenshot"))


def inspect_browser_observation_runtime(*, probe_launch: bool = True) -> dict[str, Any]:
    from aethos_core.browser_observation.browser_observation_diagnostics import (
        inspect_browser_observation_runtime as _inspect,
    )

    return _inspect(probe_launch=probe_launch)


def _runtime_is_ready(diagnostics: dict[str, Any]) -> bool:
    return bool(
        diagnostics.get("env_flag_loaded")
        and diagnostics.get("playwright_python_package_installed")
        and diagnostics.get("chromium_binary_installed")
        and str(diagnostics.get("browser_launch_test") or "").startswith("pass")
        and diagnostics.get("worker_enabled")
    )


def compose_browser_blocked_reply(
    *,
    blockers: list[str] | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> str:
    from aethos_core.browser_observation.browser_observation_diagnostics import (
        format_browser_observation_blocked_reply,
    )

    diag = diagnostics or inspect_browser_observation_runtime(probe_launch=True)
    if blockers:
        body = format_browser_observation_blocked_reply(diag)
        extra = [b for b in blockers if b not in body]
        if extra:
            return body.replace(
                "No mutation has been performed.",
                "Additional notes:\n" + "\n".join(f"- {b}" for b in extra) + "\n\nNo mutation has been performed.",
            )
        return body
    return format_browser_observation_blocked_reply(diag)


def _compose_missing_url_reply() -> str:
    return (
        "Browser observation needs a target URL.\n\n"
        "Include a domain like `pilotmain.com` or a full `https://` URL.\n\n"
        "No mutation has been performed."
    )


def _compose_policy_blocked_reply(*, detail: str) -> str:
    return (
        "Browser observation is readonly-only and cannot perform that interaction.\n\n"
        f"**Blocked:** {detail}\n\n"
        "No mutation has been performed."
    )


def _compose_success_reply(*, url: str, result: dict[str, Any]) -> str:
    captured_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    artifacts = list(result.get("artifacts") or [])
    screenshot = next((a for a in artifacts if a.get("artifact_type") == "browser_screenshot"), None)
    artifact_id = str((screenshot or {}).get("artifact_id") or "")
    artifact_ref = artifact_id or "—"
    if screenshot and screenshot.get("artifact_file_url"):
        artifact_ref = f"{artifact_id} ({screenshot['artifact_file_url']})"

    lines = [
        "**Screenshot captured** (readonly browser observation).",
        "",
        f"- **URL:** {url}",
        f"- **Timestamp:** {captured_at}",
        f"- **Artifact:** {artifact_ref}",
        "",
        str(result.get("summary") or "Evidence stored under `data/browser_artifacts/`."),
        "",
        "No mutation has been performed. No approval was required.",
    ]
    return "\n".join(lines)


def _compose_capture_failed_reply(*, url: str, result: dict[str, Any]) -> str:
    err = str(result.get("error") or result.get("failure_class") or "capture failed")
    return (
        "Browser observation attempted a readonly capture but did not succeed.\n\n"
        f"- **URL:** {url}\n"
        f"- **Detail:** {err}\n\n"
        "No mutation has been performed."
    )


def route_browser_observation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Execute readonly browser observation or return a concrete blocker."""
    raw = (text or "").strip()
    if not is_browser_observation_capture_intent(raw):
        return None

    policy = classify_user_request(raw)
    if not policy.get("allowed"):
        return (
            _compose_policy_blocked_reply(detail=str(policy.get("detail") or "blocked interaction")),
            "browser_observation_policy_blocked",
            _meta(session_id, stage="policy_blocked"),
        )

    url = extract_target_url(raw)
    if not url:
        return (
            _compose_missing_url_reply(),
            "browser_observation_needs_url",
            _meta(session_id, stage="needs_url"),
        )

    runtime_diag = inspect_browser_observation_runtime(probe_launch=True)
    if not _runtime_is_ready(runtime_diag):
        meta = _meta(session_id, stage="blocked", target_url=url)
        meta["browser_runtime_diag"] = "blocked"
        return (
            compose_browser_blocked_reply(diagnostics=runtime_diag),
            "browser_observation_blocked",
            meta,
        )

    capture_type = _infer_capture_type(raw)
    from aethos_core.browser.runtime.browser_runtime import run_browser_evidence_capture

    result = run_browser_evidence_capture(
        url=url,
        capture_type=capture_type,
        session_id=session_id,
        user_request=raw,
        approved=True,
    )

    if result.get("blocked"):
        return (
            _compose_policy_blocked_reply(detail=str((result.get("policy") or {}).get("detail") or "policy denied")),
            "browser_observation_policy_blocked",
            _meta(session_id, stage="policy_blocked", target_url=url),
        )

    if not result.get("ok"):
        return (
            _compose_capture_failed_reply(url=url, result=result),
            "browser_observation_failed",
            _meta(session_id, stage="failed", target_url=url),
        )

    captured_at = datetime.now(UTC).isoformat()
    artifacts = list(result.get("artifacts") or [])
    shot = next((a for a in artifacts if a.get("artifact_type") == "browser_screenshot"), None)
    artifact_id = str((shot or {}).get("artifact_id") or "")
    artifact_file_url = str((shot or {}).get("artifact_file_url") or "")
    if artifact_id and not artifact_file_url:
        from aethos_core.browser.runtime.browser_artifacts import artifact_file_api_path

        artifact_file_url = artifact_file_api_path(artifact_id)

    from aethos_core.browser_observation.browser_observation_lifecycle import persist_browser_observation

    persist_browser_observation(
        session_id,
        {
            "artifact_id": artifact_id,
            "url": url,
            "type": "screenshot",
            "timestamp": captured_at,
            "artifacts": artifacts,
            "status": "captured",
            "artifact_file_url": artifact_file_url,
        },
    )

    meta = _meta(session_id, stage="captured", target_url=url, artifact_id=artifact_id, hydrated=True)
    return (
        _compose_success_reply(url=url, result=result),
        "browser_observation_captured",
        meta,
    )


def is_browser_observation_lane_intent(text: str) -> bool:
    """True for capture or lifecycle follow-up prompts owned by browser observation."""
    from aethos_core.browser_observation.browser_observation_followup_router import (
        is_browser_observation_followup_intent,
    )

    return is_browser_observation_followup_intent(text) or is_browser_observation_capture_intent(text)


def route_browser_observation_lane(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Hydrate lifecycle, route follow-ups first, then capture."""
    from aethos_core.browser_observation.browser_observation_followup_router import (
        is_browser_observation_followup_intent,
        route_browser_observation_followup,
    )
    from aethos_core.browser_observation.browser_observation_lifecycle import hydrate_browser_observation_context

    hydrate_browser_observation_context(session_id=session_id)
    if is_browser_observation_followup_intent(text):
        followup = route_browser_observation_followup(text, session_id=session_id)
        if followup is not None:
            return followup
    if is_browser_observation_capture_intent(text):
        return route_browser_observation(text, session_id=session_id)
    return None


def _meta(
    session_id: str,
    *,
    stage: str,
    target_url: str = "",
    artifact_id: str = "",
    hydrated: bool = False,
) -> dict[str, str]:
    out = {
        "route_id": "browser_observation",
        "matched_module": "browser_observation.browser_observation_router",
        "browser_observation_stage": stage,
        "browser_observation_hydrated": "true" if hydrated else "false",
        "lifecycle_source": "capture",
        "blocked_handlers": "front_door,capability_intro,generic_help,llm_fallback",
        "session_id": session_id,
        "readonly": "true",
    }
    if target_url:
        out["target_url"] = target_url
    if artifact_id:
        out["artifact_id"] = artifact_id
    return out
