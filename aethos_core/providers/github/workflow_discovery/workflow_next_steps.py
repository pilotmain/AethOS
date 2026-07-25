# SPDX-License-Identifier: Apache-2.0
"""Actionable next steps and proposal-only CI workflow drafting."""

from __future__ import annotations

from typing import Any

_GENERIC_CI_FILENAME = "ci.yml"
_GENERIC_CI_PATH = f".github/workflows/{_GENERIC_CI_FILENAME}"


def should_offer_workflow_proposal(discovery: dict[str, Any]) -> bool:
    if not discovery:
        return False
    if not discovery.get("workflows_dir_found"):
        return True
    names = list(discovery.get("workflow_file_names") or [])
    return not names


def suggest_starter_workflow_type(*, repo_context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a conservative starter workflow recommendation without stack guessing."""
    _ = repo_context
    return {
        "type": "generic_ci",
        "filename": _GENERIC_CI_FILENAME,
        "path": _GENERIC_CI_PATH,
        "description": "Basic CI scaffold with push/pull_request triggers and placeholder validation steps.",
    }


def compose_workflow_discovery_next_steps(
    discovery: dict[str, Any],
    *,
    repo_context: dict[str, Any] | None = None,
) -> str:
    repo = str(discovery.get("repository") or "the repository")
    default_branch = str(discovery.get("default_branch") or "main")
    actions_status = str(discovery.get("actions_status") or "unknown")

    if should_offer_workflow_proposal(discovery):
        starter = suggest_starter_workflow_type(repo_context=repo_context)
        lines = [
            f"GitHub Actions is **{actions_status}** for **{repo}**, but no workflow files exist yet.",
            "",
            "Next best step:",
            f"1. Create `{starter['path']}`",
            f"2. Trigger on push + pull_request to `{default_branch}`",
            "3. Add basic install/test/lint steps",
            "4. Push a commit to generate the first workflow run",
            "",
            "No rerun is possible until a workflow exists and has produced at least one run.",
            "",
            "I can draft a starter workflow proposal if you'd like.",
        ]
        return "\n".join(lines)

    trigger_analysis = dict(discovery.get("trigger_analysis") or {})
    if trigger_analysis.get("has_workflow_dispatch") and not (
        trigger_analysis.get("has_push_trigger") or trigger_analysis.get("has_pull_request_trigger")
    ):
        return "\n".join(
            [
                f"Workflow files exist for **{repo}**, but only manual dispatch triggers were detected.",
                "",
                "Next best steps:",
                "- Open GitHub Actions and manually dispatch the workflow.",
                "- Or add `push` / `pull_request` triggers on the default branch if you want automatic CI runs.",
                "",
                "No rerun is possible until at least one workflow run exists.",
            ]
        )

    if discovery.get("actions_status") == "disabled":
        return "\n".join(
            [
                f"Workflow files exist for **{repo}**, but GitHub Actions appears disabled.",
                "",
                "Next best steps:",
                "- Enable GitHub Actions in repository settings.",
                f"- Push a commit to `{default_branch}` or dispatch a workflow manually.",
                "",
                "No rerun is possible until Actions is enabled and a workflow run completes.",
            ]
        )

    lines = [
        f"Workflow discovery for **{repo}** shows files exist, but no run history is available yet.",
        "",
        "Next best steps:",
    ]
    for step in discovery.get("next_steps") or [
        f"Push a commit to `{default_branch}` that matches an existing workflow trigger.",
        "Inspect GitHub Actions for pending or failed first runs.",
    ]:
        lines.append(f"- {step}")
    lines.extend(
        [
            "",
            "No rerun is possible until a workflow run exists.",
        ]
    )
    if should_offer_workflow_proposal(discovery):
        lines.append("")
        lines.append("I can draft a workflow proposal, but I will not commit or push it without approval.")
    return "\n".join(lines)


def compose_workflow_proposal_reply(
    discovery: dict[str, Any],
    *,
    repo_context: dict[str, Any] | None = None,
) -> str:
    repo = str(discovery.get("repository") or "the repository")
    default_branch = str(discovery.get("default_branch") or "main")
    starter = suggest_starter_workflow_type(repo_context=repo_context)
    yaml_body = compose_generic_ci_workflow_yaml(default_branch=default_branch)
    lines = [
        f"Here is a proposal for `{starter['path']}` for **{repo}**.",
        "",
        "No file has been created. No commit or push has been performed.",
        "",
        "```yaml",
        yaml_body.rstrip(),
        "```",
        "",
        "Important:",
        "- proposal only",
        "- no commit",
        "- no push",
        "- no PR",
        "- no file has been created in the repository",
        "",
        "After you add and push this workflow, wait for the first GitHub Actions run before requesting a governed rerun.",
    ]
    return "\n".join(lines)


def compose_generic_ci_workflow_yaml(*, default_branch: str = "main") -> str:
    branch = (default_branch or "main").strip() or "main"
    return f"""name: CI

on:
  push:
    branches: [{branch}]
  pull_request:
    branches: [{branch}]
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Detect project
        run: |
          echo "Add project-specific install/test commands here."

      - name: Placeholder validation
        run: |
          echo "CI workflow scaffold is configured."
"""


def is_workflow_proposal_intent(text: str) -> bool:
    lower = (text or "").lower()
    return any(
        phrase in lower
        for phrase in (
            "draft workflow proposal",
            "draft a workflow proposal",
            "create a ci workflow proposal",
            "create ci proposal",
            "create ci workflow",
            "prepare the workflow file",
            "prepare workflow file",
            "propose github actions workflow",
            "draft ci.yml",
            "generate ci workflow",
        )
    )


def is_workflow_next_steps_intent(text: str) -> bool:
    lower = (text or "").lower()
    return "what should i do next" in lower or "what should we do next" in lower
