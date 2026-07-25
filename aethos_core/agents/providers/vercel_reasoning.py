# SPDX-License-Identifier: Apache-2.0
"""Vercel provider diagnostics — readonly deployment intelligence scaffold."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.operations.intents import extract_target_hints


def run_vercel_diagnostics(user_request: str) -> dict[str, Any]:
    """Vercel diagnostics — uses credential gate; returns actionable scaffold when blocked."""
    from aethos_core.connections.credential_runtime_gate import check_provider_credential_gate

    gate = check_provider_credential_gate("vercel", require_validated=True)
    hints = extract_target_hints(user_request)
    target = hints[0] if hints else None

    if not gate.get("ok"):
        return {
            "ok": False,
            "provider": "vercel",
            "credential_required": True,
            "detail": gate.get("detail"),
            "target": target,
            "report": (
                "# Vercel diagnostics (credential required)\n\n"
                f"{gate.get('detail') or 'Connect Vercel credentials in Mission Control.'}\n"
                "Use governed readonly execution for deployment timeline once connected."
            ),
        }

    return {
        "ok": True,
        "provider": "vercel",
        "target": target,
        "detail": "Vercel credential available — use operation preflight / readonly execution for full timeline.",
        "report": (
            "# Vercel deployment diagnostics\n\n"
            f"**Target hint:** {target or 'unspecified'}\n"
            "- Credential gate passed.\n"
            "- Run governed readonly execution for deployment list, failure reason, and reachability evidence.\n"
            "- Browser agent can capture deployment UI when public URL resolves."
        ),
        "evidence_chain": [f"vercel:credential_valid:{target or 'unknown'}"],
    }


def _extract_project(text: str) -> str | None:
    m = re.search(r"\bproject\s+([a-z0-9_-]+)", text, re.I)
    return m.group(1) if m else None
