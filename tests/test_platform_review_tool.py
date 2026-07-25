# SPDX-License-Identifier: Apache-2.0
"""The platform_review agent tool lets the agent answer 'what's our status / what did we
do today' by returning a cross-platform digest. Read-only."""

from __future__ import annotations

import json

from aethos_core.execution_brain.agent_tool_catalog import list_model_facing_tool_names
from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool
from aethos_core.tenancy import tenant_scope


def test_tool_is_registered():
    assert "platform_review" in list_model_facing_tool_names()


def test_platform_review_returns_digest_sections():
    with tenant_scope("alice@example.com"):
        out = json.loads(execute_agent_tool("platform_review", {}))
    assert out["ok"] is True
    titles = [s["title"] for s in out["sections"]]
    assert {"Deployments", "Jobs", "Approvals", "Monitors", "Social"} <= set(titles)
    assert "AethOS Daily Digest" in out["review"]
