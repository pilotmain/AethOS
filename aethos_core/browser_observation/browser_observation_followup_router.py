# SPDX-License-Identifier: Apache-2.0
"""Browser observation lifecycle follow-ups — hard ownership before generic routes."""

from __future__ import annotations

import re
from typing import Any

_BLOCKED_HANDLERS = "front_door,capability_intro,capability_truth,generic_help,llm_fallback,operational_capability_prose"

_SHOW_SCREENSHOT_RX = re.compile(
    r"\b("
    r"show\s+(?:me\s+)?(?:the\s+)?screenshot"
    r"|open\s+(?:the\s+)?screenshot"
    r"|display\s+(?:the\s+)?screenshot"
    r")\b",
    re.I,
)

_WHERE_SAVED_RX = re.compile(
    r"\b("
    r"where\s+is\s+(?:the\s+)?screenshot\s+saved"
    r"|where\s+(?:was|is)\s+(?:the\s+)?screenshot\s+stored"
    r"|where\s+did\s+(?:you\s+)?save\s+(?:the\s+)?screenshot"
    r")\b",
    re.I,
)

_WHAT_SHOWED_RX = re.compile(
    r"\b("
    r"what\s+did\s+(?:the\s+)?screenshot\s+show"
    r"|what\s+does\s+(?:the\s+)?screenshot\s+show"
    r"|what\s+was\s+(?:on|in)\s+(?:the\s+)?screenshot"
    r")\b",
    re.I,
)

_CAPABILITY_RX = re.compile(
    r"\b("
    r"are\s+you\s+capable\s+of\s+taking\s+screenshots?"
    r"|can\s+you\s+take\s+(?:a\s+)?screenshots?"
    r"|can\s+you\s+capture\s+screenshots?"
    r"|do\s+you\s+support\s+screenshots?"
    r"|can\s+you\s+screenshot"
    r")\b",
    re.I,
)


def is_browser_observation_followup_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _SHOW_SCREENSHOT_RX.search(raw):
        return True
    if _WHERE_SAVED_RX.search(raw):
        return True
    if _WHAT_SHOWED_RX.search(raw):
        return True
    if _CAPABILITY_RX.search(raw):
        return True
    return False


def has_active_browser_observation_lifecycle(*, session_id: str = "default") -> bool:
    from aethos_core.browser_observation.browser_observation_lifecycle import load_latest_browser_observation

    state = load_latest_browser_observation(session_id=session_id)
    return bool(state and state.get("status") == "captured" and state.get("artifact_id"))


