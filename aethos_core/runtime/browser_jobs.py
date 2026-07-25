# SPDX-License-Identifier: Apache-2.0
"""Browser job proposals — approval-required supervised sessions."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.runtime.browser_capability import get_browser_capability_status
from aethos_core.runtime.browser_intents import (
    is_browser_login_request,
    is_browser_session_request,
    is_browser_status_request,
    mentions_vercel,
)

BROWSER_ACTION_TYPES = frozenset(
    {
        "browser_status_check",
        "browser_navigation_plan",
        "browser_login_required_notice",
    }
)


def extract_target_url(text: str) -> str | None:
    raw = (text or "").strip()
    m = re.search(r"https?://[^\s]+", raw, re.I)
    if m:
        return m.group(0).rstrip(".,)")
    m = re.search(r"\b([a-z0-9][-a-z0-9]*\.(?:com|org|io|dev|app))\b", raw, re.I)
    if m:
        return m.group(1).lower()
    if mentions_vercel(raw):
        return "vercel.com"
    return None


def infer_browser_intent_from_text(text: str) -> tuple[str, dict[str, Any]] | None:
    """Return (action_type, params) or None if not a browser-specific prompt."""
    raw = (text or "").strip()
    if not raw:
        return None

    target = extract_target_url(raw) or ("vercel.com" if mentions_vercel(raw) else "unknown")

    if is_browser_status_request(raw):
        return ("browser_status_check", {"target": target, "user_request": raw, "mode": "supervised"})

    if is_browser_login_request(raw):
        return (
            "browser_login_required_notice",
            {
                "target": target,
                "user_request": raw,
                "mode": "supervised",
                "login_required": True,
            },
        )

    if is_browser_session_request(raw):
        return (
            "browser_navigation_plan",
            {"target": target, "user_request": raw, "mode": "supervised"},
        )

    return None


def should_preempt_external_health(text: str) -> bool:
    """Browser login/dashboard intents should not become auto-run external health jobs."""
    intent = infer_browser_intent_from_text(text)
    if intent is None:
        return False
    action_type, _ = intent
    return action_type in {"browser_login_required_notice", "browser_navigation_plan"}


def browser_off_reply() -> str:
    return (
        "**Browser automation is currently off.**\n\n"
        "I cannot open supervised browser sessions until you enable "
        "`BROWSER_AUTOMATION_ENABLED=true` in `.env` and restart the API.\n\n"
        "I can still help with **public status checks** and **approved CLI probes** "
        "that do not use a browser session."
    )


def browser_on_no_session_reply(*, target: str) -> str:
    status = get_browser_capability_status()
    if not status.get("available"):
        diag = status.get("diagnostics") or {}
        cmds = diag.get("recommended_install_commands") or []
        if status.get("playwright_package") != "installed":
            cmd_block = "\n".join(f"  {c}" for c in cmds) if cmds else (
                "  .venv/bin/python -m pip install playwright\n"
                "  .venv/bin/python -m playwright install chromium"
            )
            return (
                f"**Browser automation is enabled** for `{target}`, but the **Playwright package "
                f"is missing in the AethOS runtime** (`{diag.get('python_executable', 'unknown')}`).\n\n"
                "Install into the **same Python that runs the API**:\n"
                f"```bash\n{cmd_block}\n```\n"
                "Then restart the API. Do not use bare `pip` unless your shell is already in `.venv`."
            )
        if status.get("chromium_browser") != "installed":
            chromium_cmd = cmds[-1] if cmds else ".venv/bin/python -m playwright install chromium"
            return (
                f"**Browser automation is enabled** for `{target}`, but **Chromium is not installed** "
                "for Playwright in the AethOS runtime.\n\n"
                f"```bash\n{chromium_cmd}\n```\n"
                "Then restart the API."
            )
        return browser_off_reply()
    return (
        f"**Supervised browser session** for `{target}`.\n\n"
        "I can open a visible browser window **after your approval** in Mission Control → Jobs. "
        "You remain responsible for login — AethOS does **not** store credentials."
    )


def login_required_reply(*, target: str) -> str:
    status = get_browser_capability_status()
    lines = [
        f"**Authenticated access to `{target}` requires a user-approved browser session.**",
        "",
        "AethOS will **not** store credentials, ask for passwords in chat, or claim "
        "private dashboard access without an approved supervised session.",
        "",
    ]
    if not status["enabled"]:
        lines = [
            f"**Authenticated access to `{target}` needs supervised browser automation.**",
            "",
            "Browser automation is **off**. I cannot log in or review a private dashboard.",
            "",
            "**Alternatives:**",
            "1. **Public status** — no login (e.g. Vercel status page).",
            "2. **CLI checks** — after approval, read-only `vercel` probes.",
            "3. **Enable browser automation** — then approve a supervised session proposal.",
        ]
    else:
        lines.extend(
            [
                "I can open a **supervised browser session** after approval. "
                "You will need to **log in manually** in the browser window.",
                "",
                "AethOS will **not** report dashboard access unless you complete login yourself.",
                "",
                "**Alternatives:** public health checks or approved CLI probes.",
            ]
        )
    return "\n".join(lines)


def propose_browser_job_record(
    action_type: str,
    params: dict[str, Any],
    *,
    source: str = "api",
    session_id: str = "default",
):
    from aethos_core.runtime.authority import authority

    return authority.propose_action(
        action_type,
        params,
        source=source,
        session_id=session_id,
    )
