# SPDX-License-Identifier: Apache-2.0
"""GitHub remote repo analysis — atlas-trader acceptance corpus."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from aethos_core.chat.engineering_intelligence import (
    EngineeringIntent,
    classify_engineering_intent,
    execute_engineering_intent,
    is_engineering_intelligence_request,
)
from aethos_core.chat.informational_help_router import is_local_workspace_setup_topic
from aethos_core.providers.github.operations.repo_remote_read_api import (
    build_github_repo_snapshot,
    extract_github_repo_hint,
    format_github_enhancement_report,
    is_github_remote_repo_analysis_request,
)


_ATLAS_SNAPSHOT = {
    "ok": True,
    "repository": "pilotmain/atlas-trader",
    "branch": "main",
    "commit_sha": "abc123def456",
    "description": "Trading stack",
    "pushed_at": "2026-06-11T12:00:00Z",
    "html_url": "https://github.com/pilotmain/atlas-trader",
    "stack": ["Python", "FastAPI"],
    "deployment_fields": {"runtime": "python", "framework": "fastapi"},
    "directory_map": ["src", "tests", "web"],
    "tree_file_count": 180,
    "files_read": ["README.md", "pyproject.toml", ".github/workflows/ci.yml"],
    "file_contents": {
        "README.md": "# atlas-trader\n\nAPI trading service.",
        "pyproject.toml": "[project]\nname = \"atlas-trader\"",
        ".github/workflows/ci.yml": "name: ci\non: [push]",
    },
    "workflows": [".github/workflows/ci.yml"],
    "manifests": ["README.md", "pyproject.toml"],
}


def test_is_github_remote_repo_analysis_atlas_trader():
    prompt = "look into atlas-trader on GitHub and suggest enhancements"
    assert is_github_remote_repo_analysis_request(prompt)
    assert extract_github_repo_hint(prompt) == "atlas-trader"
    assert is_engineering_intelligence_request(prompt)


def test_atlas_trader_prompt_returns_analysis_not_registration():
    with patch(
        "aethos_core.providers.github.operations.repo_remote_read_api.build_github_repo_snapshot",
        return_value=_ATLAS_SNAPSHOT,
    ):
        body, intent, meta = execute_engineering_intent(
            "look into atlas-trader on GitHub and suggest enhancements",
            session_id="atlas-corpus",
        )
    assert intent == "github_remote_analysis"
    assert meta.get("github_remote_read") == "true"
    assert "pilotmain/atlas-trader" in body
    assert "Enhancement" in body or "enhancement" in body.lower()
    assert "register" not in body.lower()
    assert "Mission Control" not in body


def test_github_connected_followup_not_needed_when_first_turn_works():
    """Step 2 of corpus — if step 1 works, 'but github is connected' is not engineering remote analysis."""
    followup = "but github is connected"
    assert not is_github_remote_repo_analysis_request(followup)
    assert not is_engineering_intelligence_request(followup)


def test_local_path_routes_to_architecture_not_github_remote():
    prompt = "analyze architecture for /Users/raya/AethOS"
    assert not is_github_remote_repo_analysis_request(prompt)
    classified = classify_engineering_intent(prompt)
    assert classified is not None
    assert classified.intent == EngineeringIntent.ARCHITECTURE
    assert classified.hint == "/Users/raya/AethOS"


def test_local_workspace_setup_topic_skips_github_remote_analysis():
    prompt = "look into atlas-trader on GitHub and suggest enhancements"
    assert not is_local_workspace_setup_topic(prompt)


def test_build_snapshot_tree_and_contents_mocked():
    token = "gh-test"
    owner, repo = "pilotmain", "atlas-trader"
    full = f"{owner}/{repo}"

    def fake_request(_token, method, path, *, params=None, json_body=None):
        if path == f"/repos/{owner}/{repo}":
            return {
                "ok": True,
                "data": {
                    "default_branch": "main",
                    "description": "Trading",
                    "pushed_at": "2026-06-11T12:00:00Z",
                    "html_url": f"https://github.com/{full}",
                },
            }
        if path == f"/repos/{owner}/{repo}/branches/main":
            return {"ok": True, "data": {"commit": {"sha": "commit-sha-full"}}}
        if path == f"/repos/{owner}/{repo}/git/commits/commit-sha-full":
            return {"ok": True, "data": {"tree": {"sha": "tree-sha-full"}}}
        if path == f"/repos/{owner}/{repo}/git/trees/tree-sha-full":
            return {
                "ok": True,
                "data": {
                    "tree": [
                        {"path": "README.md", "type": "blob", "size": 120},
                        {"path": "pyproject.toml", "type": "blob", "size": 200},
                        {"path": "src", "type": "tree"},
                        {"path": "src/main.py", "type": "blob", "size": 400},
                    ],
                },
            }
        if path == f"/repos/{owner}/{repo}/contents/README.md":
            import base64

            return {
                "ok": True,
                "data": {
                    "type": "file",
                    "content": base64.b64encode(b"# atlas-trader").decode(),
                },
            }
        if path == f"/repos/{owner}/{repo}/contents/pyproject.toml":
            import base64

            return {
                "ok": True,
                "data": {
                    "type": "file",
                    "content": base64.b64encode(b"[project]\nname='atlas-trader'").decode(),
                },
            }
        if path == f"/repos/{owner}/{repo}/contents/src/main.py":
            import base64

            return {
                "ok": True,
                "data": {
                    "type": "file",
                    "content": base64.b64encode(b"def main(): pass").decode(),
                },
            }
        return {"ok": False, "error": f"unexpected path {path}"}

    with (
        patch(
            "aethos_core.providers.github.operations.repo_remote_read_api._github_token",
            return_value=token,
        ),
        patch(
            "aethos_core.providers.github.operations.repo_remote_read_api.resolve_repository",
            return_value={"ok": True, "owner": owner, "repo": repo, "full_name": full},
        ),
        patch(
            "aethos_core.providers.github.operations.repo_remote_read_api.inspect_repo",
            return_value={
                "ok": True,
                "repository": full,
                "default_branch": "main",
                "description": "Trading",
                "pushed_at": "2026-06-11T12:00:00Z",
                "html_url": f"https://github.com/{full}",
            },
        ),
        patch(
            "aethos_core.providers.github.operations.repo_remote_read_api.request_github",
            side_effect=fake_request,
        ),
    ):
        snapshot = build_github_repo_snapshot("atlas-trader")

    assert snapshot["ok"] is True
    assert snapshot["repository"] == full
    assert "README.md" in snapshot["files_read"]
    report = format_github_enhancement_report(snapshot)
    assert "atlas-trader" in report
    assert "register" not in report.lower()


@pytest.mark.parametrize(
    "workspace",
    ["/tmp/myrepo", str(Path("/Users/raya/projects/demo"))],
)
def test_local_repo_scan_still_engineering(workspace: str):
    prompt = f"scan local workspace {workspace}"
    classified = classify_engineering_intent(prompt)
    assert classified is not None
    assert classified.intent == EngineeringIntent.WORKSPACE_SCAN
