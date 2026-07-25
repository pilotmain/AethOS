# SPDX-License-Identifier: Apache-2.0
"""FIX 316B — identity truth lock chat router."""

from __future__ import annotations

from aethos_core.identity_truth_lock.identity_truth_lock_intent import (
    handle_identity_truth_lock_intent,
    parse_identity_truth_lock_intent,
)
from aethos_core.identity_truth_lock.identity_truth_lock_renderer import render_identity_truth_lock_markdown
from aethos_core.identity_truth_lock.identity_truth_lock_service import build_identity_truth_lock
from aethos_core.identity_truth_lock.identity_truth_lock_contract import IDENTITY_TRUTH_LOCK_ROUTE_ID
from aethos_core.identity_truth_lock.runtime_identity_lock import runtime_identity_lock_meta


def _meta(*, session_id: str, intent: str) -> dict[str, str]:
    base = {
        "route_id": IDENTITY_TRUTH_LOCK_ROUTE_ID,
        "matched_module": "identity_truth_lock.identity_truth_lock_router",
        "session_id": session_id,
        "intent": intent,
        "suppress_governance_footer": "true",
        "show_governance_footer": "false",
        "presentation_mode": "casual",
        "lane": "identity_truth_lock",
    }
    base.update(runtime_identity_lock_meta(classification=intent))
    return base


def route_identity_truth_lock(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    parsed = parse_identity_truth_lock_intent(text)
    if parsed is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"

    if parsed.get("action") == "record":
        handle_identity_truth_lock_intent(parsed, session_id=sid)
        return (
            "Identity review recorded. This command is record-only and does not mutate identity truth.",
            "identity_review_record",
            _meta(session_id=sid, intent="identity_review_record"),
        )

    if parsed.get("action") == "view":
        payload = build_identity_truth_lock(session_id=sid).identity_truth_lock
        body = render_identity_truth_lock_markdown(
            payload=payload,
            focus=str(parsed.get("focus") or "identity_dashboard"),
        )
        return body, "identity_dashboard", _meta(session_id=sid, intent="identity_dashboard")

    return None
