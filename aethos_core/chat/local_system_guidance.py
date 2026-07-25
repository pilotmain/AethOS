# SPDX-License-Identifier: Apache-2.0
"""Local AethOS runtime guidance — not provider mutations."""

from __future__ import annotations

import re

_LOCAL_API_RESTART_RX = re.compile(
    r"\b(?:restart|reboot)\b"
    r"(?:\s+(?:the\s+)?)?(?:local\s+)?(?:aethos|aethos-core|aethos_core)\b"
    r"(?:\s+(?:api|server|process|uvicorn))?\b"
    r"|\b(?:restart|reboot)\b.*\b(?:aethos|aethos-core|aethos_core)\s+api\b"
    r"|\brestart\s+aethos\s+api\b",
    re.I,
)

_EXPLICIT_RAILWAY_SERVICE_RESTART_RX = re.compile(
    r"\b(?:restart|redeploy|re-?deploy)\b.*\b(?:railway|pilotos-api|pilotos|pilotcore)\b"
    r"|\b(?:restart|redeploy)\b.*\b(?:in|on)\s+railway\b"
    r"|\brailway\b.*\b(?:restart|redeploy)\b",
    re.I,
)

_DEPLOYED_AMBIGUOUS_RX = re.compile(
    r"\b(?:restart|reboot)\b.*\baethos\b.*\brailway\b"
    r"|\brailway\b.*\baethos\b.*\b(?:restart|reboot)\b",
    re.I,
)


def is_local_aethos_api_restart_intent(text: str) -> bool:
    """True for local API process restart — not Railway service restart."""
    raw = (text or "").strip()
    if not raw:
        return False
    if _EXPLICIT_RAILWAY_SERVICE_RESTART_RX.search(raw):
        return False
    return bool(_LOCAL_API_RESTART_RX.search(raw))


def is_deployed_aethos_restart_ambiguous(text: str) -> bool:
    raw = (text or "").strip()
    return bool(_DEPLOYED_AMBIGUOUS_RX.search(raw))


def compose_local_api_restart_reply() -> str:
    return "\n".join(
        [
            "To restart the **local AethOS API**, restart the uvicorn process running this server.",
            "",
            "Example:",
            "```bash",
            "pkill -f uvicorn || true",
            "uvicorn aethos_core.api.main:app --reload --port 8010",
            "```",
            "",
            "After restart, re-run your last operational command if needed.",
            "",
            "No Railway mutation has been performed.",
        ]
    )


def compose_deployed_restart_ambiguity_reply() -> str:
    return "\n".join(
        [
            "Do you mean the **local AethOS API** on this machine, or a **deployed Railway service**?",
            "",
            "- **Local API:** restart uvicorn (`uvicorn aethos_core.api.main:app --reload --port 8010`)",
            "- **Railway service:** say the exact service, e.g. `restart pilotos-api in railway`",
            "",
            "No mutation has been performed.",
        ]
    )


def route_local_system_guidance(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    _ = session_id
    raw = (text or "").strip()
    if not raw:
        return None

    from aethos_core.credentials.credential_guidance import route_railway_token_configuration_guidance

    token_guidance = route_railway_token_configuration_guidance(raw)
    if token_guidance is not None:
        return token_guidance

    if is_deployed_aethos_restart_ambiguous(raw):
        return (
            compose_deployed_restart_ambiguity_reply(),
            "local_system_guidance_ambiguous",
            _meta(stage="deployed_ambiguous"),
        )

    if is_local_aethos_api_restart_intent(raw):
        return (
            compose_local_api_restart_reply(),
            "local_system_api_restart_guidance",
            _meta(stage="local_api_restart"),
        )

    return None


def _meta(*, stage: str) -> dict[str, str]:
    return {
        "route_id": "local_system_guidance",
        "matched_module": "chat.local_system_guidance",
        "local_system_guidance_stage": stage,
        "readonly": "true",
        "mutation_performed": "false",
        "blocked_handlers": "explicit_mutation,railway_mutation_preflight,mutation_preflight",
    }
