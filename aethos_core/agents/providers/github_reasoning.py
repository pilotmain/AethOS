# SPDX-License-Identifier: Apache-2.0
"""GitHub provider diagnostics — workflow and deployment correlation."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.intents import extract_target_hints


def run_github_diagnostics(user_request: str) -> dict[str, Any]:
    from aethos_core.connections.credential_runtime_gate import check_provider_credential_gate

    gate = check_provider_credential_gate("github", require_validated=True)
    hints = extract_target_hints(user_request)
    repo_hint = hints[0] if hints else None

    if not gate.get("ok"):
        return {
            "ok": False,
            "provider": "github",
            "credential_required": True,
            "detail": gate.get("detail"),
            "report": (
                "# GitHub workflow diagnostics (credential required)\n\n"
                f"{gate.get('detail') or 'Connect GitHub in Mission Control.'}"
            ),
        }

    return {
        "ok": True,
        "provider": "github",
        "repo_hint": repo_hint,
        "report": (
            "# GitHub workflow diagnostics\n\n"
            f"**Repo hint:** {repo_hint or 'unspecified'}\n"
            "- Credential gate passed.\n"
            "- Use readonly GitHub workflow inventory for failed runs and job logs.\n"
            "- Correlate workflow failures with provider deployment evidence."
        ),
        "evidence_chain": [f"github:credential_valid:{repo_hint or 'unknown'}"],
    }