def route_browser_observation_followup(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Route lifecycle follow-ups; capability questions always owned by this lane."""
    raw = (text or "").strip()
    if not is_browser_observation_followup_intent(raw):
        return None

    from aethos_core.browser_observation.browser_observation_lifecycle import (
        get_hydrated_browser_observation_context,
        load_latest_browser_observation,
    )

    ctx = get_hydrated_browser_observation_context()
    lifecycle_source = ctx.hydration_source if ctx and ctx.hydrated else ""
    state = load_latest_browser_observation(session_id=session_id)

    if _CAPABILITY_RX.search(raw):
        body, stage = _compose_capability_reply(state=state, session_id=session_id)
        return body, "browser_observation_capability", _meta_followup(
            session_id,
            stage=stage,
            artifact_id=str((state or {}).get("artifact_id") or ""),
            lifecycle_source=lifecycle_source,
            hydrated=bool(state),
        )

    if not state or state.get("status") != "captured":
        return (
            "No browser observation artifact is active in this session yet.\n\n"
            "Start with a readonly capture, for example:\n"
            "`take a screenshot of pilotmain.com`\n\n"
            "No mutation has been performed.",
            "browser_observation_followup_no_state",
            _meta_followup(session_id, stage="no_state", lifecycle_source=lifecycle_source, hydrated=False),
        )

    if _SHOW_SCREENSHOT_RX.search(raw):
        return _compose_show_screenshot(state), "browser_observation_show_artifact", _meta_followup(
            session_id,
            stage="show_artifact",
            artifact_id=str(state.get("artifact_id") or ""),
            lifecycle_source=lifecycle_source,
            hydrated=True,
        )

    if _WHERE_SAVED_RX.search(raw):
        return _compose_where_saved(state), "browser_observation_artifact_location", _meta_followup(
            session_id,
            stage="artifact_location",
            artifact_id=str(state.get("artifact_id") or ""),
            lifecycle_source=lifecycle_source,
            hydrated=True,
        )

    if _WHAT_SHOWED_RX.search(raw):
        return _compose_what_showed(state), "browser_observation_artifact_summary", _meta_followup(
            session_id,
            stage="artifact_summary",
            artifact_id=str(state.get("artifact_id") or ""),
            lifecycle_source=lifecycle_source,
            hydrated=True,
        )

    return None


def _artifact_endpoint(artifact_id: str) -> str:
    aid = (artifact_id or "").strip()
    if not aid:
        return ""
    return f"/api/v1/browser/artifacts/{aid}/file"


def _compose_show_screenshot(state: dict[str, Any]) -> str:
    artifact_id = str(state.get("artifact_id") or "")
    url = str(state.get("url") or "")
    endpoint = str(state.get("artifact_file_url") or "") or _artifact_endpoint(artifact_id)
    ts = str(state.get("timestamp") or state.get("updated_at") or "—")
    return "\n".join(
        [
            "Latest screenshot artifact:",
            "",
            f"- **URL:** {url}",
            f"- **Artifact ID:** `{artifact_id}`",
            f"- **Captured:** {ts}",
            "",
            "Artifact path:",
            f"`{endpoint}`",
            "",
            "Open the endpoint in Mission Control → Browser, or paste it into your browser while the API is running.",
            "",
            "No mutation has been performed.",
        ]
    )


def _compose_where_saved(state: dict[str, Any]) -> str:
    artifact_id = str(state.get("artifact_id") or "")
    endpoint = str(state.get("artifact_file_url") or "") or _artifact_endpoint(artifact_id)
    return "\n".join(
        [
            "The screenshot was saved as a **browser observation artifact**.",
            "",
            f"**Artifact ID:** `{artifact_id}`",
            "",
            "Artifact endpoint:",
            f"`{endpoint}`",
            "",
            "Artifacts are stored under `data/browser_artifacts/` on the AethOS runtime host.",
            "",
            "No mutation has been performed.",
        ]
    )


def _compose_what_showed(state: dict[str, Any]) -> str:
    url = str(state.get("url") or "")
    artifact_id = str(state.get("artifact_id") or "")
    title = ""
    for row in list(state.get("artifacts") or []):
        if not isinstance(row, dict):
            continue
        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else row
        if isinstance(meta, dict) and meta.get("title"):
            title = str(meta["title"])
            break
        if row.get("artifact_type") == "browser_page_metadata":
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            nested = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
            title = str(nested.get("title") or "")

    lines = [
        f"Latest readonly capture for **{url}**:",
        "",
        f"- **Artifact ID:** `{artifact_id}`",
    ]
    if title:
        lines.append(f"- **Page title (metadata):** {title}")
    lines.extend(
        [
            "",
            "For the full visual, use `show me the screenshot` or open the artifact endpoint directly.",
            "",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def _compose_capability_reply(
    *,
    state: dict[str, Any] | None,
    session_id: str,
) -> tuple[str, str]:
    from aethos_core.browser_observation.browser_observation_router import (
        inspect_browser_observation_runtime,
    )

    _ = session_id
    diag = inspect_browser_observation_runtime(probe_launch=True)
    ready = bool(
        diag.get("env_flag_loaded")
        and diag.get("playwright_python_package_installed")
        and diag.get("chromium_binary_installed")
        and str(diag.get("browser_launch_test") or "").startswith("pass")
        and diag.get("worker_enabled")
    )
    if not ready:
        from aethos_core.browser_observation.browser_observation_router import compose_browser_blocked_reply

        return compose_browser_blocked_reply(diagnostics=diag), "blocked"

    lines = [
        "Yes — readonly browser screenshot capture is **available and operational**.",
        "",
        "I can capture page screenshots without mutation or approval (readonly observation lane).",
    ]
    if state and state.get("status") == "captured" and state.get("url"):
        lines.extend(
            [
                "",
                "**Latest capture in this session:**",
                f"- {state.get('url')}",
                "- captured successfully",
                f"- artifact `{state.get('artifact_id')}`",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "No capture in this session yet — try `take a screenshot of <url>`.",
            ]
        )
    lines.append("\nNo mutation has been performed.")
    return "\n".join(lines), "capability_ok"


def _meta_followup(
    session_id: str,
    *,
    stage: str,
    artifact_id: str = "",
    lifecycle_source: str = "",
    hydrated: bool = False,
) -> dict[str, str]:
    meta = {
        "route_id": "browser_observation",
        "matched_module": "browser_observation.browser_observation_followup_router",
        "browser_observation_stage": stage,
        "browser_observation_hydrated": "true" if hydrated else "false",
        "lifecycle_source": lifecycle_source or "none",
        "blocked_handlers": _BLOCKED_HANDLERS,
        "session_id": session_id,
        "readonly": "true",
    }
    if artifact_id:
        meta["artifact_id"] = artifact_id
    return meta
