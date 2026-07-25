# SPDX-License-Identifier: Apache-2.0
"""Continuity synthesis — naturalize operational replies (canonical §D1)."""

from __future__ import annotations

import re

from aethos_core.operational_cognition.types import OperationalCognitionDecision


def naturalize_operational_reply(
    reply: str,
    *,
    intent: str,
    cognition: OperationalCognitionDecision | None = None,
) -> str:
    if not reply:
        return reply

    if intent == "failed_service_diagnosis":
        return _naturalize_diagnosis(reply, cognition=cognition)
    if intent in {"failed_service_fix_plan", "operational_narrative_continuity"}:
        return reply
    if intent.startswith("operational_response") or intent.startswith("internal_"):
        return reply

    if cognition and cognition.intent in {"diagnose_failure", "verify_operation", "health_check"}:
        if reply.startswith("I checked the active"):
            return reply.replace("I checked the active", "Yes — I checked the active", 1)
    return reply


def _naturalize_diagnosis(reply: str, *, cognition: OperationalCognitionDecision | None) -> str:
    if reply.startswith("Diagnosis for"):
        service = _extract_service_label(reply, cognition=cognition)
        intro = f"Yes — **{service}** appears unhealthy."
        if "Logs available: **no**" in reply or "Insufficient evidence" in reply:
            intro += " The current evidence is still thin, so I'm keeping this diagnosis intentionally bounded."
        body = reply.split("\n\n", 1)
        remainder = body[1] if len(body) > 1 else reply
        remainder = re.sub(r"^Diagnosis for \*\*.+?\*\*:\n\n", "", remainder, count=1, flags=re.S)
        if "No restart/redeploy is recommended yet" in remainder:
            remainder = remainder.replace(
                "No restart/redeploy is recommended yet from this evidence alone.",
                "Before attempting a restart or redeploy, the safest next step is checking surrounding logs and provider events around the failure window.",
            )
        return f"{intro}\n\n{remainder}".strip()
    return reply


def _extract_service_label(reply: str, *, cognition: OperationalCognitionDecision | None) -> str:
    if cognition and cognition.target:
        return cognition.target.replace("/", " / ")
    match = re.search(r"Diagnosis for \*\*(.+?)\*\*", reply)
    if match:
        return match.group(1)
    return "the service"
