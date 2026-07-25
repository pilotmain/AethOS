# SPDX-License-Identifier: Apache-2.0
"""Provider-read inventory intents — list/show projects/services in chat."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.chat.provider_inventory_format import (
    build_inventory_result_payload,
    format_provider_inventory_table,
    vercel_health_from_state,
)
from aethos_core.response_composition.output_format_classifier import classify_output_format, is_format_only_request

_LIST_PROVIDER_RX = re.compile(
    r"\b("
    r"list|show|display|give\s+me|fetch|get"
    r")\b",
    re.I,
)

_PROVIDER_RESOURCE_RX = re.compile(
    r"\b(vercel|railway|github)\b.*\b("
    r"project|projects|app|apps|service|services|repo|repos|repository|repositories|inventory|health"
    r")\b|\b("
    r"project|projects|app|apps|service|services|repo|repos"
    r")\b.*\b(vercel|railway|github)\b",
    re.I,
)

_PROVIDER_ONLY_RX = re.compile(r"\b(vercel|railway|github)\b", re.I)

_HEALTH_UNKNOWN_RX = re.compile(
    r"\bwhy\s+(?:is\s+)?(?:the\s+)?health\s+unknown\b|\bwhy\s+unknown\s+health\b",
    re.I,
)

_CHECK_HEALTH_RX = re.compile(
    r"\b("
    r"check\s+(?:the\s+)?health"
    r"|actually\s+check\s+(?:the\s+)?health"
    r"|healthy\s+or\s+failed"
    r"|tell\s+me\s+(?:if\s+)?(?:they\s+are\s+)?healthy\s+or\s+failed"
    r")\b",
    re.I,
)

_DEFLECTION_MARKERS = (
    "start an agent session",
    "navigate to mission control",
    "mission control → runtime → tracked work",
    "go to mission control",
)


def infer_provider_from_text(text: str) -> str | None:
    raw = (text or "").strip().lower()
    if "vercel" in raw:
        return "vercel"
    if "railway" in raw:
        return "railway"
    if "github" in raw:
        return "github"
    return None


def is_provider_health_operational_turn(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _HEALTH_UNKNOWN_RX.search(raw) or _CHECK_HEALTH_RX.search(raw):
        return True
    if re.search(r"\bhealth\b", raw, re.I) and infer_provider_from_text(raw):
        if raw.endswith("?") or _CHECK_HEALTH_RX.search(raw):
            return True
    return False


def is_provider_read_inventory_request(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    from aethos_core.chat.deterministic import is_canvas_render_request

    if is_canvas_render_request(raw):
        return False
    from aethos_core.chat.explicit_mutation_intent import has_explicit_mutation_verb

    if has_explicit_mutation_verb(raw):
        return False
    # A logs request is not an inventory listing — let the logs handler / agent fetch logs
    # instead of dumping the projects table ("show recent deployment logs" → logs, not projects).
    if re.search(r"\blogs?\b", raw, re.I):
        return False
    if is_provider_health_operational_turn(raw):
        return False
    if not _PROVIDER_ONLY_RX.search(raw):
        return False
    if _LIST_PROVIDER_RX.search(raw) and _PROVIDER_RESOURCE_RX.search(raw):
        return True
    if re.search(r"\b(health|failed|status)\b", raw, re.I) and _PROVIDER_ONLY_RX.search(raw):
        return True
    if re.search(r"\b(project|projects|app|apps)\b", raw, re.I) and _PROVIDER_ONLY_RX.search(raw):
        return True
    # GitHub repo listing ("which/what repos can you access", "list my github repos") is a
    # provider read, not an informational/help turn — route it so it actually queries GitHub.
    if re.search(r"\b(repo|repos|repositor(?:y|ies))\b", raw, re.I) and re.search(r"\bgithub\b", raw, re.I):
        return True
    if is_format_only_request(raw):
        return False
    return False


def contains_deflection_runaround(reply: str) -> bool:
    low = (reply or "").lower()
    return any(marker in low for marker in _DEFLECTION_MARKERS)


def _inventory_meta(provider: str, **extra: str) -> dict[str, str]:
    meta = {
        "lane": "provider_read_inventory",
        "route_id": "provider_read_inventory",
        "provider": provider,
        "single_loop": "true",
        "suppress_governance_footer": "true",
    }
    meta.update(extra)
    return meta


def _store_inventory_for_session(
    *,
    session_id: str,
    provider: str,
    inventory: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    from aethos_core.response_composition.response_composer import store_provider_inventory_result

    store_provider_inventory_result(
        session_id=session_id,
        provider=provider,
        payload=payload,
        summary=dict(payload.get("counts") or {}),
    )


def _compose_inventory_body(
    provider: str,
    inventory: dict[str, Any],
    *,
    output_format: str = "table",
    intro: str | None = None,
) -> str:
    label = provider.capitalize()
    count = len(inventory.get("projects") or [])
    noun = "projects"
    if provider == "vercel":
        count = int(inventory.get("project_count") or count or len(inventory.get("projects") or []))
    elif provider == "github":
        noun = "repositories"
        count = int(inventory.get("repository_count") or 0) or len(inventory.get("repositories") or [])
    header = intro if intro is not None else f"**{label} {noun}** ({count})"
    if output_format == "table":
        table = format_provider_inventory_table(provider, inventory)
        return f"{header}\n\n{table}"
    if output_format == "json":
        import json

        return f"{header}\n\n```json\n{json.dumps(inventory, indent=2)}\n```"
    table = format_provider_inventory_table(provider, inventory)
    return f"{header}\n\n{table}"


def compose_provider_read_inventory_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_provider_read_inventory_request(text):
        return None
    provider = infer_provider_from_text(text) or "vercel"
    output_format = classify_output_format(text, default="table")
    from aethos_core.execution_brain.provider_agent_ops import provider_inventory

    result = provider_inventory(provider, session_id=session_id)
    meta = _inventory_meta(provider, output_format=output_format)
    if not result.get("ok"):
        err = str(result.get("error") or result.get("detail") or "inventory_failed")
        if "token" in err.lower() or "credential" in err.lower():
            body = (
                f"**{provider} inventory failed** — {err}\n\n"
                "Add or validate the token in **Mission Control → Advanced settings → Credentials** (encrypted vault)."
            )
        else:
            body = f"**{provider} inventory failed** — {err}"
        return body, "provider_read_inventory_failed", meta

    inventory = result.get("inventory") or {}
    if not isinstance(inventory, dict):
        inventory = {}
    payload = build_inventory_result_payload(provider, inventory)
    _store_inventory_for_session(
        session_id=session_id,
        provider=provider,
        inventory=inventory,
        payload=payload,
    )
    body = _compose_inventory_body(provider, inventory, output_format=output_format)
    return body, "provider_read_inventory", meta


def _explain_unknown_health(
    provider: str,
    *,
    session_id: str,
    user_text: str,
) -> tuple[str, str, dict[str, str]]:
    from aethos_core.response_composition.operational_result_store import get_latest_operational_result

    cached = get_latest_operational_result(session_id=session_id)
    rows: list[dict[str, Any]] = []
    if cached is not None and cached.operation_type == "provider_inventory":
        if cached.provider == provider or not provider:
            rows = list(cached.result_payload.get("rows") or [])

    if not rows:
        from aethos_core.execution_brain.provider_agent_ops import provider_inventory

        inv_result = provider_inventory(provider, session_id=session_id)
        inventory = inv_result.get("inventory") or {}
        if isinstance(inventory, dict):
            payload = build_inventory_result_payload(provider, inventory)
            rows = list(payload.get("rows") or [])
            _store_inventory_for_session(
                session_id=session_id,
                provider=provider,
                inventory=inventory,
                payload=payload,
            )

    unknown_rows = [row for row in rows if str(row.get("health") or "") == "unknown"]
    label = provider.capitalize()
    lines = [
        f"**Why health is unknown ({label})**",
        "",
        f"- Total rows checked: **{len(rows)}**",
        f"- Still unknown: **{len(unknown_rows)}**",
    ]
    if not rows:
        lines.append(
            "\nI could not load inventory for this provider. "
            "Add or validate the API token in **Mission Control → Advanced settings → Credentials**."
        )
    elif not unknown_rows:
        lines.append("\nAll listed services/projects now have a resolved health state from the latest deployment.")
    else:
        lines.append("\nUnknown rows and reasons:")
        for row in unknown_rows[:15]:
            reason = str(row.get("health_reason") or "deployment_status_not_available")
            name = row.get("service") or row.get("project") or "—"
            lines.append(f"- **{name}** — {reason}")
        if len(unknown_rows) > 15:
            lines.append(f"- …and {len(unknown_rows) - 15} more")

    meta = _inventory_meta(provider, route_id="provider_health_explain", intent="provider_health_unknown_explain")
    if user_text:
        lines.append(f"\n_Question:_ {user_text[:240]}")
    return "\n".join(lines), "provider_health_unknown_explain", meta


def _compose_health_check_body(
    provider: str,
    *,
    session_id: str,
    user_text: str,
) -> tuple[str, str, dict[str, str]]:
    from aethos_core.execution_brain.provider_agent_ops import provider_health, provider_inventory

    inv = provider_inventory(provider, session_id=session_id)
    inventory = inv.get("inventory") or {}
    if isinstance(inventory, dict):
        payload = build_inventory_result_payload(provider, inventory)
        _store_inventory_for_session(
            session_id=session_id,
            provider=provider,
            inventory=inventory,
            payload=payload,
        )
    health_result = provider_health(provider, session_id=session_id)
    label = provider.capitalize()
    lines = [f"**{label} health check** (live deployment state)", ""]
    if provider == "railway":
        health_payload = health_result.get("health") or {}
        rows = list(health_payload.get("health_rows") or [])
        if rows:
            table_rows = [
                {
                    "project": row.get("project"),
                    "service": row.get("service"),
                    "type": "web",
                    "health": row.get("health") or row.get("status"),
                    "domain": row.get("deployment_url") or "",
                }
                for row in rows
                if isinstance(row, dict)
            ]
            healthy = sum(1 for row in table_rows if row.get("health") == "healthy")
            failed = sum(1 for row in table_rows if row.get("health") == "failed")
            lines.insert(1, f"Healthy: **{healthy}** · Failed: **{failed}** · Total: **{len(table_rows)}**")
            lines.append(format_inventory_table_from_rows(table_rows))
        else:
            lines.append("No Railway health rows returned.")
            if health_payload.get("health_error"):
                lines.append(f"Reason: {health_payload.get('health_error')}")
    elif provider == "vercel":
        health_payload = health_result.get("health") or {}
        projects = list(health_payload.get("projects") or [])
        if projects:
            table_rows = []
            for row in projects:
                if not isinstance(row, dict):
                    continue
                state = str(
                    row.get("latest_production_state")
                    or row.get("latest_deployment_state")
                    or row.get("state")
                    or "unknown"
                )
                health, _ = vercel_health_from_state(state)
                table_rows.append(
                    {
                        "project": row.get("project_name"),
                        "service": row.get("project_name"),
                        "type": "web",
                        "health": health,
                        "domain": row.get("latest_url") or "",
                    }
                )
            healthy = sum(1 for row in table_rows if row.get("health") == "healthy")
            failed = sum(1 for row in table_rows if row.get("health") == "failed")
            lines.insert(1, f"Healthy: **{healthy}** · Failed: **{failed}** · Total: **{len(table_rows)}**")
            lines.append(format_inventory_table_from_rows(table_rows))
        elif isinstance(inventory, dict):
            lines.append(_compose_inventory_body(provider, inventory, output_format="table", intro=None))
        else:
            lines.append("No Vercel project health data returned.")
    else:
        lines.append(str(health_result.get("error") or "Health check not available for this provider."))

    meta = _inventory_meta(provider, route_id="provider_health_check", intent="provider_health_check")
    if user_text:
        lines.append(f"\n_Request:_ {user_text[:240]}")
    return "\n".join(lines), "provider_health_check", meta


def format_inventory_table_from_rows(rows: list[dict[str, Any]]) -> str:
    from aethos_core.chat.provider_inventory_format import format_inventory_table

    return format_inventory_table(rows)


def compose_provider_health_followup_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not raw or not is_provider_health_operational_turn(raw):
        return None
    provider = infer_provider_from_text(raw) or infer_provider_from_session(session_id) or "vercel"
    if _HEALTH_UNKNOWN_RX.search(raw):
        return _explain_unknown_health(provider, session_id=session_id, user_text=raw)
    if _CHECK_HEALTH_RX.search(raw) or re.search(r"\bhealth\b", raw, re.I):
        return _compose_health_check_body(provider, session_id=session_id, user_text=raw)
    return None


def infer_provider_from_session(session_id: str) -> str | None:
    from aethos_core.response_composition.operational_result_store import get_latest_operational_result

    cached = get_latest_operational_result(session_id=session_id)
    if cached is not None and cached.provider:
        return str(cached.provider)
    return None


def try_compose_inventory_rerender_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if not is_format_only_request(raw) and classify_output_format(raw) == "conversational":
        return None
    from aethos_core.response_composition.operational_result_store import get_latest_operational_result

    cached = get_latest_operational_result(session_id=session_id)
    if cached is None or cached.operation_type != "provider_inventory":
        return None
    output_format = classify_output_format(raw, default="table")
    provider = cached.provider
    inventory = dict(cached.result_payload.get("inventory") or {})
    body = _compose_inventory_body(
        provider,
        inventory,
        output_format=output_format,
        intro="Re-rendering the last provider inventory (no refresh).",
    )
    meta = _inventory_meta(
        provider,
        route_id="provider_inventory_rerender",
        output_format=output_format,
        from_cache="true",
    )
    return body, "provider_inventory_rerender", meta
