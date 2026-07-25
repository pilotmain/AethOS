# SPDX-License-Identifier: Apache-2.0
"""Deterministic agent shortcuts — skip LLM for high-confidence provider ops."""

from __future__ import annotations

import re
from typing import Any

_CATALOG_RX = re.compile(
    r"\b(?:list|show)\s+(?:all\s+)?providers?\b.*\b(?:mission\s+control|provider\s+inventory|capabilities)\b"
    r"|\bmission\s+control\s+provider\s+inventory\b"
    r"|\bwhich\s+providers?\b.*\b(?:health|validate)\b"
    r"|\bhealth\s+checks?\b.*\bvalidate[\s-]only\b",
    re.I,
)
_QUICK_SCAN_RX = re.compile(
    r"\bquick\s+(?:mode|scan)\b.*\bproviders?\b"
    r"|\b(?:run|do)\s+a\s+quick\s+scan\b"
    r"|\bquick\s+scan\s+of\s+all\b",
    re.I,
)
_FULL_SCAN_RX = re.compile(
    r"\bfull\s+mode\b.*\bproviders?\b"
    r"|\bscan\s+all\s+(?:mission\s+control\s+)?providers?\b.*\bfull\b",
    re.I,
)


_STOP_MUTATION_RX = re.compile(r"\b(?:stop|shutdown|shut\s+down|kill)\b", re.I)


def match_agent_deterministic_shortcut(text: str) -> str | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if _CATALOG_RX.search(raw):
        return "provider_catalog"
    if _QUICK_SCAN_RX.search(raw):
        return "provider_inventory_all_quick"
    if _FULL_SCAN_RX.search(raw):
        return "provider_inventory_all_full"
    if _STOP_MUTATION_RX.search(raw):
        from aethos_core.operations.mutations.stop_mutation import extract_stop_target_names

        if extract_stop_target_names(raw):
            return "provider_stop_preflight"
    return None


def run_agent_deterministic_shortcut(
    text: str,
    *,
    session_id: str = "default",
) -> dict[str, Any] | None:
    kind = match_agent_deterministic_shortcut(text)
    if kind is None:
        return None

    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    if kind == "provider_catalog":
        payload = execute_agent_tool("provider_catalog", {}, session_id=session_id)
        return {
            "reply": _format_catalog_reply(payload),
            "meta": {"lane": "agent_runtime", "route_id": "agent_deterministic_catalog", "shortcut": kind},
        }

    if kind in {"provider_inventory_all_quick", "provider_inventory_all_full"}:
        mode = "quick" if kind == "provider_inventory_all_quick" else "full"
        payload = execute_agent_tool(
            "provider_inventory_all",
            {"mode": mode, "limit": 40},
            session_id=session_id,
        )
        return {
            "reply": _format_scan_reply(payload, mode=mode),
            "meta": {
                "lane": "agent_runtime",
                "route_id": "agent_deterministic_scan",
                "shortcut": kind,
                "scan_mode": mode,
            },
        }

    if kind == "provider_stop_preflight":
        from aethos_core.operations.mutations.stop_mutation import compose_stop_mutation_preflight_reply

        handled = compose_stop_mutation_preflight_reply(text, session_id=session_id)
        if handled is None:
            return None
        body, intent, meta = handled
        return {
            "reply": body,
            "meta": {
                "lane": "agent_runtime",
                "route_id": "agent_deterministic_stop",
                "shortcut": kind,
                "intent": intent,
                **{k: str(v) for k, v in meta.items()},
            },
        }

    return None


def _format_catalog_reply(payload_json: str) -> str:
    import json

    data = json.loads(payload_json)
    providers = list(data.get("providers") or [])
    health_rows: list[str] = []
    validate_rows: list[str] = []
    for row in providers[:40]:
        caps = row.get("capabilities") or []
        label = str(row.get("label") or row.get("provider"))
        cap_text = ", ".join(caps)
        if "health" in caps:
            health_rows.append(f"- **{label}** — {cap_text}")
        else:
            validate_rows.append(f"- **{label}** — {cap_text}")

    lines = [
        "## Mission Control Provider Inventory",
        "",
        f"**{data.get('provider_count', len(providers))} providers** registered. Credentials from Provider Inventory only.",
        "",
        "### Health checks supported",
        *(health_rows or ["- *(none)*"]),
        "",
        "### Validate-only",
        *(validate_rows or ["- *(none)*"]),
        "",
        "*Deterministic catalog read — no LLM tool loop.*",
    ]
    return "\n".join(lines)


def _format_scan_reply(payload_json: str, *, mode: str) -> str:
    import json

    data = json.loads(payload_json)
    configured = [r for r in data.get("providers") or [] if r.get("connection_ok")]
    missing = [r for r in data.get("providers") or [] if not r.get("connection_ok")]
    lines = [
        f"## Provider connection scan (`{mode}` mode)",
        "",
        f"**{data.get('configured_count', len(configured))}** connected · **{len(missing)}** missing token",
        "",
    ]
    if configured:
        lines.append("### Connected")
        for row in configured[:20]:
            detail = str(row.get("detail") or "")[:80]
            extra = ""
            if mode == "full" and row.get("inventory_ok"):
                inv = row.get("inventory") if isinstance(row.get("inventory"), dict) else {}
                count = inv.get("resource_count") or inv.get("repository_count") or inv.get("project_count")
                if count is not None:
                    extra = f" · inventory={count}"
            lines.append(f"- **{row.get('label') or row.get('provider')}** — {detail}{extra}")
        if len(configured) > 20:
            lines.append(f"- …and {len(configured) - 20} more")
    if missing:
        lines.append("")
        lines.append("### Missing token (add in Mission Control → Providers)")
        names = [str(r.get("label") or r.get("provider")) for r in missing[:16]]
        lines.append(", ".join(names))
        if len(missing) > 16:
            lines.append(f"…and {len(missing) - 16} more")
    lines.extend(["", "*Deterministic scan — no LLM tool loop.*"])
    return "\n".join(lines)
