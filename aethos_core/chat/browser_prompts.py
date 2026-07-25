# SPDX-License-Identifier: Apache-2.0
"""Chat replies for browser capability and approval-required browser jobs."""

from __future__ import annotations

from aethos_core.runtime.browser_capability import get_browser_capability_status
from aethos_core.runtime.browser_jobs import (
    browser_off_reply,
    browser_on_no_session_reply,
    infer_browser_intent_from_text,
    login_required_reply,
    propose_browser_job_record,
)
from aethos_core.runtime.actions import RuntimeAction


def _proposal_footer(action: RuntimeAction) -> str:
    target = str(action.params.get("target") or "site")
    return (
        f"\n\n**Browser job proposed:** `{action.id}`\n"
        f"**Target:** {target}\n"
        f"**Mode:** supervised · **Approval required**\n"
        "Approve or deny in **Mission Control → Jobs**."
    )


def browser_status_reply() -> str:
    status = get_browser_capability_status()
    lines = [
        "**Browser automation status**",
        "",
        f"- Foundation: **{status.get('foundation_label', status['status_label'])}**",
        f"- Execution: **{status.get('execution_label', 'unknown')}**",
        f"- Playwright package: **{status.get('playwright_package', 'unknown')}**",
        f"- Chromium browser: **{status.get('chromium_browser', 'unknown')}**",
        f"- Runtime Python: `{status.get('diagnostics', {}).get('python_executable', 'unknown')}`",
        f"- Config (`{status.get('env_var', 'BROWSER_AUTOMATION_ENABLED')}`): "
        f"**{'true' if status['enabled'] else 'false'}**",
        f"- Requires approval: **yes**",
        f"- Login sessions: **{status.get('supports_login_sessions', 'supervised_only')}**",
        "",
    ]
    if not status["enabled"]:
        lines[0] = "🌐 **Browser automation is off — setup required.**"
        lines.append(
            "Enable `BROWSER_AUTOMATION_ENABLED=true` in `.env`, restart the API, "
            "then ask again to propose supervised browser jobs."
        )
    elif status["status_label"] == "Not installed":
        lines.append(
            "Browser automation is **enabled** but Playwright is **not installed** on this host. "
            "Install when Phase 8 supervised sessions are approved."
        )
    elif status.get("playwright_package") != "installed":
        hint = status.get("diagnostics", {}).get("install_hint", "")
        lines.append(
            "Foundation is on, but the **Playwright package is missing in the AethOS runtime**. "
            f"Install with: `{hint}` then restart the API."
        )
    elif status.get("chromium_browser") != "installed":
        cmds = status.get("diagnostics", {}).get("recommended_install_commands") or []
        chromium_cmd = cmds[-1] if cmds else ".venv/bin/python -m playwright install chromium"
        lines.append(
            "Playwright package is installed, but **Chromium is missing** in this runtime. "
            f"Run: `{chromium_cmd}` then restart the API."
        )
    else:
        lines.append(
            "Supervised browser sessions are available after approval. "
            "You control login in the opened browser window; AethOS does not store credentials."
        )
    return "\n".join(lines)


def create_browser_intent_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    intent = infer_browser_intent_from_text(text)
    if intent is None:
        return None

    action_type, params = intent
    status = get_browser_capability_status()
    target = str(params.get("target") or "unknown")

    if action_type == "browser_status_check":
        body = browser_status_reply()
        if status["enabled"]:
            action = propose_browser_job_record(
                "browser_status_check",
                params,
                source="chat",
                session_id=session_id,
            )
            body += (
                "\n\nI can also record a **browser status check** proposal for Mission Control."
                + _proposal_footer(action)
            )
            return (
                body,
                "browser_status",
                {"proposed_action_id": action.id, "proposed_action_type": action.action_type},
            )
        return body, "browser_status", {}

    if action_type == "browser_login_required_notice":
        body = login_required_reply(target=target)
        if not status["enabled"]:
            return body, "browser_login_notice", {}
        action = propose_browser_job_record(
            "browser_login_required_notice",
            params,
            source="chat",
            session_id=session_id,
        )
        body += (
            "\n\n⏳ I proposed a **supervised browser login notice** — approval required "
            "before any session would open."
            + _proposal_footer(action)
        )
        return (
            body,
            "browser_login_notice",
            {"proposed_action_id": action.id, "proposed_action_type": action.action_type},
        )

    # browser_navigation_plan
    if not status["enabled"]:
        body = browser_off_reply()
        return body, "browser_unavailable", {}

    body = browser_on_no_session_reply(target=target)
    action = propose_browser_job_record(
        "browser_navigation_plan",
        params,
        source="chat",
        session_id=session_id,
    )
    body += (
        "\n\n⏳ **Browser job proposed** — approval required before opening "
        f"`{target}`."
        + _proposal_footer(action)
    )
    return (
        body,
        "browser_job_proposed",
        {"proposed_action_id": action.id, "proposed_action_type": action.action_type},
    )
